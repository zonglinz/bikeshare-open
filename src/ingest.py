"""Stage 1: fetch the raw dataset and assert its shape.

Run: python -m src.ingest
"""
import hashlib
import sys
import urllib.request

import pandas as pd

from src.config import DATA_URL, FORBIDDEN, RAW, RAW_FEATURE_INPUTS, RAW_SHA256

EXPECTED_MIN_ROWS = 700
REQUIRED_COLS = {"dteday", "cnt", "casual", "registered", "temp", "hum", "windspeed"}


def download(force: bool = False) -> None:
    if RAW.exists():
        if force:
            raise ValueError("raw data is immutable; refusing --force overwrite")
        return
    RAW.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DATA_URL, RAW)


def validate_raw_columns(df: pd.DataFrame) -> None:
    unknown = set(df.columns) - (FORBIDDEN | RAW_FEATURE_INPUTS | {"dteday"})
    if unknown:
        raise ValueError(f"unclassified raw columns: {sorted(unknown)}")


def verify_raw_hash(path=RAW) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != RAW_SHA256:
        raise ValueError(f"raw SHA-256 mismatch: expected {RAW_SHA256}, got {actual}")


def load_raw() -> pd.DataFrame:
    verify_raw_hash()
    df = pd.read_csv(RAW, parse_dates=["dteday"])
    validate_raw_columns(df)
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"raw data is missing required columns: {sorted(missing)}")
    if len(df) < EXPECTED_MIN_ROWS:
        raise ValueError(f"raw data has only {len(df)} rows; expected >= {EXPECTED_MIN_ROWS}")
    return df


if __name__ == "__main__":
    download(force="--force" in sys.argv)
    df = load_raw()
    print(f"OK ingest: {len(df)} rows, {df.dteday.min().date()} -> {df.dteday.max().date()}")
