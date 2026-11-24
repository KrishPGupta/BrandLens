# BrandLens

Brand sentiment drift monitoring for social media. BrandLens reads posts, sets bot activity aside,
labels the sentiment of what is left, flags the weeks where opinion about a brand shifts, shows the
words behind each label, and writes a plain-English summary of every dashboard page.

A final-year B.Tech project. The default dataset is synthetic (see Limitations).

## What it does

- **Bot filtering:** a Random Forest scores every account (follower ratio, account age, posting rate, links, repeated text). Suspected bots are kept in the database but excluded from sentiment.
- **Sentiment:** a TF-IDF + Logistic Regression baseline and a fine-tuned DistilBERT behind one predict() call.
- **Drift alerts:** each week's positive and negative share is compared with the previous 12 normal weeks; a move beyond 3 standard deviations is flagged as "needs review".
- **Explanations:** SHAP word contributions for a sample of posts.
- **Plain-English summaries:** every dashboard page opens with a short briefing built from the numbers on that page.
- **Dashboard and API:** a React dashboard reads a FastAPI backend that serves results stored in SQLite.

## How it fits together

    posts -> clean -> bot filter -> sentiment -> weekly drift -> SHAP -> SQLite -> REST API -> dashboard
                                                                              \-> facts -> verified draft -> optional AI rewrite -> checks -> summary panel

## Quick start

### 1. Backend

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python -m src.pipeline
    python -m uvicorn api.main:app --port 8000

- The first run downloads NLTK stopwords, so it needs internet once.
- `data/` and `models/` are not in git. The pipeline generates the dataset, trains the models and fills the SQLite database (about a few seconds on a laptop).
- Interactive API docs: http://localhost:8000/docs

### 2. Dashboard

    cd frontend
    cp .env.example .env
    npm install
    npm run dev

Open http://localhost:5173 for the website and http://localhost:5173/dashboard for the dashboard. Keep the API running.

### 3. Optional: AI-written summaries with a local model

    brew install ollama
    brew services run ollama
    ollama pull llama3.2:3b

With the model installed, summaries are rewritten by it. Without it, the dashboard shows rule-based summaries built from the same numbers, and the panel says which one you are reading. Settings are under `insights:` in `config/config.yaml`. An Anthropic key in a git-ignored `.env` (ANTHROPIC_API_KEY=...) works as a second option. Stop the local server with `brew services stop ollama`.

### 4. Optional: DistilBERT

DistilBERT is fine-tuned on a GPU (Google Colab, T4). Upload `data/processed/train.csv`, `val.csv`, `test.csv` and `src/sentiment/distilbert_finetune.py`, run the script, download the saved folder into `models/distilbert/`, then run:

    python -m src.sentiment.eval_distilbert

The repo already includes the DistilBERT scores from our Colab run (`reports/results.csv`), so the Models page shows them on a fresh clone. The model weights (about 255 MB) are not in git, so live DistilBERT prediction through `/api/predict` needs this step.

## Tests

    python -m pytest -q

Run the pipeline first; the tests read the SQLite database it creates.

## Dashboard pages

| Page | Shows |
|---|---|
| Overview | sentiment split, bot share, flagged weeks, recent alerts |
| Trends and drift | weekly sentiment, distance from normal, flagged weeks |
| Bot filtering | before and after filtering, weekly negative share |
| Explanations | SHAP word contributions per post |
| Models | accuracy, precision, recall, F1, confusion matrices |

## API

| Endpoint | Returns |
|---|---|
| GET /api/health, /api/config, /api/brands | status, thresholds, brand list |
| GET /api/summary | global counts and bot share |
| GET /api/brands/{brand}/overview?include_bots= | sentiment split |
| GET /api/brands/{brand}/trend | weekly percentages, z-scores, flags |
| GET /api/alerts?brand= | flagged weeks, first sustained alert |
| GET /api/brands/{brand}/bot-filtering | before/after distributions, weekly negative share |
| GET /api/brands/{brand}/explanations, GET /api/explanations/{post_id} | SHAP word contributions |
| GET /api/brands/{brand}/summary?focus=overview/drift/bots/models | plain-English briefing |
| GET /api/models/metrics | model scores and confusion-matrix images |
| POST /api/predict | live sentiment for any text |

## Project layout

    config/config.yaml      thresholds, window, paths, brands, summary settings
    src/data                dataset generator, loading, preprocessing
    src/bot_detection       account features, Random Forest, filtering
    src/sentiment           TF-IDF+LR, DistilBERT, shared predict(), evaluation
    src/drift               weekly aggregation, rolling Z-score detection
    src/explain             SHAP on selected predictions
    src/insights            facts, rule-based writer, AI rewrite and its checks
    src/storage             SQLite helpers
    src/pipeline.py         end-to-end run
    api/                    FastAPI backend
    frontend/               React + Vite + Tailwind website and dashboard
    tests/                  pytest suite
    docs/                   architecture, summarizer design, demo script

## How the summaries stay honest

The statistics produce a verified draft. A small language model may only rewrite it in friendlier words. Any rewrite that quotes a number not in the data, or drops the key figures, is rejected and the rule-based text is shown instead. Every panel says who wrote it and lists the data it used. Details: docs/summarizer.md.

## Limitations

- The default dataset is synthetic. About 8% of its labels are random word noise, which caps both sentiment models near 92%, and the two models score identically. The bot classifier scores AUC 1.0 because the synthetic bots are easy to spot. None of these are real-world claims. Use `data.source: csv` in `config/config.yaml` for a real dataset.
- A 3-sigma rule over many brand-weeks produces occasional false alarms, which is why alerts say "needs review".
- The checks on AI-written text verify numbers, not every qualifier, so read the data behind a summary when it matters.

## Credits

Photos by Ilgmyzin and Jay Openiano on Unsplash.
