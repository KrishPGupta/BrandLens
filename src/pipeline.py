"""Run the full chain end to end and fill SQLite for the dashboard.
   python -m src.pipeline               # everything
   python -m src.pipeline --skip-train  # reuse saved models, just re-filter / re-score / re-detect
"""
import argparse
import json
import time
import pandas as pd
from src.config import load_config, resolve
from src.data import preprocess
from src.bot_detection import train_rf, filter as bot_filter
from src.sentiment import baseline_lr
from src.sentiment.evaluate import report
from src.drift import zscore_drift
from src.storage import db


def _step(name):
    print(f"\n{'=' * 8} {name} {'=' * 8}")
    return time.time()


def run_all(cfg=None, skip_train=False):
    cfg = cfg or load_config()
    t_all = time.time()

    t = _step("1/5 preprocess")
    preprocess.run(cfg)
    print(f"({time.time() - t:.1f}s)")

    if not skip_train:
        t = _step("2/5 bot detection: train Random Forest")
        train_rf.train(cfg)
        print(f"({time.time() - t:.1f}s)")
    t = _step("2/5 bot detection: filter")
    _, stats = bot_filter.run(cfg)
    print(f"({time.time() - t:.1f}s)")

    if not skip_train:
        t = _step("3/5 sentiment baseline: train + evaluate")
        train, val, test = baseline_lr.make_splits(cfg)
        pipe = baseline_lr.fit_tfidf_lr(train, cfg)
        baseline_lr.save(pipe, cfg)
        report(val["label"], pipe.predict(val["text_norm"]), "tfidf_lr_val", cfg=cfg)
        report(test["label"], pipe.predict(test["text_norm"]), "tfidf_lr", cfg=cfg)
        print(f"({time.time() - t:.1f}s)")

    t = _step("4/5 score posts + drift detection")
    weekly = zscore_drift.run(cfg)
    print(f"({time.time() - t:.1f}s)")

    t = _step("5/5 write SQLite")
    scored = pd.read_csv(resolve(cfg, "processed") / "scored_posts.csv", parse_dates=["timestamp", "week"])
    db.save_predictions(scored, cfg)
    db.save_weekly(weekly, cfg)
    db.save_bot_stats(stats, cfg)
    results = resolve(cfg, "reports") / "results.csv"
    if results.exists():
        db.save_metrics(pd.read_csv(results), cfg)
    for tbl in ["predictions", "weekly_drift", "alerts", "bot_stats", "model_metrics"]:
        try:
            print(f"  {tbl}: {len(db.load_results(tbl, cfg))} rows")
        except Exception:
            print(f"  {tbl}: (missing)")
    print(f"\nDone in {time.time() - t_all:.1f}s -> {resolve(cfg, 'db')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-train", action="store_true")
    run_all(skip_train=ap.parse_args().skip_train)
