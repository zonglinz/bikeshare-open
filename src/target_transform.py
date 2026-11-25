"""Exercise 4: predict demand changes, then add yesterday's known count.

The default command evaluates validation only. --include-test is reserved
for the frozen final evaluation; it is not used to select a transformation.
"""
import argparse
import json

import pandas as pd
from sklearn.base import clone
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import PROCESSED, ROOT, TARGET
from src.features import feature_columns
from src.train import MODELS, temporal_split


def evaluate(df, cols, include_test=False):
    train, valid, test = temporal_split(df)
    parts = [("valid", valid)]
    if include_test:
        parts.append(("test", test))

    def score(y, predictions):
        return {
            "r2": round(float(r2_score(y, predictions)), 4),
            "mae": round(float(mean_absolute_error(y, predictions)), 1),
        }

    results = {
        "transformation": "delta_cnt = cnt - cnt_lag_1; inverse = cnt_lag_1 + predicted_delta",
        "selection_split": "valid",
        "test_evaluated": include_test,
        "features": cols,
    }
    for name, estimator in MODELS.items():
        model = clone(estimator).fit(train[cols], train[TARGET])
        results[name] = {
            name_: score(part[TARGET], model.predict(part[cols])) for name_, part in parts
        }
    residual_model = clone(MODELS["hgb"]).fit(
        train[cols], train[TARGET] - train["cnt_lag_1"]
    )
    results["hgb_delta"] = {
        name: score(part[TARGET], part["cnt_lag_1"].to_numpy() + residual_model.predict(part[cols]))
        for name, part in parts
    }
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-test", action="store_true")
    args = parser.parse_args()
    df = pd.read_parquet(PROCESSED)
    result = evaluate(df, feature_columns(df), args.include_test)
    suffix = "final" if args.include_test else "validation"
    out = ROOT / "reports" / f"target_transform_{suffix}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
