"""Stage 3: temporal split, fit, evaluate, write metrics.

Two baselines and two models, on purpose.

  baseline_mean         predict the 2011 average for every day
  baseline_persistence  predict yesterday's count (cnt_lag_1)
  ridge                 standardised linear model on the audited features
  hgb                   gradient-boosted trees on the same features

The mean baseline shows what "the distribution moved" costs. Persistence
is the baseline that actually matters: ridge's features are dominated by
lagged demand, so if it cannot beat "yesterday again" it has learned
nothing worth reporting. The booster is there because it fails, and the
reason it fails is the headline result.

Run: python -m src.train
"""
import json

import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import METRICS, PROCESSED, ROOT, TARGET, TRAIN_END, VALID_END
from src.features import feature_columns


class PersistenceBaseline(BaseEstimator, RegressorMixin):
    """Predict a single lagged column unchanged. Nothing is fit."""

    def __init__(self, column: str = "cnt_lag_1"):
        self.column = column

    def fit(self, X, y=None):
        if self.column not in X.columns:
            raise ValueError(f"persistence baseline needs column {self.column!r}")
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


MODELS = {
    "baseline_mean": DummyRegressor(strategy="mean"),
    "baseline_persistence": PersistenceBaseline("cnt_lag_1"),
    "ridge": make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
    "hgb": HistGradientBoostingRegressor(random_state=0, max_iter=300),
}


def temporal_split(df: pd.DataFrame):
    """Split by date, never at random. A random split on a time series
    puts tomorrow in train and today in test."""
    train = df[df.dteday <= TRAIN_END]
    valid = df[(df.dteday > TRAIN_END) & (df.dteday <= VALID_END)]
    test = df[df.dteday > VALID_END]
    return train, valid, test


def score_variant(df: pd.DataFrame, cols: list[str]) -> dict:
    train, valid, test = temporal_split(df)

    results = {
        "n_features": len(cols),
        "features": cols,
        "n_train": len(train),
        "n_valid": len(valid),
        "n_test": len(test),
    }
    for name, estimator in MODELS.items():
        model = clone(estimator)
        model.fit(train[cols], train[TARGET])
        results[name] = {
            split: {
                "r2": round(float(r2_score(part[TARGET], model.predict(part[cols]))), 4),
                "mae": round(float(mean_absolute_error(part[TARGET], model.predict(part[cols]))), 1),
            }
            for split, part in [("valid", valid), ("test", test)]
        }
    return results


def fit_and_score() -> dict:
    df = pd.read_parquet(PROCESSED)
    before_cols = [c for c in feature_columns(df, include_rejected=True) if c != "cnt_roll_3"]
    after_cols = feature_columns(df, include_rejected=True)
    before = score_variant(df, before_cols)
    after = score_variant(df, after_cols)
    return {
        **before,
        "selected_variant": "before_feature",
        "feature_decision": "Reject cnt_roll_3 based only on validation; keep its tested implementation for inspection.",
        "before_feature": before,
        "after_feature": after,
    }


def write_final_diagnostics(df: pd.DataFrame) -> None:
    """Evidence inspected only after the feature and transformation were frozen."""
    from src.target_transform import evaluate

    cols = feature_columns(df)
    train, valid, test = temporal_split(df)
    ridge = clone(MODELS["ridge"]).fit(train[cols], train[TARGET])
    booster = clone(MODELS["hgb"]).fit(train[cols], train[TARGET])
    diagnostics = {
        "splits": {
            name: {"n": len(part), "min": int(part[TARGET].min()),
                   "max": int(part[TARGET].max()), "mean": float(part[TARGET].mean())}
            for name, part in [("train", train), ("valid", valid), ("test", test)]
        },
        "test_fraction_above_training_max": float((test[TARGET] > train[TARGET].max()).mean()),
        "hgb_test_prediction_range": [float(booster.predict(test[cols]).min()),
                                      float(booster.predict(test[cols]).max())],
        "ridge_standardized_coefficients": dict(zip(cols, ridge[-1].coef_.tolist())),
        "weather_availability": "Conditional evaluation uses realized same-day weather; day-ahead deployment requires issued forecasts.",
    }
    (ROOT / "reports/diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (ROOT / "reports/target_transform_final.json").write_text(
        json.dumps(evaluate(df, cols, include_test=True), indent=2) + "\n"
    )


if __name__ == "__main__":
    res = fit_and_score()
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(res, indent=2) + "\n")
    write_final_diagnostics(pd.read_parquet(PROCESSED))
    print(json.dumps({k: v for k, v in res.items()
                      if k not in {"features", "before_feature", "after_feature"}}, indent=2))
