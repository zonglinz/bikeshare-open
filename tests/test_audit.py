"""Offline tests for deterministic tools and batch failure containment."""
import asyncio
from dataclasses import dataclass
import json
import sys

import pandas as pd
import pytest

from agent import audit


def valid_report():
    return {"repo": "fixture", "leakage": "none", "temporal_ok": True,
            "baseline_reported": True, "reproducible": True,
            "findings": [], "confidence": "high"}


@dataclass
class FakeResult:
    structured_output: object = None
    result: str = ""
    is_error: bool = False


@pytest.mark.parametrize("suffix", [".csv", ".parquet"])
def test_identity_tool_detects_arithmetic_in_both_table_formats(tmp_path, suffix):
    frame = pd.DataFrame({"a": [1, 2, 4, 8, 16, 32],
                          "b": [3, 9, 2, 7, 5, 11]})
    frame["cnt"] = frame.a + frame.b
    path = tmp_path / ("table" + suffix)
    if suffix == ".csv":
        frame.to_csv(path, index=False)
    else:
        frame.to_parquet(path, index=False)
    response = asyncio.run(audit.check_identity.handler(
        {"csv_path": str(path), "target": "cnt", "candidates": ["a", "b"]}
    ))
    result = json.loads(response["content"][0]["text"])
    assert result["verdict"] == "LEAKAGE"
    assert any(hit["columns"] == ["a", "b"] for hit in result["identities"])


def test_auditor_uses_final_structured_message(tmp_path, monkeypatch):
    async def query(**kwargs):
        yield "intermediate prose that is not JSON"
        yield FakeResult(structured_output=valid_report())
    monkeypatch.setattr(audit, "query", query)
    monkeypatch.setattr(audit, "ResultMessage", FakeResult)
    result = asyncio.run(audit.audit_repo(tmp_path))
    assert result["leakage"] == "none"
    assert result["audit_engine"] == "claude-agent-sdk"


@pytest.mark.parametrize("target,candidates", [("a,b", ["a", "b"]), ("cnt", ["missing"])])
def test_identity_tool_rejects_invalid_arguments_instead_of_claiming_clean(tmp_path, target, candidates):
    path = tmp_path / "table.csv"
    pd.DataFrame({"a": [1, 2], "b": [3, 4], "cnt": [4, 6]}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        asyncio.run(audit.check_identity.handler(
            {"csv_path": str(path), "target": target, "candidates": candidates}
        ))


def test_auditor_reports_malformed_reply_instead_of_crashing(tmp_path, monkeypatch):
    async def query(**kwargs):
        yield FakeResult(result="This is not JSON")
    monkeypatch.setattr(audit, "query", query)
    monkeypatch.setattr(audit, "ResultMessage", FakeResult)
    result = asyncio.run(audit.audit_repo(tmp_path))
    assert result["error"] == "unparseable"


def test_fallback_json_must_obey_schema_types(tmp_path, monkeypatch):
    report = valid_report()
    report["temporal_ok"] = "true"
    async def query(**kwargs):
        yield FakeResult(result=json.dumps(report))
    monkeypatch.setattr(audit, "query", query)
    monkeypatch.setattr(audit, "ResultMessage", FakeResult)
    result = asyncio.run(audit.audit_repo(tmp_path))
    assert result["error"] == "unparseable"
    assert "boolean" in result["detail"]


def test_one_repo_exception_does_not_lose_other_batch_rows(tmp_path, monkeypatch):
    async def review(repo):
        if repo.name == "bad":
            raise RuntimeError("seeded transport failure")
        return valid_report()
    out = tmp_path / "batch.jsonl"
    monkeypatch.setattr(audit, "audit_repo", review)
    monkeypatch.setattr(sys, "argv", ["audit.py", "bad", "good", "--out", str(out)])
    asyncio.run(audit.main())
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["error"] == "RuntimeError"
    assert rows[1]["leakage"] == "none"
