import { useBrand } from "../../context/BrandContext";
import { useFetch } from "../../lib/api";
import { num, pct } from "../../lib/format";
import AiSummary from "../../components/dashboard/AiSummary";
import LineChart from "../../components/dashboard/LineChart";
import Panel from "../../components/dashboard/Panel";
import { ErrorNote, Loading, PageHeader, Stat } from "../../components/dashboard/States";

const LABELS = [
  { key: "negative", label: "Negative", color: "var(--color-neg)" },
  { key: "neutral", label: "Neutral", color: "var(--color-neu)" },
  { key: "positive", label: "Positive", color: "var(--color-pos)" },
];

function Compare({ before, after }) {
  return (
    <ul className="space-y-5">
      {LABELS.map((l) => (
        <li key={l.key}>
          <p className="mb-2 text-sm text-ink-950">{l.label}</p>
          {[
            ["Before filtering", before.pct[l.key], 0.45],
            ["After filtering", after.pct[l.key], 1],
          ].map(([name, value, opacity]) => (
            <div key={name} className="mb-1.5 flex items-center gap-3">
              <span className="w-28 shrink-0 text-xs text-slate">{name}</span>
              <div className="h-3 flex-1 rounded-full bg-paper-line/60">
                <div className="h-3 rounded-full" style={{ width: `${value}%`, background: l.color, opacity }} />
              </div>
              <span className="w-14 shrink-0 text-right text-xs text-slate">{pct(value)}</span>
            </div>
          ))}
        </li>
      ))}
    </ul>
  );
}

export default function BotsPage() {
  const { brand } = useBrand();
  const bots = useFetch(brand ? `/api/brands/${brand}/bot-filtering` : null);

  if (!brand) return <Loading />;
  const d = bots.data;
  const s = d?.overall_stats;

  return (
    <>
      <PageHeader
        eyebrow="Bot filtering"
        title={`${brand}: how much was bots`}
        description="Accounts that behave like bots are set aside before sentiment is counted. The difference between the two lines below is what bots would have done to your numbers."
      />

      <AiSummary brand={brand} focus="bots" />

      {bots.error && <ErrorNote message={bots.error} />}
      {bots.loading && <Loading>Loading bot filtering…</Loading>}

      {d && (
        <div className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-3">
            <Stat value={pct(d.removed_pct)} label="Of this brand's posts set aside" />
            <Stat value={num(d.removed_posts)} label="Posts set aside" hint={`of ${num(d.before.total)}`} />
            <Stat value={`${s.flagged_accounts} / ${s.total_accounts}`} label="Accounts flagged, all brands" />
          </div>

          <Panel label="Sentiment before and after filtering">
            <Compare before={d.before} after={d.after} />
          </Panel>

          <Panel label="Weekly negative share, with and without bots">
            <LineChart
              rows={d.weekly_negative}
              series={[
                { key: "before_negative_pct", label: "Before filtering", color: "var(--color-neu)", dash: "6 4" },
                { key: "after_negative_pct", label: "After filtering", color: "var(--color-neg)" },
              ]}
              flagKey="__none"
              label={`Weekly negative share for ${brand}, before and after bot filtering`}
            />
            <p className="mt-3 text-xs text-slate">A wide gap means bot posts are hiding or exaggerating the real mood.</p>
          </Panel>

          {s.post_precision != null && (
            <Panel label="Accuracy check">
              <p className="text-sm leading-relaxed text-slate">
                On this labelled demo data the filter caught {pct(s.post_recall * 100, 0)} of bot posts and {pct(s.post_precision * 100, 0)} of what it removed really was bot activity. The demo
                bots are deliberately easy to spot, so treat these as best-case figures, not what to expect on real social media.
              </p>
            </Panel>
          )}
        </div>
      )}
    </>
  );
}
