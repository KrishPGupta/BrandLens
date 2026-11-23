import { useState } from "react";
import { useFetch } from "../../lib/api";
import Panel from "./Panel";

function Block({ title, items }) {
  if (!items?.length) return null;
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-ink-950 font-body">{title}</h3>
      <ul className="space-y-2 text-sm leading-relaxed text-slate">
        {items.map((t) => (
          <li key={t} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brass" aria-hidden="true" />
            <span>{t}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Plain-English briefing for the current page. `focus` is overview | drift | bots | models. */
export default function AiSummary({ brand, focus = "overview", title = "In plain English" }) {
  const [nonce, setNonce] = useState(0);
  const [copied, setCopied] = useState(false);
  const path = brand ? `/api/brands/${brand}/summary?focus=${focus}${nonce ? `&refresh=true&_=${nonce}` : ""}` : null;
  const { data, error, loading } = useFetch(path);

  const copy = async () => {
    const text = [data.headline, "", data.summary, "", ...data.key_points.map((t) => `- ${t}`), "", ...data.next_steps.map((t) => `Next: ${t}`)].join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked: nothing to do */
    }
  };

  return (
    <Panel label={title} className="mb-6" aria-busy={loading}>
      {loading && (
        <div role="status" aria-live="polite">
          <p className="text-sm text-slate">Writing the summary…</p>
          <div className="mt-4 space-y-3 animate-pulse" aria-hidden="true">
            <div className="h-6 w-2/3 rounded bg-paper-line/70" />
            <div className="h-4 w-full rounded bg-paper-line/50" />
            <div className="h-4 w-5/6 rounded bg-paper-line/50" />
          </div>
        </div>
      )}

      {error && <p className="text-sm text-ink-950">{error}</p>}

      {data && (
        <>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2">
              {data.source === "llm" ? (
                <span className="tag tag-ok">Written by AI{data.model ? ` · ${data.model}` : ""}</span>
              ) : (
                <span className="tag">Rule-based summary</span>
              )}
              <span className="text-xs text-slate">Built only from the numbers on this dashboard</span>
            </div>
            <div className="flex gap-2">
              <button type="button" className="btn btn-ghost" onClick={copy}>
                {copied ? "Copied" : "Copy"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={() => setNonce((n) => n + 1)}>
                Regenerate
              </button>
            </div>
          </div>

          <h3 className="font-display text-2xl leading-snug text-ink-950">{data.headline}</h3>
          <p className="mt-3 max-w-3xl leading-relaxed text-ink-700">{data.summary}</p>

          <div className="mt-6 grid gap-6 md:grid-cols-3">
            <Block title="Key points" items={data.key_points} />
            <Block title="Watch out for" items={data.watch_outs} />
            <Block title="What to check next" items={data.next_steps} />
          </div>

          {data.note && <p className="mt-5 text-xs text-slate">{data.note}</p>}

          <details className="mt-4 text-sm">
            <summary className="cursor-pointer text-ink-700 underline underline-offset-4 decoration-ink-900/30">
              Show the data this summary used
            </summary>
            <pre className="mt-3 max-h-72 overflow-auto rounded bg-paper-dim/70 p-4 text-xs leading-relaxed text-ink-950">{JSON.stringify(data.facts, null, 2)}</pre>
          </details>
        </>
      )}
    </Panel>
  );
}
