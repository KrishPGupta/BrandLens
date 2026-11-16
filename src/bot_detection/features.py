import pandas as pd

FEATURES = ["followers", "following", "follower_ratio", "account_age_days",
            "posting_freq", "url_ratio", "hashtag_ratio", "mention_ratio",
            "dup_ratio", "n_posts"]


def build_account_features(df):
    """One row per account. Uses post-level stats from preprocess.add_text_stats."""
    g = df.groupby("user_id")
    acc = g.agg(
        followers=("followers", "first"),
        following=("following", "first"),
        account_age_days=("account_age_days", "first"),
        statuses_count=("statuses_count", "first"),
        n_posts=("post_id", "count"),
        url_ratio=("url_count", lambda s: (s > 0).mean()),
        hashtag_ratio=("hashtag_count", "mean"),
        mention_ratio=("mention_count", "mean"),
        n_unique=("text_clean", "nunique"),
    )
    acc["dup_ratio"] = 1 - acc["n_unique"] / acc["n_posts"]
    acc["follower_ratio"] = acc["followers"] / (acc["following"] + 1)
    acc["posting_freq"] = acc["statuses_count"] / (acc["account_age_days"] + 1)
    if "is_bot" in df.columns:
        acc["is_bot"] = g["is_bot"].first()
    return acc.reset_index()
