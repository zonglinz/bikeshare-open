"""The tests that make the agent honest.

test_no_forbidden_features is the single most valuable test in this repo:
casual + registered == cnt exactly, so any model handed those columns
scores R^2 = 1.0 and looks brilliant while having learned nothing.
"""
from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from src.config import FORBIDDEN, TARGET
from src.features import build_features, encode_weather, feature_columns
from src.ingest import load_raw


@pytest.fixture(scope="module")
def feats():
    return build_features(load_raw())


def test_leakage_identity_holds(feats):
    """Documents *why* casual and registered are forbidden."""
    assert (feats.casual + feats.registered == feats[TARGET]).all()


def test_no_forbidden_features(feats):
    """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
    construction, so this cannot discover a *new* leaky column. What it
    catches is someone editing feature_columns() or FORBIDDEN -- which is
    exactly the fault the Step 7 hook demonstrates."""
    cols = set(feature_columns(feats))
    assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"


def test_lags_are_true_calendar_lags(feats):
    """cnt_lag_1 for date d must equal cnt on d-1, in calendar days."""
    by_date = feats.set_index("dteday")[TARGET]
    checked = 0
    for date, lag in feats.set_index("dteday").cnt_lag_1.items():
        prev = date - pd.Timedelta(days=1)
        if prev in by_date.index:
            assert lag == pytest.approx(by_date[prev]), f"bad lag at {date.date()}"
            checked += 1
    assert checked > 600, "too few rows actually verified"


def test_lag_is_not_the_target(feats):
    assert not (feats.cnt_lag_1 == feats[TARGET]).all()


def test_rolling_mean_excludes_today(feats):
    """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
    by_date = feats.set_index("dteday")[TARGET]
    date = feats.dteday.iloc[200]
    window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
    if all(d in by_date.index for d in window):
        expected = sum(by_date[d] for d in window) / 7
        assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)


def test_no_missing_values(feats):
    assert feats[feature_columns(feats)].isna().sum().sum() == 0


def test_dates_are_sorted_and_unique(feats):
    assert feats.dteday.is_monotonic_increasing
    assert feats.dteday.is_unique


def test_three_day_mean_uses_only_prior_calendar_dates(feats):
    """June 15 uses June 12-14: 4,972, 7,421, and 7,363 rides."""
    date = pd.Timestamp("2012-06-15")
    expected = (4972 + 7421 + 7363) / 3
    actual = feats.set_index("dteday").loc[date, "cnt_roll_3"]
    assert actual == pytest.approx(expected)


def test_weather_rejects_unknown_labels():
    with pytest.raises(ValueError, match="unmapped weather labels.*STORM"):
        encode_weather(pd.Series(["GOOD", "STORM"]))


def test_no_single_feature_or_pair_exactly_restates_target(feats):
    """Inspect values, so renaming a leaked predictor does not defeat the check."""
    cols = feature_columns(feats)
    y = feats[TARGET].to_numpy(dtype=float)
    for size in (1, 2):
        for subset in combinations(cols, size):
            X = np.column_stack([feats[list(subset)].to_numpy(dtype=float), np.ones(len(y))])
            coef, *_ = np.linalg.lstsq(X, y, rcond=None)
            residual = float(np.max(np.abs(X @ coef - y)))
            assert residual > 1e-6, f"target identity in {subset}: max residual={residual}"
