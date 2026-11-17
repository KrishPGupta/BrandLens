import pandas as pd
from src.config import load_config
from src.storage import db


def test_weekly_roundtrip(tmp_path):
    cfg = load_config()
    cfg["paths"]["db"] = str(tmp_path / "t.db")
    weekly = pd.DataFrame({"brand": ["Nova", "Nova"],
                           "week": pd.to_datetime(["2025-01-06", "2025-01-13"]),
                           "negative": [30.0, 60.0], "flag": [False, True]})
    db.save_weekly(weekly, cfg)
    assert len(db.load_results("weekly_drift", cfg, brand="Nova")) == 2
    assert len(db.load_results("alerts", cfg)) == 1
