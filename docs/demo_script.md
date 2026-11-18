# BrandLens: Demo script (about 6 minutes)

1. **Pipeline.** Run `python -m src.pipeline --skip-train` (about 3 seconds). Say: raw posts, preprocessing,
   bot filtering, sentiment, drift and SHAP all write to SQLite.
2. **API docs.** Open http://localhost:8000/docs. Say: any frontend can consume these endpoints.
3. **Drift.** GET /api/alerts?brand=Nova shows first_sustained_alert 2025-04-21. Then
   GET /api/brands/Nova/trend: the negative share jumps, z-scores 7 to 13.
4. **Bot filtering.** GET /api/brands/Nova/bot-filtering shows before/after distributions. Say: bots posting
   positive spam hid part of the drift (positive 46.6% vs 24.1% after filtering).
5. **Explainability.** GET /api/brands/Nova/explanations, then one post. Say: the sentiment word carries
   the weight, the brand name is near zero.
6. **Models.** GET /api/models/metrics, then POST /api/predict with model distilbert and with tfidf_lr.

## Questions to expect

- **Why do both models score the same?** The synthetic labels carry about 8% random word noise, so both reach
  the same ceiling and miss the same noisy posts. Real data is where a transformer should separate.
- **Why is bot AUC 1.0?** Synthetic bots are easy by construction (many links, repeated text, young accounts).
  It is not a real-world claim; real labelled data (TwiBot-20, Cresci) would score lower.
- **Why is Zenith flagged?** A 3-sigma rule over many brand-weeks produces occasional false alarms. That is
  why alerts say "needs review", not "drift confirmed".
- **Is the data real?** No. The pipeline is dataset-agnostic; config.yaml points it at a real CSV.

7. **Model agreement.** On the 3,404 test posts TF-IDF and DistilBERT agree on 100%, and both make 284 errors
   (8.3%). The synthetic labels carry about 8% word-label contradictions, so that is the ceiling for any model.
