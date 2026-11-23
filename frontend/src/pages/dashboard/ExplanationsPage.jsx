import { useState } from "react";
import { useBrand } from "../../context/BrandContext";
import { useFetch } from "../../lib/api";
import Panel from "../../components/dashboard/Panel";
import { ErrorNote, Loading, PageHeader } from "../../components/dashboard/States";

const FILTERS = ["all", "negative", "neutral", "positive"];
const COLOR = { negative: "var(--color-neg)", neutral: "var(--color-neu)", positive: "var(--color-pos)" };

function Detail({ postId }) {
  const { data, error, loading } = useFetch(`/api/explanations/${postId}`);
  if (loading) return <Loading>Loading explanation…</Loading>;
  if (error) return <p className="text-sm text-ink-950">{error}</p>;

  const tokens = [...data.tokens].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));
  const max = Math.max(...tokens.map((t) => Math.abs(t.shap_value)), 0.001);

  return (
    <div>
      <p className="font-display text-xl text-ink-950">&ldquo;{data.text}&rdquo;</p>
      <p className="mt-2 text-sm text-slate">
        Predicted <strong style={{ color: COLOR[data.pred_label] }}>{data.pred_label}</strong> with {(data.confidence * 100).toFixed(0)}% confidence.
      </p>
      <ul className="mt-5 space-y-2">
        {tokens.map((t) => {
          const support = t.shap_value >= 0;
          return (
            <li key={t.token} className="flex items-center gap-3 text-sm">
              <span className="w-32 shrink-0 truncate text-ink-950" title={t.token}>
                {t.token}
              </span>
              <div className="h-3 flex-1 rounded-full bg-paper-line/60">
                <div
                  className="h-3 rounded-full"
                  style={{ width: `${(Math.abs(t.shap_value) / max) * 100}%`, background: support ? "var(--color-pos)" : "var(--color-neg)" }}
                />
              </div>
              <span className="w-28 shrink-0 text-right text-xs text-slate">{support ? "supports" : "works against"}</span>
            </li>
          );
        })}
      </ul>
      <p className="mt-4 text-xs text-slate">Longer bars mean the word mattered more to the prediction. Two-word entries are phrases the model also looked at.</p>
    </div>
  );
}

export default function ExplanationsPage() {
  const { brand } = useBrand();
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const list = useFetch(brand ? `/api/brands/${brand}/explanations${filter === "all" ? "" : `?label=${filter}`}` : null);

  if (!brand) return <Loading />;
  const posts = list.data?.posts ?? [];
  const active = selected && posts.some((p) => p.post_id === selected) ? selected : posts[0]?.post_id;

  return (
    <>
      <PageHeader
        eyebrow="Explanations"
        title={`${brand}: why a post was labelled this way`}
        description="For a sample of posts, SHAP shows which words pushed the model toward its answer, so a label is something you can check rather than take on trust."
      />

      <div className="mb-5 flex flex-wrap gap-2" role="group" aria-label="Filter by predicted label">
        {FILTERS.map((f) => (
          <button key={f} type="button" onClick={() => setFilter(f)} aria-pressed={filter === f} className={`btn ${filter === f ? "" : "btn-ghost"} capitalize`}>
            {f}
          </button>
        ))}
      </div>

      {list.error && <ErrorNote message={list.error} />}
      {list.loading && <Loading>Loading posts…</Loading>}

      {list.data && posts.length === 0 && (
        <Panel>
          <p className="text-sm text-slate">No explained posts for this brand{filter !== "all" ? ` with a ${filter} label` : ""}. Explanations are pre-computed for a small sample of posts, so some brands have few.</p>
        </Panel>
      )}

      {posts.length > 0 && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
          <Panel label="Sample posts">
            <ul className="max-h-[28rem] overflow-y-auto">
              {posts.map((p) => (
                <li key={p.post_id} className="border-b border-paper-line last:border-0">
                  <button type="button" onClick={() => setSelected(p.post_id)} aria-current={active === p.post_id} className={`w-full py-3 text-left ${active === p.post_id ? "text-ink-950" : "text-slate hover:text-ink-950"}`}>
                    <span className="block text-sm leading-snug">{p.text}</span>
                    <span className="mt-1 block text-xs" style={{ color: COLOR[p.pred_label] }}>
                      {p.pred_label}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel label="Words behind the label">{active != null && <Detail postId={active} />}</Panel>
        </div>
      )}
    </>
  );
}
