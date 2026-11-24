# Demo script (about 8 minutes)

## Start-up, in this order (do it 10 minutes before)

Close heavy apps first (extra browser tabs, Colab, Docker). Use three terminal tabs.

Tab 1, local model (optional; without it the summaries are rule-based):

    brew services run ollama

Tab 2, API:

    cd ~/sentiment-drift-monitor && source .venv/bin/activate
    unset ANTHROPIC_API_KEY
    python -m src.pipeline --skip-train
    python -m uvicorn api.main:app --port 8000

Tab 3, dashboard:

    cd ~/sentiment-drift-monitor/frontend && npm run dev

Warm the summaries once (about three minutes with a local model) so nobody waits during the demo:

    for b in Nova Pulse Zenith; do for f in overview drift bots models; do curl -s -m 180 -o /dev/null "localhost:8000/api/brands/$b/summary?focus=$f"; echo "warmed $b $f"; done; done

Open http://localhost:5173. After the demo: `brew services stop ollama`.

## Walkthrough

1. **Website (30 s).** Say what BrandLens does: reads posts, sets bots aside, flags the weeks where opinion shifts, and shows why. Scroll to the six-step pipeline. Click Open dashboard.
2. **Overview, Nova (1.5 min).** Read the plain-English panel. Point out the tag (rule-based or written by AI) and click "Show the data this summary used". Say: every number in this text comes from the data underneath. Show the stat cards: 11 of 26 weeks flagged, latest week needs review.
3. **Trends and drift (1.5 min).** The shaded weeks are flagged. The first sustained alert is the week of 21 Apr 2025: negative posts went from 31.8% to 52.8% and positive from 45.6% to 25.1%. Show the distance-from-normal chart and the dashed 3-standard-deviation line.
4. **Bot filtering (1 min).** About 12.7% of all posts were set aside. Before and after bars differ; in the drift period bots were hiding about 5.7 points of the negative shift.
5. **Explanations (1 min).** Pick a negative post. The sentiment word (for example "hate" or "scam") carries the weight; the brand name carries almost none.
6. **Models (1 min).** Both models score 91.7% accuracy, F1 0.91. Say why they are identical (see below).
7. **Brand switch and fallback (1 min).** Switch to Pulse (no weeks flagged) and Zenith (two isolated flags). To show the fallback, stop Ollama and click Regenerate: the panel switches to a rule-based summary with a note.
8. **API (30 s, optional).** Open http://localhost:8000/docs and run POST /api/predict with a sentence.

## Numbers to have ready

- Dataset: 19,500 synthetic posts, 26 weeks, 3 brands, about 12.7% bot posts.
- Nova: 11 of 26 weeks flagged, first sustained alert 21 Apr 2025. Pulse: 0 flagged. Zenith: 2 isolated weeks (10 and 17 Mar 2025).
- Sentiment models: 91.7% accuracy, macro-F1 0.91 on 3,404 test posts; both make the same 284 errors (8.3%).
- Bot classifier: AUC 1.0 on the synthetic data.

## Questions to expect

- **Why do both models score the same?** The synthetic labels carry about 8% random word noise, so both models reach the same ceiling and miss the same noisy posts. Real data is where a transformer should separate from the baseline.
- **Why is the bot AUC 1.0?** The synthetic bots are easy by construction (many links, repeated text, young accounts). It is not a real-world claim.
- **Is the data real?** No, it is generated for the project and every page says so. The pipeline accepts a real CSV through config/config.yaml.
- **Why is Zenith flagged?** A 3-sigma rule over many brand-weeks occasionally flags a normal week. That is why alerts say "needs review" and not "drift confirmed".
- **How do you stop the AI inventing things?** It never analyses the data. Statistics produce a verified draft, the model only rewrites it, and two checks reject any rewrite that quotes a number not in the data or drops the key figures. The data used is one click away.
- **Does the check catch everything?** No. It checks numbers, not every qualifier. One accepted rewrite said bots made up 29.6% of posts without saying "since the alert began". That is why the data panel exists.
- **Why a small local model?** No key, no quota, no internet, and nothing leaves the laptop. The trade-off is plainer wording, covered by the checks and the rule-based fallback.
- **What if the local model is not running?** The panel falls back to the rule-based summary and says so.
