---
name: seed-fault
description: Exercise a bikeshare guard with a deliberate fault, capture real test and hook output, and verify the restored pipeline. Use for the assignment's repeated fault experiments.
allowed-tools: Read, Edit, Bash(python tools/seed_fault.py*), Bash(.venv/bin/python tools/seed_fault.py*), Bash(make test*), Bash(git add*), Bash(git commit*)
---

# Seed a fault: $ARGUMENTS

Use one of `forbidden`, `rolling`, `weather`, or `raw-bash` as the argument.
Run `.venv/bin/python tools/seed_fault.py $ARGUMENTS` from the repository
root when that environment exists; otherwise use the active `python`.
The helper mutates an isolated temporary copy, invokes the real hook using
a JSON tool payload, records the diff and unedited output under
`reports/faults/`, restores the copy, and verifies the restored tests.

Read the saved output before reporting success. For a source fault, the
hook must exit 2 and pytest must fail; after restoration pytest must pass.
For `raw-bash`, the PostToolUse hook must miss the Bash copy, while
`make data` must reject the changed SHA-256. Never experiment on the
submission's immutable raw CSV.

Append the actual transcript to `docs/SEEDED_FAULTS.md`, distinguish a
direct hook-payload test from an observed Claude Code session, and report
the number of repair attempts actually made. Commit one fault at a time,
with the restoration described in the commit message. An unexpected
result is evidence to investigate, not text to rewrite as a success.
