"""Run /seed-fault experiments in disposable copies; never change real raw data."""
from __future__ import annotations

import argparse
import csv
import difflib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FAULTS = {
    "forbidden": (
        'return [c for c in numeric if c not in FORBIDDEN]',
        'return list(numeric)  # seeded fault: bypass FORBIDDEN',
    ),
    "rolling": (
        'out[TARGET].shift(1).rolling(LAG_WARMUP).mean()',
        'out[TARGET].rolling(LAG_WARMUP).mean()',
    ),
    "weather": (
        'raise ValueError(f"unmapped weather labels: {sorted(unknown)}")',
        'pass  # seeded fault: silently accept unknown weather',
    ),
}


def experiment(name: str) -> Path:
    transcript = [f"Fault: {name}", "Harness: direct JSON hook invocation; not a Claude Code session."]
    with tempfile.TemporaryDirectory(prefix=f"bikeshare-{name}-") as directory:
        repo = Path(directory) / "repo"
        shutil.copytree(ROOT, repo, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".pytest_cache", "processed", "reports"
        ))
        env = os.environ.copy()
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        env["CLAUDE_PROJECT_DIR"] = str(repo)
        env["PYTHONPATH"] = str(repo)

        def run(label, command, payload=None):
            result = subprocess.run(command, cwd=repo, env=env,
                                    input=payload, capture_output=True, text=True)
            transcript.extend([f"\n$ {label}", f"exit={result.returncode}",
                               "stdout:", result.stdout or "(empty)",
                               "stderr:", result.stderr or "(empty)"])
            return result.returncode

        target = repo / ("data/raw/bike_daily.csv" if name == "raw-bash" else "src/features.py")
        original = target.read_bytes()
        if name == "raw-bash":
            lines = original.decode().splitlines(keepends=True)
            header = next(csv.reader([lines[0]]))
            row = next(csv.reader([lines[1]]))
            col = header.index("cnt")
            row[col] = str(int(row[col]) + 1)
            replacement = io.StringIO()
            csv.writer(replacement, lineterminator="\n").writerow(row)
            changed = lines[0] + replacement.getvalue() + "".join(lines[2:])
            source = Path(directory) / "replacement.csv"
            source.write_text(changed)
            run('Bash: cp "$1" "$2"', ["bash", "-c", 'cp "$1" "$2"',
                                         "seed-fault", str(source), str(target)])
            payload = {"tool_name": "Bash", "tool_input": {"command": "cp replacement.csv data/raw/bike_daily.csv"}}
        else:
            old, new = FAULTS[name]
            text = original.decode()
            assert text.count(old) == 1, f"fault target changed: {old}"
            changed = text.replace(old, new)
            target.write_text(changed)
            payload = {"tool_name": "Edit", "tool_input": {"file_path": str(target)}}

        transcript.extend(["\nExact seeded diff:", "".join(difflib.unified_diff(
            original.decode().splitlines(keepends=True), changed.splitlines(keepends=True),
            fromfile=str(target.relative_to(repo)), tofile=str(target.relative_to(repo))
        ))])
        hook_rc = run("PostToolUse check_leakage.sh < payload.json",
                      ["bash", ".claude/hooks/check_leakage.sh"], json.dumps(payload))
        if name == "raw-bash":
            failed_rc = run("make data", ["make", "data"])
        else:
            failed_rc = run("python -m pytest tests/test_leakage.py -q",
                            [sys.executable, "-m", "pytest", "tests/test_leakage.py", "-q"])
        target.write_bytes(original)
        transcript.append("\nRepair attempts: 1 (restore the exact pre-fault bytes).")
        restored_rc = run("make test (after restoration)", ["make", "test"])

    out = ROOT / "reports" / "faults" / f"{name}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(transcript) + "\n")
    assert hook_rc == (0 if name == "raw-bash" else 2), f"unexpected hook result; see {out}"
    assert failed_rc != 0, f"seeded fault was not detected; see {out}"
    assert restored_rc == 0, f"restored tests failed; see {out}"
    print(f"OK {name}: hook={hook_rc}, red={failed_rc}, restored={restored_rc} -> {out.relative_to(ROOT)}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fault", choices=[*FAULTS, "raw-bash"])
    experiment(parser.parse_args().fault)
