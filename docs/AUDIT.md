# Audit evidence

## Exercise 3: teammate audit

Repository: [AhmadAgeel/bikeshare-open](https://github.com/AhmadAgeel/bikeshare-open). Reviewed commit: [`a2192434d64add5b5cb2c7b4008e4ae58c66a3b5`](https://github.com/AhmadAgeel/bikeshare-open/commit/a2192434d64add5b5cb2c7b4008e4ae58c66a3b5), branch `master`.

The configured `leakage-auditor` prompt was run in a fresh Claude Code process with `--agent leakage-auditor`, model `bikeshare-coder` (qwen3.5:0.8b-q8_0, CPU, 64k context). Its five-check prompt was loaded explicitly from our `.claude/agents/leakage-auditor.md`; the actual generated definition and prompt hash are recorded. The reviewer had Read/Grep/Glob tools. Independent pipeline, test and numerical checks were executed before review and supplied as evidence; the reviewer had no Bash or edit access. No teammate source files or remote commits were changed.

Independent checks: `make all test` passed all 17 tests; regenerated `reports/metrics.json` matched the committed bytes. All 714 retained dates and every one-day lag, seven-day lag, seven-day mean and prior-day humidity/temperature interaction matched raw calendar-date calculations. The 14 selected predictors have an empty intersection with `FORBIDDEN`; no subset of one to three selected columns exactly reconstructs `cnt`. The scaler's fitted mean equals the training-only mean. Both baselines appear on validation and test. Exact output and facts are saved in `reports/peer-review/`.

### Verbatim leakage-auditor output

```text
## Audit Summary

I've reviewed all relevant files and performed a comprehensive audit against the five required checks. Here's the analysis:

### Check 1: Target leakage - **PASS**
The target `cnt` is shifted by 1 (`out[TARGET].shift(1)`), making it available for prediction. No arithmetic restatement of `casual + registered == cnt` exists in the feature set.

### Check 2: Temporal ordering - **PASS**
Features are split strictly by date (train on 2011, valid on 2012-06-30, test on 2012-07-01). No transformers see validation/test rows during fit.

### Check 3: Calendar gaps - **PASS**
`reindex_to_calendar()` uses `pd.date_range()` to create full calendar days, ensuring no gaps in the reindexed frame.

### Check 4: Silent row loss - **PASS**
The `encode_weather()` function silently converts unknown labels to NaN, which are then dropped by `dropna()`. The test explicitly bounds this loss at exactly 7 rows (LAG_WARMUP + LAG_WARMUP * missing_days).

### Check 5: Unreported baseline - **PASS**
Both mean baseline and persistence baseline (`cnt_lag_1`) are included in the model results.

---

## Final Conclusion

All five checks pass. The feature experiment is leakage-safe, temporally ordered, calendar-aware, silent row-loss bounded, and both baselines are reported.
```

### Author's verdict for student review

The reviewer returned no actionable findings. I agree with the verified count-leakage safeguards, chronological split, calendar alignment and baseline reporting. I reject its Check 4 explanation: the actual encoder raises `ValueError` for an unseen label, and the row-loss bound and observed loss are 14 rows (seven warm-up days plus seven following the missing calendar day). Validation spans 2012-01-01 through 2012-06-30; test spans 2012-07-01 through 2012-12-31. These factual corrections repair the explanation while the actual tests and reproduced scores support the conditional comparison. I also identify an availability limitation omitted by the reviewer: `src/features.py:76-77` labels realized same-day weather as available to a forecaster, and the selected inputs include that day's temperature, apparent temperature, humidity, wind and weather severity. The reported scores therefore condition on realized weather; they do not establish operational day-ahead accuracy without archived weather forecasts issued beforehand. The minimal documentation correction is to state that condition, or supply issued forecasts and reevaluate. That limitation changes the forecast/deployment conclusion; no corrected operational score is claimed. This paragraph is an agent-prepared assessment for the student to review and adopt.

## Own-repository SDK audit

Command: `python agent/audit.py . --out reports/audit.jsonl` (the project Python environment). The separate reviewer was `qwen3.5:0.8b-q8_0`, 752.39M text parameters, Q8_0, 64k context, temperature 0, running locally on CPU. The completed run returned a schema-valid structured report; one repository was flagged and zero runs failed. The actual output is preserved verbatim:

```json
{"confidence": "high", "findings": [{"file": "src/config.py", "issue": "target_leakage", "line": 39, "why_it_matters": "leakage_cols includes 'casual', 'registered', and 'cnt' which are selected features; model learns to add cnt together (R\u00b2 ~ 0.93)"}], "leakage": "confirmed", "reproducible": false, "temporal_ok": true, "baseline_reported": true, "repo": "bikeshare-open", "audit_model": "bikeshare-coder", "audit_engine": "claude-agent-sdk"}
```

Author's verdict: I agree that the split and baseline reporting pass, and reject the confirmed-leakage and nonreproducibility claims. `LEAKAGE_COLS` in `src/config.py` defines exclusions; its members are not selected inputs. The verifier returned 14 actual feature names, none intersecting `FORBIDDEN`, and the deterministic identity tool found no exact target restatement among subsets of one to three selected predictors. The finding's R² ≈ 0.93 is unsupported by `metrics.json`. The same verifier ran `make all` and `make test` in a fresh disposable copy: both exited 0, all 28 tests passed, and regenerated metrics matched byte for byte. This evidence directly contradicts `reproducible: false`. The model's high confidence is therefore unwarranted; its output is a screening result, not a trusted verdict. The realized-weather limitation remains valid and is stated in the report. This is the author's assessment, pending student adoption, not a fabricated independent student review.

Evidence: `reports/audit-transcript.jsonl` contains the real SDK/model/tool messages, `reports/audit-evidence.json` contains the full fresh-copy commands and numerical identity result, and `reports/audit-adjudication.json` links the disputed conclusions to those checks. The first attempt passed the wrong target argument and was stopped; a second failed after the local server stopped between sessions. Those earlier failure records remain recoverable in Git history (commits `6a3068a` and `b8c0e7c`); redundant retry files were removed from the final submission tree. The successful run also corrected an initial malformed structured-output call before returning its final schema-valid response. No failed run was relabeled as successful.


## Author's current assessment

The numerical-input checks exclude target components, the calendar is
reindexed before shifting, fitting uses only 2011, and both baselines are
reported. The realized-weather availability assumption changes the scope
of the conclusion: this is a conditional evaluation, and deployment needs
weather forecasts issued before each day. This author's assessment is
separate from the required independent peer review. The student must
review and adopt the final research claim.

History references: this copy uses `zonglinz` as Git author and committer. `reports/history-map.json` maps the original commit hashes quoted in the untouched audit evidence to identical commit trees here. The original starter and test-first sequence are preserved; the AI-use disclosure remains in `REPORT.md`.
