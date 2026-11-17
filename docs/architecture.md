# Architecture

## Layers

| Layer | Folder | Responsibility |
|---|---|---|
| Data | `src/data` | Load data, remove exact duplicates, clean text, stratified train/val/test split |
| Bot filtering | `src/bot_detection` | Per-account features, Random Forest, flag posts above a probability cutoff |
| Sentiment | `src/sentiment` | TF-IDF+LogReg and DistilBERT behind one `predict()`; shared evaluation |
| Drift | `src/drift` | Weekly sentiment %, rolling baseline, Z-score alerts |
| Explainability | `src/explain` | SHAP (exact LinearExplainer) on a selected sample |
| Storage | `src/storage` | SQLite write/read helpers |
| API | `api/` | FastAPI endpoints reading SQLite, plus live prediction |

## Design decisions

- **Training and serving are separate.** Scripts produce models in `models/`; the API only loads them.
- **One `predict()`** for both sentiment models, so evaluation and serving share code.
- **Thresholds live in `config/config.yaml`** (window, Z threshold, bot cutoff), so sensitivity is tunable without code changes.
- **Store before serve.** `pipeline.py` writes predictions, weekly aggregates, alerts, explanations and metrics to SQLite; SHAP is precomputed because it is slow on transformers.
- **Bot-flagged posts are kept in the database** (flagged, not deleted) so before/after comparisons are possible.
- **Alerts are flags that need review**, never verdicts.

## Drift method

For each brand and week, the share of negative and positive posts is compared with a rolling baseline:

    z = (x_t - mean(baseline)) / max(std(baseline), 1 percentage point)

- Baseline = previous 12 weeks that were **not flagged** (min 8 weeks), so a sustained shift keeps alerting
  instead of becoming the new normal.
- A week is flagged when |z| >= 3.0 for negative or positive share.
- The "first sustained alert" is the first run of 2 consecutive flagged weeks.
- Std floor avoids huge z-scores from a near-flat baseline.

## Data schema

Required: `post_id, brand, text, timestamp`.
For bot detection: `user_id, followers, following, account_age_days, statuses_count`.
For training/evaluation: `label` in {negative, neutral, positive}; `is_bot` (0/1) if available for the bot model.

Account features: followers, following, follower ratio, account age, posting frequency, URL ratio,
hashtag rate, mention rate, duplicate-text ratio, post count.

## SQLite tables

`predictions`, `weekly_drift`, `alerts`, `bot_stats`, `model_metrics`, `explanations`.

## Splitting and leakage

Exact duplicates are removed before splitting. The bot classifier is split by account. Sentiment models
train only on posts that survived bot filtering. Near-duplicate spam is kept through preprocessing on
purpose, because duplicate ratio is a bot feature.
