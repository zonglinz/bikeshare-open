# Decisions

One line per methodological decision: what you chose, why, and what it changed.
Agents append here via the `/new-feature` skill; you append here by hand.

- Exclude `casual`, `registered`: they sum to `cnt` exactly. Leaky model R^2 1.000 -> honest ridge 0.583.
- Exclude `cnt_2d_bfr`: a shipped 2-day lag we cannot test the alignment of. Build our own lags instead.
- Exclude `instant`, `yr`, `days_since_2011`: time indexes let a tree predict a flat constant past 2011 and a linear model extrapolate a trend we have no grounds for.
- Split 2011 / H1 2012 / H2 2012 by date. Test set touched once, after all feature work.
- Report mean and persistence baselines with every score. Persistence (test R^2 0.510, MAE 840) is within 0.07 R^2 of ridge and beats it on MAE; that caveat goes in the report.

- 2026-11-25: Follow Part 5: preserve the finished starter as commit 1 and extend it rather than rebuilding tutorial code. New choices below are agent-proposed and require the student's review; they are not invented accounts of student decisions.
- 2026-11-25: Checked the local CSV directly: 728 rows, 2011-01-03 to 2012-12-31, missing 2011-03-10, weather GOOD/MISTY/BAD = 463/245/20. Least-squares identity maximum residual = 5.4569682106375694e-12; evidence in reports/data_profile.json. No separate local-model exploration answer was claimed.
- 2026-11-25: Added cnt_roll_3 = mean(cnt[d-3], cnt[d-2], cnt[d-1]), after calendar reindexing and shift(1). Every input is known after day d-1 closes. Validation-only comparison: ridge 0.6475 -> 0.6439 (delta -0.0036), hgb 0.2185 -> 0.1983 (delta -0.0202). Reject it as a final predictor; retain its implementation/test and before/after evidence for reproducibility. LAG_WARMUP remains 7.
