import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from src.config import load_config, resolve
from src.data.loader import split
from src.sentiment.evaluate import report


def make_splits(cfg):
    """Train only on posts that survived bot filtering; save splits so Colab/DistilBERT reuses them."""
    df = pd.read_csv(resolve(cfg, "processed") / "filtered_posts.csv")
    df = df[~df["is_bot_pred"]].dropna(subset=["text_norm", "label"])
    train, val, test = split(df, cfg)
    out = resolve(cfg, "processed")
    for name, part in [("train", train), ("val", val), ("test", test)]:
        part.to_csv(out / f"{name}.csv", index=False)
    print(f"train={len(train)} val={len(val)} test={len(test)}")
    return train, val, test


def fit_tfidf_lr(train, cfg):
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2,
                                  max_features=cfg["sentiment"]["tfidf_max_features"])),
        ("lr", LogisticRegression(max_iter=1000, C=2.0)),
    ])
    return pipe.fit(train["text_norm"], train["label"])


def save(pipe, cfg):
    joblib.dump(pipe, resolve(cfg, "models") / "tfidf_lr.joblib")


if __name__ == "__main__":
    cfg = load_config()
    train, val, test = make_splits(cfg)
    pipe = fit_tfidf_lr(train, cfg)
    save(pipe, cfg)
    report(val["label"], pipe.predict(val["text_norm"]), "tfidf_lr_val", cfg=cfg)
    report(test["label"], pipe.predict(test["text_norm"]), "tfidf_lr", cfg=cfg)
