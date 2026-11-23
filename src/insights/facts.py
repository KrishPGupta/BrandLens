"""Turn the stored results for one brand into a small dict of verified facts.
Everything the summariser says comes from this dict; nothing is invented."""
import json

import numpy as np
import pandas as pd

from src.config import load_config
from src.drift.zscore_drift import first_sustained_alert
from src.storage import db


def _default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return str(o)


def _r(x, nd=1):
    return None if x is None or pd.isna(x) else round(float(x), nd)


def build_facts(brand, cfg=None):
    cfg = cfg or load_config()
    w = db.query(
        "SELECT week, negative, neutral, positive, n, z_negative, z_positive, flag, driver "
        "FROM weekly_drift WHERE brand = ? ORDER BY week", (brand,), cfg)
    if w.empty:
        raise LookupError(f"No weekly data stored for {brand}")
    w["flag"] = w["flag"].astype(bool)

    first_alert = first_sustained_alert(pd.Series(w["flag"].values, index=w["week"]))
    since = first_alert or w["week"].iloc[max(len(w) - 4, 0)]
    before = w[w["week"] < since]
    recent = w[w["week"] >= since]
    base = before if len(before) else w

    # how many consecutive flagged weeks end at the latest week
    run = 0
    for f in reversed(w["flag"].tolist()):
        if not f:
            break
        run += 1

    directions = {}
    for d in w.loc[w["flag"], "driver"]:
        for part in str(d).split(","):
            part = part.strip()
            if part:
                directions[part] = directions.get(part, 0) + 1

    peak = None
    zs = w[["z_negative", "z_positive"]].abs()
    if zs.notna().any().any():
        i = zs.max(axis=1).idxmax()
        col = zs.loc[i].idxmax()
        peak = {"week": w.loc[i, "week"], "metric": col[2:], "z": _r(w.loc[i, col])}

    last = w.iloc[-1]
    drift = {
        "weeks_flagged": int(w["flag"].sum()),
        "first_sustained_alert": first_alert,
        "consecutive_flagged_weeks": run,
        "flag_directions": directions,
        "strongest_signal": peak,
        "latest_week": {"week": last["week"], "negative": _r(last["negative"]),
                        "positive": _r(last["positive"]), "flagged": bool(last["flag"])},
        "baseline": {"negative": _r(base["negative"].mean()), "positive": _r(base["positive"].mean())},
        "recent": {"since": since, "negative": _r(recent["negative"].mean()),
                   "positive": _r(recent["positive"].mean())},
    }

    # ---- bots ----
    tot = db.query("SELECT COUNT(*) AS total, SUM(is_bot_pred) AS bots FROM predictions WHERE brand = ?",
                   (brand,), cfg).iloc[0]
    win = db.query(
        "SELECT COUNT(*) AS n, SUM(is_bot_pred) AS bots, "
        "100.0 * AVG(pred_label = 'negative') AS b_neg, 100.0 * AVG(pred_label = 'positive') AS b_pos, "
        "100.0 * AVG(CASE WHEN is_bot_pred = 0 THEN (pred_label = 'negative') END) AS a_neg, "
        "100.0 * AVG(CASE WHEN is_bot_pred = 0 THEN (pred_label = 'positive') END) AS a_pos "
        "FROM predictions WHERE brand = ? AND week >= ?", (brand, since), cfg).iloc[0]
    stats = {}
    try:
        for k, v in db.query("SELECT key, value FROM bot_stats", cfg=cfg).values:
            stats[k] = v
    except Exception:
        pass
    total, bots = int(tot["total"]), int(tot["bots"] or 0)
    bots_facts = {
        "posts": total,
        "removed_pct": _r(100 * bots / total) if total else 0.0,
        "accounts_flagged": int(float(stats["flagged_accounts"])) if "flagged_accounts" in stats else None,
        "accounts_total": int(float(stats["total_accounts"])) if "total_accounts" in stats else None,
        "window": {
            "since": since,
            "bot_share_pct": _r(100 * (win["bots"] or 0) / win["n"]) if win["n"] else None,
            "negative_before_filtering": _r(win["b_neg"]), "negative_after_filtering": _r(win["a_neg"]),
            "positive_before_filtering": _r(win["b_pos"]), "positive_after_filtering": _r(win["a_pos"]),
        },
    }

    split = db.query("SELECT pred_label, COUNT(*) AS n FROM predictions WHERE brand = ? AND is_bot_pred = 0 "
                     "GROUP BY pred_label", (brand,), cfg)
    kept = int(split["n"].sum()) or 1
    sentiment = {lab: _r(100 * split.loc[split["pred_label"] == lab, "n"].sum() / kept)
                 for lab in cfg["sentiment"]["labels"]}

    # ---- words behind the predictions (SHAP sample) ----
    words, explained = {}, 0
    try:
        ex = db.query("SELECT post_id, pred_label, token, shap_value FROM explanations WHERE brand = ?",
                      (brand,), cfg)
        explained = int(ex["post_id"].nunique())
        uni = ex[~ex["token"].str.contains(" ")]
        for lab, g in uni.groupby("pred_label"):
            s = g.groupby("token")["shap_value"].sum().sort_values(ascending=False)
            words[lab] = list(s.index[:5])
    except Exception:
        pass

    # ---- models (global) ----
    models, identical = [], False
    try:
        m = db.query("SELECT model, accuracy, f1_macro FROM model_metrics", cfg=cfg)
        m = m[~m["model"].str.endswith("_val")]
        models = [{"model": r.model, "accuracy": float(r.accuracy), "f1_macro": float(r.f1_macro)}
                  for r in m.itertuples()]
        identical = len(models) > 1 and len({(x["accuracy"], x["f1_macro"]) for x in models}) == 1
    except Exception:
        pass

    facts = {
        "brand": brand,
        "data_is_synthetic": cfg["data"]["source"] == "synthetic",
        "method": {"baseline_weeks": cfg["drift"]["window"], "z_threshold": cfg["drift"]["z_threshold"]},
        "period": {"first_week": w["week"].iloc[0], "last_week": w["week"].iloc[-1], "weeks": len(w)},
        "drift": drift,
        "bots": bots_facts,
        "sentiment_after_filtering": sentiment,
        "top_words": words,
        "explained_posts": explained,
        "models": models,
        "models_identical": identical,
    }
    return json.loads(json.dumps(facts, default=_default))
