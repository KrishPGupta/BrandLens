import { SITE, FALLBACK_SUMMARY, FALLBACK_ALERT } from "../../config/site";
import { useApi } from "../../lib/api";

const nf = new Intl.NumberFormat("en-IN");

function formatWeek(iso) {
  const d = new Date(`${iso}T00:00:00`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

const signed = (n) => `${n > 0 ? "+" : "\u2212"}${Math.abs(n).toFixed(1)}`;

export default function About() {
  const { data: summary } = useApi("/api/summary", FALLBACK_SUMMARY, (d) => ({
    posts: d.posts,
    bot_pct: d.bot_pct,
  }));
  const { data: alert } = useApi("/api/alerts?brand=Nova", FALLBACK_ALERT, (d) => d.alerts?.[0]);

  return (
    <section id="about" className="scroll-mt-20 mx-auto max-w-6xl px-6 py-20 md:py-28">
      <div className="grid md:grid-cols-2 gap-12 items-start">
        <div>
          <p className="eyebrow text-brass mb-4">About {SITE.name}</p>

          <h2 className="font-display text-3xl md:text-4xl text-ink-950 leading-tight">
            Spot the week sentiment turns,
            <br />
            and see what drove it.
          </h2>

          <div className="flex gap-16 mt-16">
            <div>
              <p className="font-display text-3xl text-ink-950">{nf.format(summary.posts)}</p>
              <p className="text-sm text-slate mt-1">Posts analysed</p>
            </div>
            <div>
              <p className="font-display text-3xl text-ink-950">
                {Number(summary.bot_pct).toFixed(1)}%
              </p>
              <p className="text-sm text-slate mt-1">Set aside as bot activity</p>
            </div>
          </div>
          <p className="mt-4 text-xs text-slate">Demo dataset, generated for this project.</p>
        </div>

        <div className="space-y-6">
          <p className="text-slate leading-relaxed">
            Raw sentiment can mislead. A burst of automated posts can make a
            struggling brand look loved, and a quiet shift in tone is easy to
            miss in a daily feed. {SITE.name} filters out suspected bots first,
            then compares each week with the weeks before it and flags the ones
            that need a human look.
          </p>

          <div className="pt-4 border-t border-paper-line">
            <div className="rounded-xl bg-ink-950 text-paper p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-display text-lg">
                    {alert.brand}: week of {formatWeek(alert.week)}
                  </p>
                  <p className="text-sm text-brass-dim mt-1">{alert.driver}</p>
                </div>
                <span className="rounded-full bg-brass text-ink-950 text-xs font-semibold px-3 py-1 whitespace-nowrap">
                  Needs review
                </span>
              </div>

              <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <dt className="text-paper/60">Negative posts</dt>
                  <dd className="font-display text-2xl mt-1">
                    {Number(alert.negative).toFixed(1)}%
                  </dd>
                  <dd className="text-paper/60 text-xs mt-1">Z-score {signed(alert.z_negative)}</dd>
                </div>
                <div>
                  <dt className="text-paper/60">Positive posts</dt>
                  <dd className="font-display text-2xl mt-1">
                    {Number(alert.positive).toFixed(1)}%
                  </dd>
                  <dd className="text-paper/60 text-xs mt-1">Z-score {signed(alert.z_positive)}</dd>
                </div>
              </dl>
            </div>
            <p className="mt-3 text-xs text-slate">
              An example alert from the demo data. Alerts are prompts to look,
              not verdicts.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
