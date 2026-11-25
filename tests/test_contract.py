"""Guard rails on the ingest contract and the trained model's behaviour."""
import pandas as pd
import pytest
from sklearn.metrics import r2_score

from src.config import FORBIDDEN, LAG_WARMUP, RAW_FEATURE_INPUTS, TARGET
from src.features import build_features, feature_columns, reindex_to_calendar
from src.ingest import load_raw, validate_raw_columns, verify_raw_hash
from src.train import MODELS, temporal_split


@pytest.fixture(scope="module")
def raw():
    return load_raw().sort_values("dteday").reset_index(drop=True)


@pytest.fixture(scope="module")
def feats(raw):
    return build_features(raw)


def test_calendar_is_complete_before_lagging(raw):
    """The reindexed frame must have no gaps, or the lags are wrong."""
    grid = reindex_to_calendar(raw)
    assert set(grid.dteday.diff().dropna().dt.days.unique()) == {1}


def test_only_expected_rows_are_dropped(raw, feats):
    """Rows may only vanish for the lag warm-up or downstream of a genuinely
    absent day -- never because an encoder produced a silent NaN.

    Accounting: the first LAG_WARMUP days have no complete history. Each
    absent calendar day m costs the LAG_WARMUP rows after it (cnt_lag_1 is
    NaN on m+1, cnt_roll_7 is NaN on m+1..m+7, cnt_lag_7 on m+7; their
    union is 7 rows). Day m itself was never in `raw`, so it is not a loss.
    The bound is exact for the current feature set; add a longer lag and
    LAG_WARMUP in src/config.py must grow with it.
    """
    full = pd.date_range(raw.dteday.min(), raw.dteday.max(), freq="D")
    missing_days = len(full) - len(raw)
    allowed_loss = LAG_WARMUP + LAG_WARMUP * missing_days
    lost = len(raw) - len(feats)
    assert lost <= allowed_loss, f"lost {lost} rows; expected at most {allowed_loss}"


def test_exact_retained_dates_have_complete_calendar_history(raw, feats):
    """A row shift across the missing day must not pass the row-loss upper bound."""
    observed = set(raw.dteday)
    expected = {
        day for day in observed
        if all(day - pd.Timedelta(days=k) in observed
               for k in range(1, LAG_WARMUP + 1))
    }
    assert set(feats.dteday) == expected


def test_beats_the_mean_baseline(feats):
    """A model that cannot beat predicting the training mean is not a result."""
    cols = feature_columns(feats)
    train, valid, _ = temporal_split(feats)
    ridge = MODELS["ridge"]
    ridge.fit(train[cols], train[TARGET])
    # Routine verification must not turn held-out test data into a tuning set.
    assert r2_score(valid[TARGET], ridge.predict(valid[cols])) > 0.4


def test_persistence_baseline_is_reported():
    """The baseline that matters for a lag-driven model is 'yesterday again'.
    It must be in the comparison, whatever its score."""
    assert "baseline_persistence" in MODELS


def test_every_raw_column_is_classified(raw):
    known = FORBIDDEN | RAW_FEATURE_INPUTS | {"dteday"}
    assert not (set(raw.columns) - known), "unclassified raw columns"
    # A renamed copy of the target must be rejected even with an innocent name.
    unexpected = raw.assign(innocent_measurement=raw[TARGET])
    with pytest.raises(ValueError, match="unclassified raw columns.*innocent_measurement"):
        validate_raw_columns(unexpected)


def test_raw_hash_detects_a_modified_copy(tmp_path):
    from src.config import RAW
    changed = tmp_path / "bike_daily.csv"
    changed.write_bytes(RAW.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="raw SHA-256 mismatch"):
        verify_raw_hash(changed)
