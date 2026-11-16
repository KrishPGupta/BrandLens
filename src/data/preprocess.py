import re
import pandas as pd
from nltk.tokenize import TweetTokenizer
from src.config import load_config, resolve
from src.data.loader import load_raw

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#\w+")
KEEP = {"not", "no", "nor", "never", "n't"}   # negations matter for sentiment

try:
    from nltk.corpus import stopwords
    _STOP = set(stopwords.words("english")) - KEEP
except LookupError:
    import nltk
    nltk.download("stopwords", quiet=True)
    from nltk.corpus import stopwords
    _STOP = set(stopwords.words("english")) - KEEP

_tok = TweetTokenizer(preserve_case=False, reduce_len=True, strip_handles=True)


def add_text_stats(df):
    """Counts from the RAW text; needed later as bot features."""
    df = df.copy()
    df["url_count"] = df["text"].str.count(URL_RE)
    df["hashtag_count"] = df["text"].str.count(HASHTAG_RE)
    df["mention_count"] = df["text"].str.count(MENTION_RE)
    return df


def clean_text(t):
    t = str(t).lower()
    t = URL_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    t = t.replace("#", " ")
    t = re.sub(r"[^a-z0-9' ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def normalize(text_clean):
    toks = _tok.tokenize(text_clean)
    return " ".join(t for t in toks if t.replace("'", "").isalpha() and t not in _STOP)


def remove_duplicates(df):
    keys = [c for c in ["user_id", "text", "timestamp"] if c in df.columns]
    return df.drop_duplicates(subset=keys).reset_index(drop=True)


def run(cfg=None):
    cfg = cfg or load_config()
    df = load_raw(cfg)
    n0 = len(df)
    df = add_text_stats(remove_duplicates(df))
    df["text_clean"] = df["text"].map(clean_text)
    df = df[df["text_clean"].str.len() > 0].copy()
    df["text_norm"] = df["text_clean"].map(normalize)
    out = resolve(cfg, "interim") / "clean.csv"
    df.to_csv(out, index=False)
    print(f"raw={n0}  clean={len(df)}  saved -> {out}")
    return df


if __name__ == "__main__":
    run()
