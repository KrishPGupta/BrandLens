import numpy as np
import pandas as pd
from src.config import load_config, resolve
from src.drift.aggregate import score_posts, weekly_distribution


def detect_drift_series(series, window=8, threshold=2.0, min_baseline_weeks=6, std_floor=1.0):
    """Z-score each week against a rolling baseline of the previous `window` NON-FLAGGED weeks."""
    vals = series.to_numpy(float)
    z = np.full(len(vals), np.nan)
    flag = np.zeros(len(vals), dtype=bool)
    clean = []                                   # indices of weeks not flagged
    for t, x in enumerate(vals):
        if np.isnan(x):
            continue
        base = vals[clean[-window:]]
        if len(base) >= min_baseline_weeks:
            sd = max(base.std(ddof=1), std_floor)
            z[t] = (x - base.mean()) / sd
            flag[t] = abs(z[t]) >= threshold
        if not flag[t]:
            clean.append(t)
    return pd.DataFrame({"z": z, "flag": flag}, index=series.index)


def detect_drift(weekly, window=8, threshold=2.0, min_baseline_weeks=6,
                 monitor=("negative", "positive")):
    """weekly: output of weekly_distribution. Adds z_<label>, flag, driver, status columns."""
    out = weekly.copy()
    flags = pd.DataFrame(index=weekly.index)
    for lab in monitor:
        r = detect_drift_series(weekly[lab], window, threshold, min_baseline_weeks)
        out[f"z_{lab}"] = r["z"]
        flags[lab] = r["flag"]
    out["flag"] = flags.any(axis=1)
    drivers = []
    for _, row in out.iterrows():
        if not row["flag"]:
            drivers.append("")
            continue
        lab = max(monitor, key=lambda l: abs(row[f"z_{l}"]) if pd.notna(row[f"z_{l}"]) else 0)
        drivers.append(f"{lab} {'up' if row[f'z_{lab}'] > 0 else 'down'}")
    out["driver"] = drivers
    out["status"] = np.where(out["flag"], "needs review", "normal")   # flags, not verdicts
    return out


def run(cfg=None):
    cfg = cfg or load_config()
    d = cfg["drift"]
    params = dict(window=d["window"], threshold=d["z_threshold"], min_baseline_weeks=d["min_baseline_weeks"])

    scored = score_posts(cfg)
    kept = scored[~scored["is_bot_pred"]]

    frames = []
    for brand in cfg["brands"]:
        res = detect_drift(weekly_distribution(kept, brand, cfg=cfg), **params)
        res.insert(0, "brand", brand)
        frames.append(res.reset_index())
        print(f"{brand}: {int(res['flag'].sum())} weeks flagged of {len(res)}")
    allres = pd.concat(frames, ignore_index=True)
    allres.to_csv(resolve(cfg, "processed") / "weekly_drift.csv", index=False)
    allres[allres["flag"]].to_csv(resolve(cfg, "reports") / "drift_alerts.csv", index=False)

    # detail for Nova + before/after bot filtering comparison
    nova = allres[allres["brand"] == "Nova"].set_index("week")
    print("\nNova weekly (after bot filtering):")
    print(nova[["negative", "positive", "z_negative", "z_positive", "status", "driver"]].round(1).to_string())

    if nova["flag"].any():
        first = nova.index[nova["flag"]][0]
        print(f"\nFirst Nova alert: {first.date()}")
        for name, frame in [("after filtering ", kept), ("before filtering", scored)]:
            w = weekly_distribution(frame, "Nova", cfg=cfg)
            pre, post = w.loc[w.index < first, "negative"].mean(), w.loc[w.index >= first, "negative"].mean()
            print(f"  {name}: negative % {pre:.1f} -> {post:.1f}  (shift {post - pre:+.1f} pts)")
    return allres


if __name__ == "__main__":
    run()
