import joblib
import numpy as np
import pandas as pd
import shap
from src.config import load_config, resolve
from src.data.preprocess import clean_text, normalize


def explain(texts, ids=None, model_name="tfidf_lr", cfg=None, top_k=6, n_background=500):
    """Word-level SHAP contributions toward each post's PREDICTED class.
    Returns rows: post_id, pred_label, token, shap_value (positive = pushes toward the predicted label)."""
    if model_name != "tfidf_lr":
        raise NotImplementedError("DistilBERT SHAP is slow; run it on a few samples in Colab "
                                  "(shap.Explainer on the HF pipeline).")
    cfg = cfg or load_config()
    texts = [str(t) for t in texts]
    ids = list(ids) if ids is not None else list(range(len(texts)))

    pipe = joblib.load(resolve(cfg, "models") / "tfidf_lr.joblib")
    tfidf, lr = pipe.named_steps["tfidf"], pipe.named_steps["lr"]
    names = tfidf.get_feature_names_out()
    classes = list(lr.classes_)

    train = pd.read_csv(resolve(cfg, "processed") / "train.csv")["text_norm"].fillna("")
    bg = tfidf.transform(train.sample(n_background, random_state=cfg["data"]["random_seed"])).toarray()
    X = tfidf.transform([normalize(clean_text(t)) for t in texts])

    sv = shap.LinearExplainer(lr, bg).shap_values(X.toarray())
    if isinstance(sv, list):                       # older shap: list of (n, f) per class
        sv = np.stack(sv, axis=-1)
    if sv.ndim == 3 and sv.shape[0] == len(classes) and sv.shape[0] != len(texts):
        sv = np.moveaxis(sv, 0, -1)                # (classes, n, f) -> (n, f, classes)

    proba = lr.predict_proba(X)
    rows = []
    for i in range(len(texts)):
        c = int(proba[i].argmax())
        present = X[i].nonzero()[1]
        contrib = sv[i, :, c]
        for j in sorted(present, key=lambda j: -abs(contrib[j]))[:top_k]:
            rows.append({"post_id": ids[i], "pred_label": classes[c],
                         "token": names[j], "shap_value": float(contrib[j])})
    return pd.DataFrame(rows)


def run(cfg=None):
    cfg = cfg or load_config()
    df = pd.read_csv(resolve(cfg, "processed") / "scored_posts.csv")
    df = df[~df["is_bot_pred"]]
    seed = cfg["data"]["random_seed"]
    parts = [df[df["pred_label"] == l].sample(10, random_state=seed) for l in ["positive", "negative"]]
    parts.append(df.nsmallest(10, "confidence"))
    sel = pd.concat(parts).drop_duplicates("post_id").reset_index(drop=True)

    ex = explain(sel["text"], ids=sel["post_id"], cfg=cfg)
    ex = ex.merge(sel[["post_id", "brand", "text", "confidence"]], on="post_id", how="left")
    ex.to_csv(resolve(cfg, "reports") / "explanations.csv", index=False)
    print(f"SHAP: {sel['post_id'].nunique()} posts, {len(ex)} word contributions")
    return ex


if __name__ == "__main__":
    run()
