import numpy as np
import pandas as pd
from src.drift.zscore_drift import detect_drift_series


def test_step_change_is_flagged_and_stays_flagged():
    rng = np.random.default_rng(0)
    s = pd.Series(np.r_[30 + rng.normal(0, 2, 20), 55 + rng.normal(0, 2, 6)])
    r = detect_drift_series(s)
    assert r["flag"].iloc[20:].all()          # baseline is frozen, so alerts persist
    assert r["flag"].iloc[:20].sum() <= 3


def test_stable_series_mostly_quiet():
    rng = np.random.default_rng(1)
    r = detect_drift_series(pd.Series(30 + rng.normal(0, 2, 40)))
    assert r["flag"].mean() < 0.15
