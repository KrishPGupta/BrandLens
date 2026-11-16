import pandas as pd
from src.config import load_config, resolve
from src.sentiment.predict import predict


def add_week(df, col="timestamp"):
    df = df.copy()
    df["week"] = pd.to_datetime(df[col]).dt.to_period("W").dt.start_time   # Monday-start weeks
    return df


def score_posts(cfg=None, model_name="tfidf_lr"):
    """Run the chosen sentiment model on every post (bot-flagged posts included, so the
    dashboard can show before vs after filtering). Saves data/processed/scored_posts.csv."""
    cfg = cfg or load_config()
    df = pd.read_csv(resolve(cfg, "processed") / "filtered_posts.csv", parse_dates=["timestamp"])
    pred = predict(df["text"], model_name, cfg)
    df["pred_label"] = pred["label"].values
    df["confidence"] = pred["confidence"].values
    df["model"] = model_name
    df = add_week(df)
    df.to_csv(resolve(cfg, "processed") / "scored_posts.csv", index=False)
    return df


def weekly_distribution(df, brand, label_col="pred_label", cfg=None):
    """Week x negative/neutral/positive percentages (+ post count n) for one brand."""
    cfg = cfg or load_config()
    labels = cfg["sentiment"]["labels"]
    d = df[df["brand"] == brand]
    counts = d.groupby(["week", label_col]).size().unstack(fill_value=0)
    counts = counts.reindex(columns=labels, fill_value=0)
    n = counts.sum(axis=1)
    pct = counts.div(n, axis=0) * 100
    pct["n"] = n
    full = pd.date_range(pct.index.min(), pct.index.max(), freq="W-MON")
    pct = pct.reindex(full)
    pct["n"] = pct["n"].fillna(0).astype(int)
    pct.index.name = "week"
    return pct
