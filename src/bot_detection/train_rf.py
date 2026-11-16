import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from src.config import load_config, resolve
from src.bot_detection.features import build_account_features, FEATURES


def train(cfg=None):
    cfg = cfg or load_config()
    seed = cfg["data"]["random_seed"]
    cutoff = cfg["bot"]["prob_cutoff"]
    df = pd.read_csv(resolve(cfg, "interim") / "clean.csv")
    acc = build_account_features(df)
    X, y = acc[FEATURES], acc["is_bot"]

    # split by ACCOUNT, so no account appears in both train and test
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
    rf = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                                random_state=seed, n_jobs=-1).fit(Xtr, ytr)

    proba = rf.predict_proba(Xte)[:, 1]
    pred = (proba >= cutoff).astype(int)
    metrics = {
        "auc": float(roc_auc_score(yte, proba)),
        "cutoff": cutoff,
        "report": classification_report(yte, pred, output_dict=True),
        "feature_importance": {f: float(round(v, 4)) for f, v in zip(FEATURES, rf.feature_importances_)},
    }
    save(rf, metrics, cfg)
    print(f"AUC={metrics['auc']:.3f}")
    print(classification_report(yte, pred, target_names=["human", "bot"]))
    print("Top features:", sorted(metrics["feature_importance"].items(), key=lambda x: -x[1])[:5])
    return rf, metrics


def save(rf, metrics, cfg):
    joblib.dump({"model": rf, "features": FEATURES}, resolve(cfg, "models") / "bot_rf.joblib")
    with open(resolve(cfg, "reports") / "bot_model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    train()
