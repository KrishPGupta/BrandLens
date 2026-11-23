import { useState } from "react";
import { Link } from "react-router-dom";
import { useBrand } from "../../context/BrandContext";
import { useFetch } from "../../lib/api";
import { fmtWeek, num, pct } from "../../lib/format";
import AiSummary from "../../components/dashboard/AiSummary";
import Panel from "../../components/dashboard/Panel";
import { ErrorNote, Loading, PageHeader, Stat } from "../../components/dashboard/States";

const SEGMENTS = [
  { key: "negative", label: "Negative", color: "var(--color-neg)" },
  { key: "neutral", label: "Neutral", color: "var(--color-neu)" },
  { key: "positive", label: "Positive", color: "var(--color-pos)" },
];

export default function OverviewPage() {
  const { brand, offline } = useBrand();
  const [withBots, setWithBots] = useState(false);
  const overview = useFetch(brand ? `/api/brands/${brand}/overview?include_bots=${withBots}` : null);
  const trend = useFetch(brand ? `/api/brands/${brand}/trend` : null);
  const bots = useFetch(brand ? `/api/brands/${brand}/bot-filtering` : null);
  const alerts = useFetch(brand ? `/api/alerts?brand=${brand}` : null);

  if (offline) return <ErrorNote message="Cannot reach the API. Start it with: python -m uvicorn api.main:app --port 8000" />;
  if (!brand) return <Loading />;

  const err = overview.error || trend.error || bots.error || alerts.error;
  const ready = overview.data && trend.data && bots.data && alerts.data;
  const latest = trend.data?.weeks.at(-1);
  const recent = alerts.data ? [...alerts.data.alerts].reverse().slice(0, 5) : [];

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title={`${brand} at a glance`}
        description="What people are saying, how much of it comes from bots, and whether sentiment has moved away from normal."
      />

      <AiSummary brand={brand} focus="overview" />

      {err && <ErrorNote message={err} />}
      {!ready && !err && <Loading>Loading the numbers…</Loading>}

      {ready && (
        <>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <Stat value={num(overview.data.total)} label={withBots ? "Posts, bots included" : "Posts analysed"} hint="Bots excluded unless you switch them on" />
            <Stat value={pct(bots.data.removed_pct)} label="Set aside as bot activity" />
            <Stat value={overview.data.weeks_flagged} label="Weeks flagged for review" hint={`of ${trend.data.weeks.length} weeks`} />
            <Stat value={latest?.flag ? "Needs review" : "Normal"} label={`Latest week (${fmtWeek(latest?.week, true)})`} />
          </div>

          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            <Panel label="Sentiment split">
              <div className="flex h-5 overflow-hidden rounded-full bg-paper-line" role="img" aria-label={SEGMENTS.map((s) => `${s.label} ${overview.data.pct[s.key]}%`).join(", ")}>
                {SEGMENTS.map((s) => (
                  <div key={s.key} style={{ width: `${overview.data.pct[s.key]}%`, background: s.color }} />
                ))}
              </div>
              <ul className="mt-5">
                {SEGMENTS.map((s) => (
                  <li key={s.key} className="list-row">
                    <span className="flex items-center gap-2 text-sm text-ink-950">
                      <span className="h-3 w-3 rounded-sm" style={{ background: s.color }} aria-hidden="true" />
                      {s.label}
                    </span>
                    <span className="text-sm text-slate">
                      {pct(overview.data.pct[s.key])} <span className="text-slate/70">({num(overview.data.counts[s.key])})</span>
                    </span>
                  </li>
                ))}
              </ul>
              <label className="mt-4 flex items-center gap-2 text-sm text-slate">
                <input type="checkbox" checked={withBots} onChange={(e) => setWithBots(e.target.checked)} />
                Include posts from suspected bots
              </label>
            </Panel>

            <Panel label="Recent alerts">
              {recent.length === 0 && <p className="text-sm text-slate">No weeks have been flagged for this brand.</p>}
              <ul>
                {recent.map((a) => (
                  <li key={a.week} className="list-row">
                    <div>
                      <p className="text-sm text-ink-950">Week of {fmtWeek(a.week, true)}</p>
                      <p className="text-xs text-slate">{a.driver}</p>
                    </div>
                    <span className="text-sm text-slate">
                      {pct(a.negative)} neg · {pct(a.positive)} pos
                    </span>
                  </li>
                ))}
              </ul>
              <Link to="/dashboard/trends" className="mt-4 inline-block text-sm font-medium text-brass-deep underline underline-offset-4">
                See the full trend
              </Link>
            </Panel>
          </div>
        </>
      )}
    </>
  );
}
