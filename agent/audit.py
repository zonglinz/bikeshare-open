"""Batch leakage auditor built on the Claude Agent SDK.

Why this exists: the `/leakage-auditor` subagent inside Claude Code is the
right tool for reviewing *your* diff, once, while you watch. This script is
the right tool for reviewing *forty* repos, unattended, and getting back a
row per repo you can put in a dataframe. Same reviewer, different harness.

    pip install claude-agent-sdk
    python agent/audit.py ../student-repos/*/ --out audit.jsonl

The SDK drives the same Claude Code binary the tutorial uses, so it reads
the same endpoint settings: with Ollama running locally and
.claude/settings.json pointing at it, no API key is needed. The model
comes from AUDIT_MODEL (default: the local `bikeshare-coder` build).
To run against a hosted model instead, set ANTHROPIC_BASE_URL /
ANTHROPIC_AUTH_TOKEN and AUDIT_MODEL in the environment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import shutil
import subprocess
import tempfile
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    create_sdk_mcp_server,
    query,
    tool,
)

# --------------------------------------------------------------------------
# A custom tool. The model is bad at deciding whether three float columns
# sum to a fourth; numpy is perfect at it. Give the deterministic part to
# code and leave the judgement to the model.
# --------------------------------------------------------------------------


@tool(
    "check_identity",
    "Test whether any subset of candidate columns is an exact linear "
    "restatement of the target column. Returns the offending subsets.",
    {"type": "object", "properties": {
        "csv_path": {"type": "string", "description": "CSV or parquet table path."},
        "target": {"type": "string", "description": "One target column name: use cnt for bikeshare, never a feature list."},
        "candidates": {"type": "array", "items": {"type": "string"}, "minItems": 1}
    }, "required": ["csv_path", "target", "candidates"], "additionalProperties": False},
)
async def check_identity(args: dict[str, Any]) -> dict[str, Any]:
    path = Path(args["csv_path"])
    df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    if args["target"] not in df.columns:
        raise ValueError("target must be one existing column name; use target='cnt' for bikeshare, not a feature list")
    if not isinstance(args["candidates"], list) or not args["candidates"]:
        raise ValueError("candidates must be a nonempty list of individual column names")
    unknown = set(args["candidates"]) - set(df.columns)
    if unknown:
        raise ValueError(f"unknown candidate columns: {sorted(unknown)}")
    cols = [c for c in args["candidates"] if c in df.columns and c != args["target"]]

    # Least squares with an intercept column, so `cnt = a*x + b` is caught
    # as well as `cnt = casual + registered`. Rows with any NaN are dropped
    # first; lstsq on NaN returns garbage rather than raising.
    hits = []
    for r in (1, 2, 3):
        for subset in _combinations(cols, r):
            block = df[list(subset) + [args["target"]]].dropna()
            if len(block) < r + 2:
                continue
            X = np.column_stack([block[list(subset)].to_numpy(dtype=float),
                                 np.ones(len(block))])
            y = block[args["target"]].to_numpy(dtype=float)
            coef, *_ = np.linalg.lstsq(X, y, rcond=None)
            resid = float(np.abs(X @ coef - y).max())
            if resid < 1e-6:
                hits.append({"columns": list(subset), "max_residual": resid})
    verdict = "LEAKAGE" if hits else "clean"
    return {
        "content": [
            {"type": "text", "text": json.dumps({"verdict": verdict, "identities": hits})}
        ]
    }


def _combinations(items, r):
    from itertools import combinations

    return combinations(items, r)


@tool("verify_pipeline", "Run make all and make test in a fresh disposable copy; return actual evidence and selected feature names.", {"repo_path": str})
async def verify_pipeline(args):
    def run():
        repo = Path(args["repo_path"]).resolve()
        expected = (repo / "reports/metrics.json").read_bytes()
        with tempfile.TemporaryDirectory(prefix="bikeshare-audit-") as directory:
            copy = Path(directory) / "repo"
            shutil.copytree(repo, copy, ignore=shutil.ignore_patterns(
                ".git", ".venv", "__pycache__", ".pytest_cache", "processed", "reports", "runtime"
            ))
            env = os.environ.copy()
            env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", LOKY_MAX_CPU_COUNT="1")
            commands = {}
            for target in ("all", "test"):
                result = subprocess.run(["make", f"PYTHON={sys.executable}", target],
                                        cwd=copy, env=env, capture_output=True, text=True, timeout=120)
                commands[target] = {"exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
            actual = copy / "reports/metrics.json"
            metrics = json.loads(actual.read_text()) if actual.exists() else {}
            identity = None
            if commands["all"]["exit"] == 0:
                response = asyncio.run(check_identity.handler({
                    "csv_path": str(copy / "data/processed/features.parquet"),
                    "target": "cnt", "candidates": metrics["features"],
                }))
                identity = json.loads(response["content"][0]["text"])
            result = {
                "commands": commands,
                "reproduced_metrics_byte_for_byte": actual.exists() and actual.read_bytes() == expected,
                "selected_features": metrics.get("features", []),
                "metrics": metrics,
                "identity_check": identity,
                "processed_table_for_identity_check": str(repo / "data/processed/features.parquet"),
            }
        evidence_file = repo / "reports/audit-evidence.json"
        evidence_file.write_text(json.dumps(result, indent=2) + "\n")
        summary = {
            "make_all_exit": commands["all"]["exit"],
            "make_test_exit": commands["test"]["exit"],
            "tests": commands["test"]["stdout"].splitlines()[-2:],
            "reproduced_metrics_byte_for_byte": result["reproduced_metrics_byte_for_byte"],
            "selected_features": result["selected_features"],
            "identity_check": identity,
            "model_scores": {name: metrics.get(name) for name in
                             ["baseline_mean", "baseline_persistence", "ridge", "hgb"]},
            "full_evidence_file": str(evidence_file),
        }
        return {"content": [{"type": "text", "text": json.dumps(summary)}]}
    return await asyncio.to_thread(run)


auditor_tools = create_sdk_mcp_server(
    name="audit", version="1.1.0", tools=[check_identity, verify_pipeline]
)

SYSTEM = """\
You review student data-science repos for methodology errors. You did not
write this code and you have no stake in it passing.

Check exactly four things:
  1. Target leakage: any selected feature that contains the SAME-DAY target.
     Past-only target lags are legitimate for one-step rolling prediction.
     Call verify_pipeline first: it runs check_identity deterministically on
     the selected columns with target cnt. Use the separate identity tool
     for additional investigations if needed. Retained raw columns
     casual/registered/cnt in a table are not inputs unless selected.
  2. Temporal validity: splits by date not at random; every rolling or
     lag feature shifts before it aggregates; no transformer is fit on
     validation or test rows.
  3. Baseline: BOTH mean and naive-persistence baselines reported next to
     every model score.
  4. Reproducibility: the pipeline runs from a documented command and
     random seeds are fixed.

Verify by reading files and running code. Do not accept a docstring or a
README claim as evidence.
The pipeline explicitly evaluates conditional on realized same-day weather.
Note the operational day-ahead limitation if relevant; do not pretend actual
weather was available earlier. Report only findings changing a conclusion.

Your final answer is a single JSON object matching the schema you were
given. No prose around it.
Keep the report under 400 words and use at most two material findings.
"""

# Enforced by the SDK: the final turn must validate against this schema and
# arrives parsed in ResultMessage.structured_output. Asking nicely in the
# prompt is not a contract; a schema is.
REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "repo": {"type": "string"},
        "leakage": {"type": "string", "enum": ["none", "suspected", "confirmed"]},
        "temporal_ok": {"type": "boolean"},
        "baseline_reported": {"type": "boolean"},
        "reproducible": {"type": "boolean"},
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "issue": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                },
                "required": ["file", "line", "issue", "why_it_matters"],
            },
        },
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["repo", "leakage", "temporal_ok", "baseline_reported",
                 "reproducible", "findings", "confidence"],
}


async def audit_repo(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    transcript = []
    settings_path = repo / ".claude/settings.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    endpoint_env = {"ANTHROPIC_BASE_URL": "http://localhost:11434",
                    "ANTHROPIC_AUTH_TOKEN": "ollama", "ANTHROPIC_API_KEY": ""}
    endpoint_env.update(settings.get("env", {}))
    for key in ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"):
        if key in os.environ:
            endpoint_env[key] = os.environ[key]
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM,
        cwd=str(repo),
        mcp_servers={"audit": auditor_tools},
        tools=["Read", "Grep", "Glob"],
        allowed_tools=[
            "Read",
            "Grep",
            "Glob",
            "mcp__audit__check_identity",
            "mcp__audit__verify_pipeline",
        ],
        # tools controls exposure; allowed_tools only controls auto-approval.
        # Deterministic MCP code runs the documented commands in a copy.
        disallowed_tools=["Write", "Edit", "Bash", "NotebookEdit", "WebSearch", "WebFetch"],
        setting_sources=["project"],
        strict_mcp_config=True,
        env={**endpoint_env, "CLAUDE_CONFIG_DIR": str(repo / ".claude/runtime"),
             "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
             "CLAUDE_CODE_DISABLE_THINKING": "1",
             "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "1024",
             "MAX_STRUCTURED_OUTPUT_RETRIES": "2"},
        permission_mode="default",
        max_turns=40,
        thinking={"type": "disabled"},
        model=os.environ.get("AUDIT_MODEL", "bikeshare-coder"),
        output_format={"type": "json_schema", "schema": REPORT_SCHEMA},
    )

    # Only the ResultMessage carries the final answer. Concatenating every
    # intermediate TextBlock ("Let me look at config.py first...") and
    # json.loads-ing the lot fails on the first repo that thinks out loud.
    final: ResultMessage | None = None
    try:
        async for message in query(prompt=f"Audit {repo}. Call verify_pipeline with repo_path={str(repo)!r}; its identity_check is already computed by the deterministic tool on target cnt. Read src/features.py and src/train.py, then return the report schema. Keep the final answer short.", options=options):
            transcript.append(asdict(message) if is_dataclass(message) else str(message))
            if isinstance(message, ResultMessage):
                final = message
    finally:
        log = repo / "reports/audit-transcript.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(json.dumps(row, default=str) + "\n" for row in transcript))

    if final is None or final.is_error:
        return {"repo": repo.name, "error": "run_failed",
                "raw": (final.result or "")[:500] if final else ""}
    try:
        # Belt and braces: small open-weight models do not always honour
        # the schema; fall back to parsing the final text.
        report = final.structured_output
        if report is None:
            report = json.loads((final.result or "").strip())
        validate_report(report)
        return {**report, "repo": repo.name, "audit_model": options.model, "audit_engine": "claude-agent-sdk"}
    except (json.JSONDecodeError, ValueError, TypeError) as error:
        # Never let one malformed reply kill a 40-repo run.
        return {"repo": repo.name, "error": "unparseable", "detail": str(error), "raw": (final.result or "")[:500]}


def validate_report(report):
    if not isinstance(report, dict) or any(key not in report for key in REPORT_SCHEMA["required"]):
        raise ValueError("missing required report fields")
    for key in ("temporal_ok", "baseline_reported", "reproducible"):
        if type(report[key]) is not bool:
            raise ValueError(f"{key} must be boolean")
    if report["leakage"] not in {"none", "suspected", "confirmed"}:
        raise ValueError("invalid leakage verdict")
    if report["confidence"] not in {"low", "medium", "high"}:
        raise ValueError("invalid confidence")
    if not isinstance(report["repo"], str) or not isinstance(report["findings"], list):
        raise ValueError("invalid repo or findings")
    for finding in report["findings"]:
        if not isinstance(finding, dict) or type(finding.get("line")) is not int:
            raise ValueError("finding must contain an integer line")
        for key in ("file", "issue", "why_it_matters"):
            if not isinstance(finding.get(key), str):
                raise ValueError(f"finding must contain string {key}")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=Path("audit.jsonl"))
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=600)
    ns = ap.parse_args()
    if ns.concurrency < 1 or ns.timeout <= 0:
        ap.error("concurrency and timeout must be positive")

    sem = asyncio.Semaphore(ns.concurrency)

    async def bounded(repo: Path) -> dict[str, Any]:
        async with sem:
            try:
                return await asyncio.wait_for(audit_repo(repo), timeout=ns.timeout)
            except Exception as error:
                return {"repo": repo.name, "error": type(error).__name__, "detail": str(error)[:500]}

    results = await asyncio.gather(*(bounded(r) for r in ns.repos))
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    with ns.out.open("w") as fh:
        for row in results:
            fh.write(json.dumps(row) + "\n")

    flagged = sum(r.get("leakage") in {"suspected", "confirmed"} for r in results)
    print(f"audited {len(results)} repos; {flagged} flagged -> {ns.out}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
