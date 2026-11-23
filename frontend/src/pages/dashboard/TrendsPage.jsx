import { useBrand } from "../../context/BrandContext";
import { useFetch } from "../../lib/api";
import { fmtWeek, pct, signed } from "../../lib/format";
import AiSummary from "../../components/dashboard/AiSummary";
import LineChart from "../../components/dashboard/LineChart";
import Panel from "../../components/dashboard/Panel";
import { ErrorNote, Loading, PageHeader } from "../../components/dashboard/States";

const SENTIMENT = [
  { key: "negative", label: "Negative", color: "var(--color-neg)" },
  { key: "neutral", label: "Neutral", color: "var(--color-neu)" },
  { key: "positive", label: "Positive", color: "var(--color-pos)" },
];

export default function TrendsPage() {
  const { brand } = useBrand();
  const trend = useFetch(brand ? `/api/brands/${brand}/trend` : null);
  const alerts = useFetch(brand ? `/api/alerts?brand=${brand}` : null);

  if (!brand) return <Loading />;
  const err = trend.error || alerts.error;
  const weeks = trend.data?.weeks ?? [];
  const zMax = Math.max(4, Math.ceil(Math.max(0, ...weeks.flatMap((w) => [Math.abs(w.z_negative ?? 0), Math.abs(w.z_positive ?? 0)]))) + 1);
  const first = alerts.data?.first_sustained_alert;

  return (
    <>
      <PageHeader
        eyebrow="Trends and drift"
        title={`${brand}: week by week`}
        description="Each week is compared with the weeks before it. When sentiment moves further than normal week-to-week variation, the week is flagged for a human to look at."
      />

      <AiSummary brand={brand} focus="drift" />

      {err && <ErrorNote message={err} />}
      {trend.loading && <Loading>Loading the trend…</Loading>}

      {trend.data && (
        <div className="space-y-6">
          <Panel label="Share of posts by sentiment">
            <LineChart rows={weeks} series={SENTIMENT} label={`Weekly sentiment shares for ${brand}`} />
            <p className="mt-3 text-xs text-slate">Bot-flagged posts are excluded. Shaded weeks were flagged for review.</p>
          </Panel>

          <Panel label="How far each week is from normal">
            <LineChart
              rows={weeks}
              series={[
                { key: "z_negative", label: "Negative (standard deviations)", color: "var(--color-neg)" },
                { key: "z_positive", label: "Positive (standard deviations)", color: "var(--color-pos)" },
              ]}
              yMin={-zMax}
              yMax={zMax}
              suffix=""
              hlines={[{ y: trend.data.z_threshold }, { y: -trend.data.z_threshold }]}
              label={`Distance from baseline for ${brand}`}
            />
            <p className="mt-3 text-xs text-slate">
              Each week is measured against the previous {trend.data.window_weeks} normal weeks. The dashed lines at ±{trend.data.z_threshold} are the flagging threshold.
              {first ? ` The first sustained alert (two flagged weeks in a row) began the week of ${fmtWeek(first, true)}.` : " No sustained alert (two flagged weeks in a row) has occurred."}
            </p>
          </Panel>

          <Panel label="Flagged weeks">
            {alerts.data?.alerts.length === 0 && <p className="text-sm text-slate">No weeks were flagged for this brand.</p>}
            {alerts.data?.alerts.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase tracking-wider text-slate">
                    <tr>
                      <th className="py-2 pr-4 font-semibold">Week of</th>
                      <th className="py-2 pr-4 font-semibold">What moved</th>
                      <th className="py-2 pr-4 font-semibold">Negative</th>
                      <th className="py-2 pr-4 font-semibold">Positive</th>
                    </tr>
                  </thead>
                  <tbody>
                    {alerts.data.alerts.map((a) => (
                      <tr key={a.week} className="border-t border-paper-line">
                        <td className="py-2 pr-4 text-ink-950">{fmtWeek(a.week, true)}</td>
                        <td className="py-2 pr-4 text-slate">{a.driver}</td>
                        <td className="py-2 pr-4 text-slate">
                          {pct(a.negative)} <span className="text-slate/70">({signed(a.z_negative)} SD)</span>
                        </td>
                        <td className="py-2 pr-4 text-slate">
                          {pct(a.positive)} <span className="text-slate/70">({signed(a.z_positive)} SD)</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}
