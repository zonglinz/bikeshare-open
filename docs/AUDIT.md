# Audit evidence

## Exercise 3: teammate audit — pending

No teammate repository URL or local path has been supplied. No teammate
repository has been audited, and no `/leakage-auditor` peer output is
claimed. The assignment requires this evidence; an audit of this project
cannot stand in for it. This is the outstanding required exercise.

Once the repository is available, run the configured `leakage-auditor`
reviewer against that repository in a fresh context, paste its actual
output here verbatim, and add the student's paragraph identifying which
findings change a number or invalidate a conclusion. Record the teammate's
URL and reviewed commit. If no findings are returned, preserve the run and
say so explicitly.

## Own-repository SDK audit

Command: `python agent/audit.py . --out reports/audit.jsonl` (the project Python environment). The separate reviewer was `qwen3.5:0.8b-q8_0`, 752.39M text parameters, Q8_0, 64k context, temperature 0, running locally on CPU. The completed run returned a schema-valid structured report; one repository was flagged and zero runs failed. The actual output is preserved verbatim:

```json
{"confidence": "high", "findings": [{"file": "src/config.py", "issue": "target_leakage", "line": 39, "why_it_matters": "leakage_cols includes 'casual', 'registered', and 'cnt' which are selected features; model learns to add cnt together (R\u00b2 ~ 0.93)"}], "leakage": "confirmed", "reproducible": false, "temporal_ok": true, "baseline_reported": true, "repo": "bikeshare-open", "audit_model": "bikeshare-coder", "audit_engine": "claude-agent-sdk"}
```

Author's verdict: I agree that the split and baseline reporting pass, and reject the confirmed-leakage and nonreproducibility claims. `LEAKAGE_COLS` in `src/config.py` defines exclusions; its members are not selected inputs. The verifier returned 14 actual feature names, none intersecting `FORBIDDEN`, and the deterministic identity tool found no exact target restatement among subsets of one to three selected predictors. The finding's R² ≈ 0.93 is unsupported by `metrics.json`. The same verifier ran `make all` and `make test` in a fresh disposable copy: both exited 0, all 28 tests passed, and regenerated metrics matched byte for byte. This evidence directly contradicts `reproducible: false`. The model's high confidence is therefore unwarranted; its output is a screening result, not a trusted verdict. The realized-weather limitation remains valid and is stated in the report. This is the author's assessment, pending student adoption, not a fabricated independent student review.

Evidence: `reports/audit-transcript.jsonl` contains the real SDK/model/tool messages, `reports/audit-evidence.json` contains the full fresh-copy commands and numerical identity result, and `reports/audit-adjudication.json` links the disputed conclusions to those checks. The first attempt passed the wrong target argument and was stopped; a second failed after the local server stopped between sessions. Those actual transcripts and errors are retained as `reports/audit-attempt-*`. The successful run also corrected an initial malformed structured-output call before returning its final schema-valid response. No failed run was relabeled as successful.


## Author's current assessment

The numerical-input checks exclude target components, the calendar is
reindexed before shifting, fitting uses only 2011, and both baselines are
reported. The realized-weather availability assumption changes the scope
of the conclusion: this is a conditional evaluation, and deployment needs
weather forecasts issued before each day. This author's assessment is
separate from the required independent peer review. The student must
review and adopt the final research claim.
