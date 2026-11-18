# BrandLens

AI-based social media sentiment analysis for **brand sentiment drift detection**, with bot filtering and
explainable predictions. Backend only: a pipeline that fills SQLite, and a REST API that any frontend can call.

## Pipeline

    posts (CSV) -> preprocess (NLTK/Pandas) -> bot detection (Random Forest on account features)
      -> sentiment (TF-IDF+LogReg baseline | DistilBERT) -> weekly aggregation
      -> drift detection (rolling Z-score) -> SHAP explanations -> SQLite -> FastAPI

Bot-flagged posts are excluded before sentiment is aggregated. Drift alerts are flags that need review,
not verdicts.

## Setup

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

## Run

    python -m src.pipeline                 # preprocess, train, filter, score, detect drift, explain, write SQLite
    python -m src.pipeline --skip-train    # reuse saved models
    python -m uvicorn api.main:app --reload --port 8000    # API; interactive docs at /docs
    python -m pytest -q

DistilBERT is fine-tuned on a GPU (Colab): src/sentiment/distilbert_finetune.py trains on
data/processed/train.csv, val.csv and test.csv. Copy the saved folder to models/distilbert/, then run
`python -m src.sentiment.eval_distilbert`.

## API

| Endpoint | Returns |
|---|---|
| GET /api/health, /api/config, /api/brands | status, thresholds, brand list |
| GET /api/summary | global counts, bot share, brands with flags |
| GET /api/brands/{brand}/overview?include_bots= | sentiment split |
| GET /api/brands/{brand}/trend | weekly percentages, z-scores, flags |
| GET /api/alerts?brand= | flagged weeks, first sustained alert |
| GET /api/brands/{brand}/bot-filtering | before/after distributions, weekly negative share |
| GET /api/brands/{brand}/explanations, GET /api/explanations/{post_id} | SHAP word contributions |
| GET /api/models/metrics | accuracy, P/R/F1, confusion-matrix image URLs |
| POST /api/predict | live sentiment (tfidf_lr or distilbert) |

CORS origins for a frontend dev server are set in config/config.yaml.

## Project layout

    config/config.yaml      thresholds, window, paths, brands, CORS
    src/data                loader, synthetic generator, preprocessing
    src/bot_detection       account features, Random Forest, filtering
    src/sentiment           TF-IDF+LR, DistilBERT, shared predict(), evaluation
    src/drift               weekly aggregation, rolling Z-score detection
    src/explain             SHAP on selected predictions
    src/storage             SQLite helpers
    src/pipeline.py         end-to-end run
    api/                    FastAPI backend
    tests/                  pytest suite
    reports/                metrics, figures, alerts, explanations

## Results (synthetic data)

| Model | Accuracy | Macro-F1 |
|---|---|---|
| TF-IDF + Logistic Regression | 0.917 | 0.911 |
| DistilBERT | 0.917 | 0.911 |

- Drift: Nova's negative share jumps from week 15; the first sustained alert is the week of 2025-04-21.
- Bot filtering: about 12.7% of posts removed. In Nova's drift period the positive share reads 46.6%
  before filtering and 24.1% after, so bot spam hides the drift.

## Limitations

- The default dataset is **synthetic** (data.source: synthetic). About 8% of labels are random word noise,
  which caps both models near 92%. The bot classifier scores AUC 1.0 because synthetic bots are easy by
  construction. Neither number is a real-world claim.
- A 3-sigma threshold over many brand-weeks produces occasional false alarms (one appears for Zenith).
- To use real data, set data.source to csv and provide the columns listed in docs/architecture.md.
