## Results

Daily demand was evaluated using the immutable starter mirror, not a replacement UCI file. It contains 728 observations from 2011-01-03 through 2012-12-31, with 2011-03-10 absent. GOOD, MISTY and BAD weather occur on 463, 245 and 20 days. Reindexing to daily calendar dates before shifting makes the missing day explicit. Seven warm-up days and seven dates depending on the missing day are excluded, leaving 714 modeling rows: 348 training days in 2011, 182 validation days in H1 2012 and 184 test days in H2 2012. Lagged counts assume a rolling one-day prediction setting, so yesterday's observed demand is available on each subsequent day.

The new candidate, `cnt_roll_3`, is the mean of the three preceding calendar days. Its test was committed before its implementation and failed with `KeyError: 'cnt_roll_3'`. On 2012-06-15 the hand-computed expectation is (4,972 + 7,421 + 7,363) / 3 = 6,585.3333. The implementation shifts before rolling and requires no increase to the seven-day warm-up. The candidate reduced validation R² by 0.0036 for ridge and 0.0202 for hgb, so it was rejected before the final evaluation. The implementation remains testable, while the selected model matrix excludes it.

The eight rows below are generated directly from `reports/metrics.json` (`before_feature` and `after_feature`). The top-level four model entries select **Before**. “After candidate” is the required recorded experiment, not the selected pipeline. MAE is measured in rides per day.

| Variant | Model | Validation R² | Validation MAE | Test R² | Test MAE |
| --- | --- | ---: | ---: | ---: | ---: |
| Before | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| Before | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| Before | ridge | 0.6475 | 832.9 | 0.5833 | 947.1 |
| Before | hgb | 0.2185 | 1296.6 | -0.4975 | 1972.6 |
| After candidate | baseline_mean | -0.9318 | 2002.2 | -2.1441 | 2847.7 |
| After candidate | baseline_persistence | 0.4507 | 900.6 | 0.5099 | 840.1 |
| After candidate | ridge | 0.6439 | 836.5 | 0.5800 | 946.2 |
| After candidate | hgb | 0.1983 | 1311.6 | -0.5338 | 1998.7 |

Python 3.13, the starter's pinned libraries and a single numerical thread reproduce these values with `make all`; `make test` verifies the contracts. The original NumPy pin requires Python 3.12+, so the assignment's Python 3.11 setup was corrected in the README. The raw CSV SHA-256 remains `a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc`. Choices and the validation experiment were committed before the first held-out evaluation. Later runs regenerate fixed results solely for reproducibility checks, without changing the selected feature set or hyperparameters.

## Headline finding

The deliberately leaky demonstration obtains R² = 1.000000, but least squares reconstructs the target from casual and registered riders with maximum absolute residual 5.46 × 10⁻¹²: it learns an arithmetic identity rather than a forecast. Under the temporal split, the training-mean baseline falls to test R² = −2.1441, persistence achieves 0.5099, ridge reaches 0.5833 and raw gradient boosting falls to −0.4975. Thus boosting still beats the training-mean baseline, while ridge's improvement over persistence is only 0.0734 R² and comes with worse MAE. Training counts range from 431 to 6,043; test counts range from 22 to 8,714, and 56.52% exceed the training maximum. This fitted booster predicts only 1,055.0–5,537.0 on test: its piecewise constant response does not extrapolate the demand growth. Only 348 training rows and the fixed default configuration also constrain validation performance; the growth explanation is not proof of every error's cause. The new three-day feature worsened validation performance and was excluded from the selected pipeline.

All results condition on **realized same-day weather** in the starter predictors, including temperature, apparent temperature, humidity and wind speed. That is a material availability assumption: these measurements are not known in full before the day. An operational day-ahead claim requires archived weather forecasts issued before each prediction and a new evaluation with those inputs. These scores support the stated conditional comparison, not an already validated deployment.

## Exercise 4: target transformation

I preselected one transformation using training and validation only: predict `delta_cnt = cnt - cnt_lag_1` with the same hgb configuration and reconstruct demand as `cnt_lag_1 + predicted_delta`. The feature decision was already fixed, so this experiment uses the selected 14 inputs. Validation R² improves from 0.2185 to 0.6079 and MAE falls from 1,296.6 to 834.3. For comparison, ridge gives R² 0.6475 and MAE 832.9, persistence 0.4507 and 900.6, and the mean baseline −0.9318 and 2,002.2. The tree now competes much more closely with ridge without a hyperparameter search.

This transformation is defensible for rolling one-day prediction: yesterday's count is known, and a bounded predicted change can be added to a larger current demand level. It adds a persistence anchor instead of pretending the tree has learned a long-term extrapolation law. It would be invalid to use actual intermediate counts when forecasting the entire six-month test period at once. The same conditional-weather limitation remains. After the transformation and feature choices were committed, its final test R² was 0.5440 and MAE 921.7, versus raw hgb −0.4975/1,972.6, ridge 0.5833/947.1, persistence 0.5099/840.1 and mean −2.1441/2,847.7. It improves the tree comparison but still does not beat persistence on MAE. `reports/target_transform_validation.json` preserves the pre-final run with `test_evaluated: false`; the separate final file records held-out evaluation. The required `metrics.json` remains the untransformed pipeline.

## Exercise 5: ridge vs persistence

For a decision whose cost scales with absolute ride-count error, I would prefer persistence as the initial operational benchmark. Ridge raises test R² from 0.5099 to 0.5833, but raises MAE from 840.1 to 947.1: 107.0 more rides of error per day, or 12.7%. A squared-error improvement can matter when large misses are especially costly, but no such cost function was supplied. Standardized ridge coefficients are about +566.9 rides per standard deviation for the seven-day mean and +361.6 for yesterday's count, compared with −279.9 for weather severity and +200.0 for temperature. Ridge therefore learns beyond simply repeating yesterday, but remains strongly anchored in past demand. Correlated lag and weather inputs prevent a causal interpretation of these coefficients. The modest R² improvement does not justify extra maintenance for an absolute-error objective, and neither model is deployment-ready until weather availability is evaluated honestly.

## Attribution

Codex (GPT-6 family; parameter count and context configuration are not exposed in this session) authored the changes. A separate local SDK reviewer used qwen3.5:0.8b-q8_0 (752.39M text parameters, Q8_0, 64k context, temperature 0, CPU). I did not switch the authoring model; the local reviewer was a separate process. The same local model also performed the isolated fault-edit/repair verification described in `docs/SEEDED_FAULTS.md`; it did not author the submitted numerical pipeline. Its real schema-valid output confirmed leakage with high confidence and marked reproducibility false. I reject those two claims: the 14 selected inputs have no intersection with `FORBIDDEN`, the deterministic one-to-three-column identity check is clean, and the fresh-copy pipeline exits 0, passes all 28 tests, and reproduces identical metric bytes. The audit's quoted R² ≈ 0.93 is unsupported. I accept its temporal and baseline checks. The untouched verdict, tool transcript and numerical rebuttal are saved in `reports/audit.jsonl`, `reports/audit-transcript.jsonl` and `reports/audit-adjudication.json`. This is a concrete example of a schema-valid, confident model answer that still requires verification. The small reviewer is not being presented as equivalent to the tutorial's recommended 9B authoring setup.

Agent-generated work:

- The candidate implementation and its prior-date test; raw-column, arithmetic-identity and raw-hash guards; the auditor's offline failure tests.
- The before/after scoring output, additive-target experiment, diagnostics, fault helper and real transcripts, custom `seed-fault` skill, documentation and Git commits.
- The report draft and decisions log. The first commit preserves all unmodified starter files; it does not claim the starter was written during this session.

Research choices supplied by the assignment or proposed by the agent, recorded in `docs/DECISIONS.md` for student review:

- Predict total daily rides; exclude target components, unverified supplied lags and raw time indexes for their distinct reasons.
- Use the prescribed date split and both baselines; keep test predictions out of feature and transformation selection.
- Reject the three-day average based on its negative validation changes; interpret the additive-target experiment within rolling one-step prediction.
- Limit the claim to conditional weather inputs, and prefer the persistence benchmark for an absolute-error objective.

These are not fabricated claims that the student independently made the choices or performed the commands. The student must review and adopt the analysis before submission. Exercise 3 audited AhmadAgeel/bikeshare-open at commit a2192434d64add5b5cb2c7b4008e4ae58c66a3b5 using the configured leakage-auditor in a fresh local process. `docs/AUDIT.md` preserves its actual output and the separate assessment, including corrections to its weather-encoding and row-loss statements and the realized-weather limitation. The peer's 17 tests pass and its committed metrics reproduce exactly. Three later native Claude Code Edit/PostToolUse runs measured 1, 2 and 1 assistant repair turns for the forbidden-column, rolling-window and weather faults respectively (5, 5 and 4 whole-workflow CLI turns). Each recorded hook exited 2 after seeding and 0 after exact restoration; `reports/faults/agent-hook-verification.jsonl` preserves the real events and hashes. The model's final prose misdescribes those outcomes, so the assessment uses the recorded hook results and restored bytes. These were prompted seed-and-restore checks, not unprompted fault discovery. Optional Exercise 6 was not performed.
