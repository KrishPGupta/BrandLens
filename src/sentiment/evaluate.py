import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)
from src.config import load_config, resolve


def report(y_true, y_pred, model_name, labels=None, cfg=None):
    """Accuracy, macro P/R/F1, confusion matrix. Saves figure + upserts reports/results.csv."""
    cfg = cfg or load_config()
    labels = labels or cfg["sentiment"]["labels"]
    acc = accuracy_score(y_true, y_pred)
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels,
                                                 average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(4.5, 4))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, cm[i, j], ha="center", va="center")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix: {model_name}")
    fig.tight_layout()
    figdir = resolve(cfg, "reports") / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(figdir / f"cm_{model_name}.png", dpi=150)
    plt.close(fig)

    path = resolve(cfg, "reports") / "results.csv"
    row = pd.DataFrame([{"model": model_name, "accuracy": round(acc, 4),
                         "precision_macro": round(p, 4), "recall_macro": round(r, 4),
                         "f1_macro": round(f, 4)}])
    if path.exists():
        old = pd.read_csv(path)
        row = pd.concat([old[old["model"] != model_name], row], ignore_index=True)
    row.to_csv(path, index=False)

    print(f"\n== {model_name} ==  accuracy={acc:.4f}  macro-F1={f:.4f}")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))
    return {"accuracy": acc, "precision_macro": p, "recall_macro": r,
            "f1_macro": f, "confusion_matrix": cm.tolist()}
