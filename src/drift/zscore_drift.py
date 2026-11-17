import numpy as np
import pandas as pd
from src.config import load_config, resolve
from src.drift.aggregate import score_posts, weekly_distribution


def detect_drift_series(series, window=12, threshold=3.0, min_baseline_weeks=8, std_floor=1.0):
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


def detect_drift(weekly, window=12, threshold=3.0, min_baseline_weeks=8,
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
    for i in range(len(out)):
        parts = [f"{lab} {'up' if out[f'z_{lab}'].iloc[i] > 0 else 'down'}"
                 for lab in monitor if flags[lab].iloc[i]]
        drivers.append(", ".join(parts))
    out["driver"] = drivers
    out["status"] = np.where(out["flag"], "needs review", "normal")   # flags, not verdicts
    return out


def first_sustained_alert(flag, min_run=2):
    """First week that starts a run of >= min_run consecutive flagged weeks."""
    f = flag.to_numpy(bool)
    for i in range(len(f) - min_run + 1):
        if f[i:i + min_run].all():
            return flag.index[i]
    return None


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
        wk = [str(w.date()) for w in res.index[res["flag"]]]
        print(f"{brand}: {len(wk)} weeks flagged of {len(res)} {wk}")
    allres = pd.concat(frames, ignore_index=True)
    allres.to_csv(resolve(cfg, "processed") / "weekly_drift.csv", index=False)
    allres[allres["flag"]].to_csv(resolve(cfg, "reports") / "drift_alerts.csv", index=False)

    nova = allres[allres["brand"] == "Nova"].set_index("week")
    print("\nNova weekly (after bot filtering):")
    print(nova[["negative", "positive", "z_negative", "z_positive", "status", "driver"]].round(1).to_string())

    first = first_sustained_alert(nova["flag"])
    if first is None:
        print("\nNo sustained Nova alert found.")
    else:
        print(f"\nFirst sustained Nova alert: {first.date()}")
        for name, frame in [("after filtering ", kept), ("before filtering", scored)]:
            w = weekly_distribution(frame, "Nova", cfg=cfg)
            pre, post = w.loc[w.index < first, "negative"].mean(), w.loc[w.index >= first, "negative"].mean()
            print(f"  {name}: negative % {pre:.1f} -> {post:.1f}  (shift {post - pre:+.1f} pts)")
    return allres


if __name__ == "__main__":
    run()
