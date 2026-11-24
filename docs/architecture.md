# Architecture

## Layers

| Layer | Folder | Responsibility |
|---|---|---|
| Data | src/data | Generate or load posts, remove exact duplicates, clean text, stratified train/val/test split |
| Bot filtering | src/bot_detection | Per-account features, Random Forest, flag posts above a probability cutoff |
| Sentiment | src/sentiment | TF-IDF+LogReg and DistilBERT behind one predict(); shared evaluation |
| Drift | src/drift | Weekly sentiment shares, rolling baseline, Z-score alerts |
| Explainability | src/explain | SHAP (exact LinearExplainer) on a selected sample |
| Storage | src/storage | SQLite write and read helpers |
| Insights | src/insights | Facts per brand, rule-based writer, optional AI rewrite with checks |
| API | api/ | FastAPI endpoints reading SQLite, plus live prediction and summaries |
| Dashboard | frontend/ | React, Vite and Tailwind: public website and five dashboard pages |

## Data flow

    posts -> clean -> bot filter -> sentiment -> weekly drift -> SHAP -> SQLite
    SQLite -> REST API -> dashboard
    SQLite -> facts -> verified draft -> optional AI rewrite -> checks -> summary panel

## Design decisions

- **Training and serving are separate.** Scripts produce models in models/; the API only loads them.
- **One predict()** for both sentiment models, so evaluation and serving share code.
- **Thresholds live in config/config.yaml** (window, Z threshold, bot cutoff, summary provider), so sensitivity is tunable without code changes.
- **Store before serve.** pipeline.py writes predictions, weekly aggregates, alerts, explanations and metrics to SQLite. SHAP is precomputed because it is slow on transformers.
- **Bot-flagged posts stay in the database** (flagged, not deleted), so before and after comparisons are possible.
- **The frontend only talks to the API.** Any other client can use the same endpoints.
- **Alerts are flags that need review**, never verdicts.
- **Summaries are grounded.** Statistics produce a verified draft; a language model may only rewrite it, and checks reject invented numbers or dropped key figures. See docs/summarizer.md.

## Drift method

For each brand and week, the share of negative and positive posts is compared with a rolling baseline:

    z = (x_t - mean(baseline)) / max(std(baseline), 1 percentage point)

- Baseline = previous 12 weeks that were not flagged (minimum 8), so a sustained shift keeps alerting instead of becoming the new normal.
- A week is flagged when |z| >= 3.0 for the negative or positive share.
- The first sustained alert is the first run of 2 consecutive flagged weeks.
- The standard deviation floor avoids huge z-scores from a near-flat baseline.

## Data schema

- Required: post_id, brand, text, timestamp.
- For bot detection: user_id, followers, following, account_age_days, statuses_count.
- For training and evaluation: label in {negative, neutral, positive}; is_bot (0 or 1) if available.

Account features: followers, following, follower ratio, account age, posting frequency, URL ratio, hashtag rate, mention rate, duplicate-text ratio, post count.

## SQLite tables

predictions, weekly_drift, alerts, bot_stats, model_metrics, explanations.

## Splitting and leakage

Exact duplicates are removed before splitting. The bot classifier is split by account. Sentiment models train only on posts that survived bot filtering. Near-duplicate spam is kept through preprocessing on purpose, because the duplicate ratio is a bot feature.

## Running it

See README.md. Order of start-up for a demo: local model (optional), API, dashboard.
