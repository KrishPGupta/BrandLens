"""Brand Sentiment Drift API. Reads results the pipeline stored in SQLite.
   Run:  python -m uvicorn api.main:app --reload --port 8000     Docs: http://localhost:8000/docs"""
import json
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.schemas import PredictRequest, PredictResponse
from src.config import load_config, resolve
from src.drift.zscore_drift import first_sustained_alert
from src.sentiment.predict import predict
from src.storage import db

CFG = load_config()
LABELS = CFG["sentiment"]["labels"]
BRANDS = CFG["brands"]

app = FastAPI(
    title="Brand Sentiment Drift API",
    version="1.0.0",
    description="Bot-filtered sentiment, drift alerts and SHAP explanations. "
                "Alerts are flags that need review, not verdicts.",
)
app.add_middleware(CORSMiddleware,
                   allow_origins=CFG.get("api", {}).get("cors_origins", ["*"]),
                   allow_methods=["*"], allow_headers=["*"])

_figdir = resolve(CFG, "reports") / "figures"
_figdir.mkdir(parents=True, exist_ok=True)
app.mount("/static/figures", StaticFiles(directory=_figdir), name="figures")


# ---------- helpers ----------
def q(sql, params=()):
    if not resolve(CFG, "db").exists():
        raise HTTPException(503, "Database not built. Run: python -m src.pipeline")
    return db.query(sql, params, CFG)


def rec(df):
    """DataFrame -> list of dicts, NaN -> null."""
    return json.loads(df.to_json(orient="records"))


def check_brand(brand):
    match = next((b for b in BRANDS if b.lower() == brand.lower()), None)
    if match is None:
        raise HTTPException(404, f"Unknown brand '{brand}'. Known brands: {BRANDS}")
    return match


def distribution(df):
    """df has columns pred_label, n -> counts and percentages per label."""
    counts = {l: int(df.loc[df["pred_label"] == l, "n"].sum()) for l in LABELS}
    total = sum(counts.values())
    pct = {l: (round(100 * c / total, 2) if total else 0.0) for l, c in counts.items()}
    return {"total": total, "counts": counts, "pct": pct}


def _num(v):
    try:
        return float(v) if "." in str(v) else int(v)
    except (TypeError, ValueError):
        return v


# ---------- meta ----------
@app.get("/api/health", tags=["meta"])
def health():
    models = resolve(CFG, "models")
    return {"status": "ok",
            "database": resolve(CFG, "db").exists(),
            "models": {"tfidf_lr": (models / "tfidf_lr.joblib").exists(),
                       "bot_rf": (models / "bot_rf.joblib").exists(),
                       "distilbert": (models / "distilbert").exists()}}


@app.get("/api/config", tags=["meta"])
def config():
    return {"brands": BRANDS, "labels": LABELS, "drift": CFG["drift"],
            "bot_prob_cutoff": CFG["bot"]["prob_cutoff"], "data_source": CFG["data"]["source"]}


@app.get("/api/brands", tags=["meta"])
def brands():
    return {"brands": BRANDS}


# ---------- results ----------
@app.get("/api/summary", tags=["results"])
def summary():
    p = q("SELECT COUNT(*) AS posts, SUM(is_bot_pred) AS bot_posts FROM predictions").iloc[0]
    per_brand = q("SELECT brand, COUNT(*) AS weeks_flagged, MIN(week) AS first_flag, "
                  "MAX(week) AS last_flag FROM alerts GROUP BY brand")
    posts, bots = int(p["posts"]), int(p["bot_posts"] or 0)
    return {"posts": posts, "bot_posts": bots,
            "bot_pct": round(100 * bots / posts, 2) if posts else 0.0,
            "brands_monitored": len(BRANDS),
            "weeks_flagged_total": int(per_brand["weeks_flagged"].sum()) if len(per_brand) else 0,
            "brands_with_flags": rec(per_brand)}


@app.get("/api/brands/{brand}/overview", tags=["results"])
def overview(brand: str, include_bots: bool = False):
    b = check_brand(brand)
    extra = "" if include_bots else " AND is_bot_pred = 0"
    d = q(f"SELECT pred_label, COUNT(*) AS n FROM predictions WHERE brand = ?{extra} GROUP BY pred_label", (b,))
    flagged = int(q("SELECT COUNT(*) AS c FROM alerts WHERE brand = ?", (b,))["c"].iloc[0])
    return {"brand": b, "include_bots": include_bots, **distribution(d), "weeks_flagged": flagged}


@app.get("/api/brands/{brand}/trend", tags=["results"])
def trend(brand: str):
    b = check_brand(brand)
    df = q("SELECT week, negative, neutral, positive, n, z_negative, z_positive, flag, driver, status "
           "FROM weekly_drift WHERE brand = ? ORDER BY week", (b,))
    df["flag"] = df["flag"].astype(bool)
    return {"brand": b, "window_weeks": CFG["drift"]["window"], "z_threshold": CFG["drift"]["z_threshold"],
            "weeks": rec(df)}


@app.get("/api/alerts", tags=["results"])
def alerts(brand: Optional[str] = Query(None, description="Filter to one brand")):
    sql = ("SELECT brand, week, driver, negative, positive, z_negative, z_positive, status FROM alerts")
    params = ()
    if brand:
        sql, params = sql + " WHERE brand = ?", (check_brand(brand),)
    out = {"alerts": rec(q(sql + " ORDER BY brand, week", params))}
    if brand:
        w = q("SELECT week, flag FROM weekly_drift WHERE brand = ? ORDER BY week", (params[0],))
        first = first_sustained_alert(pd.Series(w["flag"].astype(bool).values, index=w["week"]))
        out["first_sustained_alert"] = first
    return out


@app.get("/api/brands/{brand}/bot-filtering", tags=["results"])
def bot_filtering(brand: str):
    b = check_brand(brand)
    allp = q("SELECT pred_label, COUNT(*) AS n FROM predictions WHERE brand = ? GROUP BY pred_label", (b,))
    kept = q("SELECT pred_label, COUNT(*) AS n FROM predictions WHERE brand = ? AND is_bot_pred = 0 "
             "GROUP BY pred_label", (b,))
    before, after = distribution(allp), distribution(kept)
    weekly = q("SELECT substr(week, 1, 10) AS week, "
               "100.0 * AVG(pred_label = 'negative') AS before_negative_pct, "
               "100.0 * AVG(CASE WHEN is_bot_pred = 0 THEN (pred_label = 'negative') END) AS after_negative_pct "
               "FROM predictions WHERE brand = ? GROUP BY 1 ORDER BY 1", (b,))
    stats = {k: _num(v) for k, v in zip(*q("SELECT key, value FROM bot_stats").T.values)}
    return {"brand": b,
            "removed_posts": before["total"] - after["total"],
            "removed_pct": round(100 * (before["total"] - after["total"]) / before["total"], 2) if before["total"] else 0.0,
            "before": before, "after": after,
            "weekly_negative": rec(weekly.round(2)),
            "overall_stats": stats}


@app.get("/api/brands/{brand}/explanations", tags=["explainability"])
def explained_posts(brand: str, label: Optional[str] = None):
    b = check_brand(brand)
    sql, params = ("SELECT DISTINCT post_id, pred_label, confidence, text FROM explanations WHERE brand = ?", (b,))
    if label:
        sql, params = sql + " AND pred_label = ?", (b, label)
    return {"brand": b, "posts": rec(q(sql + " ORDER BY confidence DESC", params))}


@app.get("/api/explanations/{post_id}", tags=["explainability"])
def explanation(post_id: int):
    df = q("SELECT brand, text, pred_label, confidence, token, shap_value FROM explanations "
           "WHERE post_id = ? ORDER BY ABS(shap_value) DESC", (post_id,))
    if df.empty:
        raise HTTPException(404, f"No explanation stored for post {post_id}")
    head = df.iloc[0]
    return {"post_id": post_id, "brand": head["brand"], "text": head["text"],
            "pred_label": head["pred_label"], "confidence": float(head["confidence"]),
            "tokens": rec(df[["token", "shap_value"]])}


@app.get("/api/models/metrics", tags=["models"])
def model_metrics():
    df = q("SELECT * FROM model_metrics")
    rows = rec(df)
    for r in rows:
        f = _figdir / f"cm_{r['model']}.png"
        r["confusion_matrix_url"] = f"/static/figures/{f.name}" if f.exists() else None
    return {"models": rows}


# ---------- live inference ----------
@app.post("/api/predict", response_model=PredictResponse, tags=["inference"])
def predict_sentiment(req: PredictRequest):
    try:
        out = predict(req.texts, req.model, CFG)
    except (FileNotFoundError, OSError, ImportError) as e:
        raise HTTPException(503, f"Model '{req.model}' is not available: {e}")
    items = [{"text": t, "label": r["label"], "confidence": float(r["confidence"]),
              "probabilities": {l: float(r[f"prob_{l}"]) for l in LABELS}}
             for t, (_, r) in zip(req.texts, out.iterrows())]
    return {"model": req.model, "results": items}
