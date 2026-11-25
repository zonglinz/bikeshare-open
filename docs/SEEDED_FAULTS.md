# Seeded faults and real verification output

The authoring agent was Codex. Hook experiments below invoke the real script with a JSON payload directly; they do not claim an interactive Claude Code hook event. Deliberate mutations use isolated copies, preserving the submission CSV. Repair attempts mean explicit restoration attempts, not local-model conversation turns.

## Feature test written first

Named date: 2012-06-15. Expected value: (4,972 + 7,421 + 7,363) / 3, using June 12–14 only. The following command was run before adding the feature, and the failing test was committed separately.

```text
$ .venv/bin/python -m pytest tests/test_leakage.py::test_three_day_mean_uses_only_prior_calendar_dates -q
F                                                                        [100%]
=================================== FAILURES ===================================
______________ test_three_day_mean_uses_only_prior_calendar_dates ______________

self = Index(['instant', 'season', 'yr', 'mnth', 'holiday', 'weekday', 'temp',
       'atemp', 'hum', 'windspeed', 'casual', ...kday', 'month_sin', 'month_cos',
       'weather_severity', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7'],
      dtype='str')
key = 'cnt_roll_3'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
>           return self._engine.get_loc(casted_key)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.venv/lib/python3.13/site-packages/pandas/core/indexes/base.py:3641: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
pandas/_libs/index.pyx:168: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/index.pyx:197: in pandas._libs.index.IndexEngine.get_loc
    ???
pandas/_libs/hashtable_class_helper.pxi:7668: in pandas._libs.hashtable.PyObjectHashTable.get_item
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

>   ???
E   KeyError: 'cnt_roll_3'

pandas/_libs/hashtable_class_helper.pxi:7676: KeyError

The above exception was the direct cause of the following exception:

feats =         dteday  instant  season  ...  cnt_lag_1 cnt_lag_7   cnt_roll_7
0   2011-01-10     10.0  WINTER  ...      822.0...    1787.0  1530.142857
713 2012-12-31    731.0  WINTER  ...     1796.0     920.0  1531.428571

[714 rows x 28 columns]

    def test_three_day_mean_uses_only_prior_calendar_dates(feats):
        """June 15 uses June 12-14: 4,972, 7,421, and 7,363 rides."""
        date = pd.Timestamp("2012-06-15")
        expected = (4972 + 7421 + 7363) / 3
>       actual = feats.set_index("dteday").loc[date, "cnt_roll_3"]
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_leakage.py:73: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/pandas/core/indexing.py:1199: in __getitem__
    return self.obj._get_value(*key, takeable=self._takeable)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/pandas/core/frame.py:4489: in _get_value
    series = self._get_item(col)
             ^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/pandas/core/frame.py:4969: in _get_item
    loc = self.columns.get_loc(item)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Index(['instant', 'season', 'yr', 'mnth', 'holiday', 'weekday', 'temp',
       'atemp', 'hum', 'windspeed', 'casual', ...kday', 'month_sin', 'month_cos',
       'weather_severity', 'cnt_lag_1', 'cnt_lag_7', 'cnt_roll_7'],
      dtype='str')
key = 'cnt_roll_3'

    def get_loc(self, key):
        """
        Get integer location, slice or boolean mask for requested label.
    
        Parameters
        ----------
        key : label
            The key to check its location if it is present in the index.
    
        Returns
        -------
        int if unique index, slice if monotonic index, else mask
            Integer location, slice or boolean mask.
    
        See Also
        --------
        Index.get_slice_bound : Calculate slice bound that corresponds to
            given label.
        Index.get_indexer : Computes indexer and mask for new index given
            the current index.
        Index.get_non_unique : Returns indexer and masks for new index given
            the current index.
        Index.get_indexer_for : Returns an indexer even when non-unique.
    
        Examples
        --------
        >>> unique_index = pd.Index(list("abc"))
        >>> unique_index.get_loc("b")
        1
    
        >>> monotonic_index = pd.Index(list("abbc"))
        >>> monotonic_index.get_loc("b")
        slice(1, 3, None)
    
        >>> non_monotonic_index = pd.Index(list("abcb"))
        >>> non_monotonic_index.get_loc("b")
        array([False,  True, False,  True])
        """
        casted_key = self._maybe_cast_indexer(key)
        try:
            return self._engine.get_loc(casted_key)
        except KeyError as err:
            if isinstance(casted_key, slice) or (
                isinstance(casted_key, abc.Iterable)
                and any(isinstance(x, slice) for x in casted_key)
            ):
                raise InvalidIndexError(key) from err
>           raise KeyError(key) from err
E           KeyError: 'cnt_roll_3'

.venv/lib/python3.13/site-packages/pandas/core/indexes/base.py:3648: KeyError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_three_day_mean_uses_only_prior_calendar_dates
1 failed in 66.16s (0:01:06)
```

After implementation: `make features test` reported 714 feature rows and `19 passed in 2.13s`.

## Fault 1: bypass forbidden-column filtering

One controlled Codex restoration action; no Claude conversation-turn count was measured. The helper invokes the hook before the separate red pytest run. Exact diff, stdout and hook stderr follow.

```text
Fault: forbidden
Harness: direct JSON hook invocation; not a Claude Code session.

Exact seeded diff:
--- src/features.py
+++ src/features.py
@@ -84,7 +84,7 @@
     """Safe model inputs; rejected candidates can be evaluated explicitly."""
     numeric = [c for c in df.select_dtypes(include="number").columns
                if include_rejected or c not in REJECTED_FEATURES]
-    return [c for c in numeric if c not in FORBIDDEN]
+    return list(numeric)  # seeded fault: bypass FORBIDDEN
 
 
 if __name__ == "__main__":


$ PostToolUse check_leakage.sh < payload.json
exit=2
stdout:
(empty)
stderr:
Leakage tests failed after editing /var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-forbidden-2vocl8ns/repo/src/features.py:
[714 rows x 29 columns]

    def test_no_single_feature_or_pair_exactly_restates_target(feats):
        """Inspect values, so renaming a leaked predictor does not defeat the check."""
        cols = feature_columns(feats)
        y = feats[TARGET].to_numpy(dtype=float)
        for size in (1, 2):
            for subset in combinations(cols, size):
                X = np.column_stack([feats[list(subset)].to_numpy(dtype=float), np.ones(len(y))])
                coef, *_ = np.linalg.lstsq(X, y, rcond=None)
                residual = float(np.max(np.abs(X @ coef - y)))
>               assert residual > 1e-6, f"target identity in {subset}: max residual={residual}"
E               AssertionError: target identity in ('cnt',): max residual=1.8189894035458565e-12
E               assert 1.8189894035458565e-12 > 1e-06

tests/test_leakage.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
FAILED tests/test_leakage.py::test_no_single_feature_or_pair_exactly_restates_target
2 failed, 8 passed in 1.06s


$ python -m pytest tests/test_leakage.py -q
exit=1
stdout:
.F.......F                                                               [100%]
=================================== FAILURES ===================================
__________________________ test_no_forbidden_features __________________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_forbidden_features(feats):
        """Guards the gate, not the data: feature_columns() excludes FORBIDDEN by
        construction, so this cannot discover a *new* leaky column. What it
        catches is someone editing feature_columns() or FORBIDDEN -- which is
        exactly the fault the Step 7 hook demonstrates."""
        cols = set(feature_columns(feats))
>       assert not (cols & FORBIDDEN), f"forbidden columns in feature set: {cols & FORBIDDEN}"
E       AssertionError: forbidden columns in feature set: {'cnt_2d_bfr', 'registered', 'yr', 'days_since_2011', 'cnt', 'instant', 'casual'}
E       assert not ({'atemp', 'casual', 'cnt', 'cnt_2d_bfr', 'cnt_lag_1', 'cnt_lag_7', ...} & {'casual', 'cnt', 'cnt_2d_bfr', 'days_since_2011', 'instant', 'registered', ...})

tests/test_leakage.py:34: AssertionError
____________ test_no_single_feature_or_pair_exactly_restates_target ____________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....142857  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1531.428571  2077.333333

[714 rows x 29 columns]

    def test_no_single_feature_or_pair_exactly_restates_target(feats):
        """Inspect values, so renaming a leaked predictor does not defeat the check."""
        cols = feature_columns(feats)
        y = feats[TARGET].to_numpy(dtype=float)
        for size in (1, 2):
            for subset in combinations(cols, size):
                X = np.column_stack([feats[list(subset)].to_numpy(dtype=float), np.ones(len(y))])
                coef, *_ = np.linalg.lstsq(X, y, rcond=None)
                residual = float(np.max(np.abs(X @ coef - y)))
>               assert residual > 1e-6, f"target identity in {subset}: max residual={residual}"
E               AssertionError: target identity in ('cnt',): max residual=1.8189894035458565e-12
E               assert 1.8189894035458565e-12 > 1e-06

tests/test_leakage.py:94: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_no_forbidden_features - AssertionError: fo...
FAILED tests/test_leakage.py::test_no_single_feature_or_pair_exactly_restates_target
2 failed, 8 passed in 0.52s

stderr:
(empty)

Repair attempts: 1 (restore the exact pre-fault bytes).

$ make test (after restoration)
exit=0
stdout:
python -m pytest tests/ -q
...................                                                      [100%]
19 passed in 2.17s

stderr:
(empty)
```

## Fault 2: include today in the rolling mean

Delete the shift on cnt_roll_7, then restore it in one controlled action. Exact red output and hook stderr:

```text
Fault: rolling
Harness: direct JSON hook invocation; not a Claude Code session.

Exact seeded diff:
--- src/features.py
+++ src/features.py
@@ -74,7 +74,7 @@
     # If you add a longer lag, raise LAG_WARMUP in src/config.py.
     out["cnt_lag_1"] = out[TARGET].shift(1)
     out["cnt_lag_7"] = out[TARGET].shift(LAG_WARMUP)
-    out["cnt_roll_7"] = out[TARGET].shift(1).rolling(LAG_WARMUP).mean()
+    out["cnt_roll_7"] = out[TARGET].rolling(LAG_WARMUP).mean()
     out["cnt_roll_3"] = out[TARGET].shift(1).rolling(3).mean()
 
     return out.dropna().reset_index(drop=True)


$ PostToolUse check_leakage.sh < payload.json
exit=2
stdout:
(empty)
stderr:
Leakage tests failed after editing /var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-rolling-wrc_31j3/repo/src/features.py:
[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:60: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 1.04s


$ python -m pytest tests/test_leakage.py -q
exit=1
stdout:
....F.....                                                               [100%]
=================================== FAILURES ===================================
_______________________ test_rolling_mean_excludes_today _______________________

feats =         dteday  instant  season  ...  cnt_lag_7   cnt_roll_7   cnt_roll_3
0   2011-01-10     10.0  WINTER  ...     134....428571  2183.333333
713 2012-12-31    731.0  WINTER  ...      920.0  1789.857143  2077.333333

[714 rows x 29 columns]

    def test_rolling_mean_excludes_today(feats):
        """cnt_roll_7 must be the mean of the 7 calendar days *before* today."""
        by_date = feats.set_index("dteday")[TARGET]
        date = feats.dteday.iloc[200]
        window = [date - pd.Timedelta(days=k) for k in range(1, 8)]
        if all(d in by_date.index for d in window):
            expected = sum(by_date[d] for d in window) / 7
>           assert feats.set_index("dteday").cnt_roll_7[date] == pytest.approx(expected)
E           assert np.float64(4389.0) == 4414.857142857143 ± 0.00441486
E             
E             comparison failed
E             Obtained: 4389.0
E             Expected: 4414.857142857143 ± 0.00441486

tests/test_leakage.py:60: AssertionError
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_rolling_mean_excludes_today - assert np.fl...
1 failed, 9 passed in 0.50s

stderr:
(empty)

Repair attempts: 1 (restore the exact pre-fault bytes).

$ make test (after restoration)
exit=0
stdout:
python -m pytest tests/ -q
...................                                                      [100%]
19 passed in 2.14s

stderr:
(empty)
```

## Fault 3: remove the weather encoder exception

Remove the unknown-label raise. The added STORM-label test must fail, so the hook can detect this change even though all current CSV weather labels are known. Restore in one controlled action.

```text
Fault: weather
Harness: direct JSON hook invocation; not a Claude Code session.

Exact seeded diff:
--- src/features.py
+++ src/features.py
@@ -27,7 +27,7 @@
     known = series.dropna()
     unknown = set(known.unique()) - set(WEATHER_ORDER)
     if unknown:
-        raise ValueError(f"unmapped weather labels: {sorted(unknown)}")
+        pass  # seeded fault: silently accept unknown weather
     return series.map(WEATHER_ORDER).astype(float)
 
 


$ PostToolUse check_leakage.sh < payload.json
exit=2
stdout:
(empty)
stderr:
Leakage tests failed after editing /var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-weather-d2a413lm/repo/src/features.py:
........F.                                                               [100%]
=================================== FAILURES ===================================
_____________________ test_weather_rejects_unknown_labels ______________________

    def test_weather_rejects_unknown_labels():
>       with pytest.raises(ValueError, match="unmapped weather labels.*STORM"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:81: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_weather_rejects_unknown_labels - Failed: D...
1 failed, 9 passed in 1.05s


$ python -m pytest tests/test_leakage.py -q
exit=1
stdout:
........F.                                                               [100%]
=================================== FAILURES ===================================
_____________________ test_weather_rejects_unknown_labels ______________________

    def test_weather_rejects_unknown_labels():
>       with pytest.raises(ValueError, match="unmapped weather labels.*STORM"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests/test_leakage.py:81: Failed
=========================== short test summary info ============================
FAILED tests/test_leakage.py::test_weather_rejects_unknown_labels - Failed: D...
1 failed, 9 passed in 0.49s

stderr:
(empty)

Repair attempts: 1 (restore the exact pre-fault bytes).

$ make test (after restoration)
exit=0
stdout:
python -m pytest tests/ -q
.........................                                                [100%]
25 passed in 2.93s

stderr:
(empty)
```

## Fault 4: Bash cp bypasses the Edit/Write hook

The helper changes the first row's cnt by one in an isolated replacement file, then really runs Bash cp into the disposable data/raw/. The Bash payload contains no Edit/Write file_path; the PostToolUse guard exits 0 without checking. The new SHA-256 check in load_raw/make data rejects the copy. A Stop hook running the same check, a Bash PreToolUse guard, or filesystem restrictions could provide additional boundaries. No submission raw bytes were modified. Exact cp outcome, hook stderr, hash failure and restoration:

```text
Fault: raw-bash
Harness: direct JSON hook invocation; not a Claude Code session.

$ Bash: cp "$1" "$2"
exit=0
stdout:
(empty)
stderr:
(empty)

Exact seeded diff:
--- data/raw/bike_daily.csv
+++ data/raw/bike_daily.csv
@@ -1,5 +1,5 @@
 "instant","dteday","season","yr","mnth","holiday","weekday","temp","atemp","hum","windspeed","casual","registered","cnt","workday","weather","days_since_2011","cnt_2d_bfr"
-3,"2011-01-03","WINTER","2011","JAN","N","MON",1.229108,22.43977,43.7273,16.636703,120,1229,1349,"Y","GOOD",2,985
+3,2011-01-03,WINTER,2011,JAN,N,MON,1.229108,22.43977,43.7273,16.636703,120,1229,1350,Y,GOOD,2,985
 4,"2011-01-04","WINTER","2011","JAN","N","TUE",1.4,23.212148,59.0435,10.739832,108,1454,1562,"Y","GOOD",3,801
 5,"2011-01-05","WINTER","2011","JAN","N","WED",2.666979,23.79518,43.6957,12.5223,82,1518,1600,"Y","GOOD",4,1349
 6,"2011-01-06","WINTER","2011","JAN","N","THU",1.604356,23.929106,51.8261,6.0008684,88,1518,1606,"Y","GOOD",5,1562


$ PostToolUse check_leakage.sh < payload.json
exit=0
stdout:
(empty)
stderr:
(empty)

$ make data
exit=2
stdout:
python -m src.ingest

stderr:
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/private/var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-raw-bash-f6r2x9ge/repo/src/ingest.py", line 52, in <module>
    df = load_raw()
  File "/private/var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-raw-bash-f6r2x9ge/repo/src/ingest.py", line 39, in load_raw
    verify_raw_hash()
    ~~~~~~~~~~~~~~~^^
  File "/private/var/folders/wv/4rdwzt8n1_s6lh7md0cr5msm0000gn/T/bikeshare-raw-bash-f6r2x9ge/repo/src/ingest.py", line 35, in verify_raw_hash
    raise ValueError(f"raw SHA-256 mismatch: expected {RAW_SHA256}, got {actual}")
ValueError: raw SHA-256 mismatch: expected a6bed1577f6e4de56dcfae6d8315985073cc0ad3446c8c99ed60c86a0b5ad9dc, got bf4fceabfe2ea3a55c5392a175a7de7a6e9282feb860bc9ae9e652ef30d9101b
make: *** [data] Error 1


Repair attempts: 1 (restore the exact pre-fault bytes).

$ make test (after restoration)
exit=0
stdout:
python -m pytest tests/ -q
.........................                                                [100%]
25 passed in 2.03s

stderr:
(empty)
```
