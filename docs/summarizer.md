# How the summaries work

Every dashboard page opens with a short plain-English briefing. The design goal is that a reader who
cannot read charts still gets the right message, and that nothing in it can be invented.

## The pipeline

1. **Facts.** `src/insights/facts.py` reads the stored results for one brand and builds a small dictionary: drift, bot effect, top SHAP words, model scores. Every number the summary can use comes from here.
2. **Verified draft.** `template_summary()` writes a headline, summary, key points, watch-outs and next steps from the facts using fixed rules. Its numbers and directions of change are correct by construction.
3. **Optional rewrite.** If a local model (Ollama, llama3.2:3b) or an API key is available, the model is asked to rewrite the draft in friendlier words. It does not analyse the data. Its output is constrained to a JSON schema.
4. **Checks.** The rewrite is accepted only if:
   - every percentage, decimal or large number it quotes exists in the facts (a change between two stored numbers is allowed), and
   - it keeps at least two of the draft's key figures, so it cannot stay vague.
5. **Fallback.** If there is no model, the call fails, or a check rejects the text, the rule-based draft is shown with a one-line reason.
6. **Cache.** Accepted summaries are cached in memory per brand, page and data state. Failed AI attempts are not cached.

## What the reader sees

The panel is labelled "Rule-based summary" or "Written by AI" with the model name. A toggle shows the exact data used. Copy and Regenerate buttons are provided.

## Why this design

- Language models are good at wording and unreliable with arithmetic and trends, so the statistics stay in code and the model only handles wording.
- A local model needs no key, no quota and no internet, and no data leaves the machine. Only aggregate numbers and a few top words are used.
- A first attempt asked a small model to analyse the facts directly. It produced a vague summary that called a 21-point rise in negative posts "a slight decrease". The rewrite design and the key-figures check came from that result.

## Limits

- The checks verify numbers, not every qualifier. One accepted rewrite said bots made up 29.6% of posts without saying "since the alert began", which is true only for that period.
- Word lists come from a small SHAP sample.
- A 3-billion-parameter model reads plainer than a large hosted one and sometimes fails the checks; the rule-based text covers those cases.
- On the demo dataset all figures are synthetic, and the summaries say so.

## Configuration

`insights:` in `config/config.yaml` sets the provider (auto, ollama or anthropic), the local model name and the Anthropic model. In auto mode a running local model is used first, then an Anthropic key, then the rule-based writer.
