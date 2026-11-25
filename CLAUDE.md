# Bikeshare demand capstone

Forecast daily Capital Bikeshare `cnt`, 2011–2012, under a one-day rolling
origin: yesterday's observed count is available before predicting today.

## Commands
- `make all`: verify raw hash, build features, reproduce final metrics.
- `make test`: run every guard before claiming completion.
- `python -m src.target_transform`: validation-only target experiment.
- Python 3.13 and the pinned requirements are the verified environment.

## Methodology
- Never feed any column in `src.config.FORBIDDEN` to a model.
  `casual + registered == cnt`; shipped lags and time indexes have
  separate exclusion reasons in that file. Derive inputs from it.
- Never split randomly. Use `temporal_split`: 2011 train, H1 2012 valid,
  H2 2012 test. Select using validation; freeze before inspecting test.
- Report both mean and persistence baselines with every model score.
- Reindex to a complete calendar before lagging; shift before aggregating.
  Test each new feature against strictly earlier named calendar dates.
- `cnt_roll_3` is a rejected experiment: compute and test it, but keep it
  out of the selected matrix. Its validation deltas were both negative.
- Same-day realized weather makes this a conditional evaluation. A live
  day-ahead forecast needs weather forecasts issued before the day.
- Raw data is immutable. `make data` verifies the starter SHA-256.
  Classify any proposed new raw column explicitly in `src/config.py`.
- Record each methodological decision with its measured validation delta
  in `docs/DECISIONS.md`; report null or negative results plainly.

## Repeated workflows
- Keep the starter `/new-feature` skill; write its failing test first.
- Use `/seed-fault <forbidden|rolling|weather|raw-bash>` for isolated fault
  experiments. Paste actual stdout/stderr and restore before completion.
- Request `/leakage-auditor` review for methodology changes; findings must
  identify a concrete change to a number or conclusion.
- Keep pinned dependencies; do not add packages for speculative work.
