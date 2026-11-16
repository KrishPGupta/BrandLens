"""One predict() for every sentiment model, so the dashboard and evaluation share code."""
import joblib
import numpy as np
import pandas as pd
from src.config import load_config, resolve
from src.data.preprocess import clean_text, normalize

_cache = {}


def _labels(cfg):
    return cfg["sentiment"]["labels"]          # order: negative, neutral, positive


def _load(model_name, cfg):
    if model_name in _cache:
        return _cache[model_name]
    mdir = resolve(cfg, "models")
    if model_name == "tfidf_lr":
        obj = joblib.load(mdir / "tfidf_lr.joblib")
    elif model_name == "distilbert":
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        path = mdir / "distilbert"
        obj = (AutoTokenizer.from_pretrained(path),
               AutoModelForSequenceClassification.from_pretrained(path).eval(), torch)
    else:
        raise ValueError(f"Unknown model: {model_name}")
    _cache[model_name] = obj
    return obj


def predict(texts, model_name="tfidf_lr", cfg=None, batch_size=64):
    """texts: list/Series of RAW post text. Returns DataFrame: label, confidence, prob_<label>."""
    cfg = cfg or load_config()
    labels = _labels(cfg)
    texts = [str(t) for t in texts]
    cleaned = [clean_text(t) for t in texts]
    model = _load(model_name, cfg)

    if model_name == "tfidf_lr":
        proba = model.predict_proba([normalize(c) for c in cleaned])
        classes = list(model.classes_)
        proba = proba[:, [classes.index(l) for l in labels]]
    else:
        tok, net, torch = model
        chunks = []
        for i in range(0, len(cleaned), batch_size):
            enc = tok(cleaned[i:i + batch_size], truncation=True, max_length=128,
                      padding=True, return_tensors="pt")
            with torch.no_grad():
                chunks.append(torch.softmax(net(**enc).logits, dim=-1).numpy())
        proba = np.vstack(chunks)

    out = pd.DataFrame(proba, columns=[f"prob_{l}" for l in labels])
    out.insert(0, "confidence", proba.max(axis=1))
    out.insert(0, "label", [labels[i] for i in proba.argmax(axis=1)])
    return out
