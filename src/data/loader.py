import pandas as pd
from sklearn.model_selection import train_test_split
from src.config import load_config, resolve, ROOT
from src.data.synthetic import generate

REQUIRED = ["post_id", "brand", "text", "timestamp"]
ACCOUNT_COLS = ["user_id", "followers", "following", "account_age_days", "statuses_count"]


def load_raw(cfg=None):
    cfg = cfg or load_config()
    if cfg["data"]["source"] == "synthetic":
        path = resolve(cfg, "raw") / "posts_synthetic.csv"
        if not path.exists():
            generate(seed=cfg["data"]["random_seed"], brands=tuple(cfg["brands"])).to_csv(path, index=False)
    else:
        path = ROOT / cfg["data"]["csv_path"]
    df = pd.read_csv(path, parse_dates=["timestamp"])
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    return df


def split(df, cfg=None, label_col="label"):
    """Stratified train/val/test split. Call AFTER dedup so no copy of a post lands in two splits."""
    cfg = cfg or load_config()
    seed = cfg["data"]["random_seed"]
    train_val, test = train_test_split(df, test_size=cfg["data"]["test_size"],
                                       stratify=df[label_col], random_state=seed)
    val_frac = cfg["data"]["val_size"] / (1 - cfg["data"]["test_size"])
    train, val = train_test_split(train_val, test_size=val_frac,
                                  stratify=train_val[label_col], random_state=seed)
    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)
