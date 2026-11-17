import json
import sqlite3
from contextlib import closing
import pandas as pd
from src.config import load_config, resolve

PRED_COLS = ["post_id", "brand", "week", "timestamp", "user_id", "text", "pred_label",
             "confidence", "model", "bot_prob", "is_bot_pred", "label"]


def get_conn(cfg=None):
    cfg = cfg or load_config()
    return sqlite3.connect(resolve(cfg, "db"))


def _write(df, table, cfg):
    with closing(get_conn(cfg)) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)
        conn.commit()


def save_predictions(df, cfg=None):
    cfg = cfg or load_config()
    out = df[[c for c in PRED_COLS if c in df.columns]].copy()
    out = out.rename(columns={"label": "true_label"})
    for c in ["week", "timestamp"]:
        out[c] = pd.to_datetime(out[c]).dt.strftime("%Y-%m-%d %H:%M:%S")
    _write(out, "predictions", cfg)
    with closing(get_conn(cfg)) as conn:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pred ON predictions(brand, week)")
        conn.commit()


def save_weekly(df, cfg=None):
    cfg = cfg or load_config()
    out = df.copy()
    out["week"] = pd.to_datetime(out["week"]).dt.strftime("%Y-%m-%d")
    _write(out, "weekly_drift", cfg)
    _write(out[out["flag"]], "alerts", cfg)


def save_bot_stats(stats, cfg=None):
    cfg = cfg or load_config()
    _write(pd.DataFrame({"key": list(stats), "value": [str(v) for v in stats.values()]}),
           "bot_stats", cfg)


def save_metrics(df, cfg=None):
    _write(df, "model_metrics", cfg or load_config())


def load_results(table, cfg=None, brand=None):
    """Dashboard entry point: read a stored table, optionally for one brand."""
    cfg = cfg or load_config()
    sql, params = f"SELECT * FROM {table}", ()
    if brand is not None:
        sql, params = sql + " WHERE brand = ?", (brand,)
    with closing(get_conn(cfg)) as conn:
        return pd.read_sql(sql, conn, params=params)


def save_explanations(df, cfg=None):
    _write(df, "explanations", cfg or load_config())


def query(sql, params=(), cfg=None):
    """Run a read-only SQL query and return a DataFrame."""
    cfg = cfg or load_config()
    with closing(get_conn(cfg)) as conn:
        return pd.read_sql(sql, conn, params=params)
