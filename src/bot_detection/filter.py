import json
import joblib
import pandas as pd
from src.config import load_config, resolve
from src.bot_detection.features import build_account_features


def filter_bots(df, bundle, cutoff):
    """Score every account, flag posts from accounts with bot_prob >= cutoff.
    Returns ALL posts with flags (dashboard needs before/after) plus removal stats."""
    acc = build_account_features(df)
    acc["bot_prob"] = bundle["model"].predict_proba(acc[bundle["features"]])[:, 1]
    out = df.merge(acc[["user_id", "bot_prob"]], on="user_id", how="left")
    out["is_bot_pred"] = out["bot_prob"] >= cutoff

    total, removed = len(out), int(out["is_bot_pred"].sum())
    stats = {
        "cutoff": cutoff,
        "total_posts": total,
        "removed_posts": removed,
        "removed_pct": round(100 * removed / total, 2),
        "total_accounts": int(acc["user_id"].nunique()),
        "flagged_accounts": int((acc["bot_prob"] >= cutoff).sum()),
    }
    if "is_bot" in out.columns:   # ground truth available (synthetic / labeled data)
        tp = int((out["is_bot_pred"] & (out["is_bot"] == 1)).sum())
        stats["post_precision"] = round(tp / max(removed, 1), 4)
        stats["post_recall"] = round(tp / max(int((out["is_bot"] == 1).sum()), 1), 4)
        stats["bot_posts_remaining"] = int((~out["is_bot_pred"] & (out["is_bot"] == 1)).sum())
    return out, stats


def run(cfg=None):
    cfg = cfg or load_config()
    bundle = joblib.load(resolve(cfg, "models") / "bot_rf.joblib")
    df = pd.read_csv(resolve(cfg, "interim") / "clean.csv", parse_dates=["timestamp"])
    out, stats = filter_bots(df, bundle, cfg["bot"]["prob_cutoff"])
    out.to_csv(resolve(cfg, "processed") / "filtered_posts.csv", index=False)
    with open(resolve(cfg, "reports") / "bot_stats.json", "w") as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats, indent=2))
    return out, stats


if __name__ == "__main__":
    run()
