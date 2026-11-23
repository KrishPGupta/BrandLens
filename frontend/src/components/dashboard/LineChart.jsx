import { useState } from "react";
import { fmtWeek } from "../../lib/format";

const W = 760;
const H = 280;
const M = { t: 14, r: 18, b: 32, l: 46 };

function pathFor(rows, key, x, y) {
  let d = "";
  let pen = false;
  rows.forEach((r, i) => {
    const v = r[key];
    if (v == null || Number.isNaN(v)) {
      pen = false;
      return;
    }
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)} `;
    pen = true;
  });
  return d.trim();
}

/** Line chart drawn in SVG. Flagged weeks get a brass band; hover (or touch) shows the values. */
export default function LineChart({
  rows,
  series,
  yMin = 0,
  yMax = 100,
  hlines = [],
  flagKey = "flag",
  xKey = "week",
  suffix = "%",
  digits = 1,
  label,
}) {
  const [hover, setHover] = useState(null);
  const n = rows.length;
  if (!n) return <p className="text-sm text-slate">No data yet.</p>;

  const iw = W - M.l - M.r;
  const ih = H - M.t - M.b;
  const x = (i) => M.l + (n === 1 ? iw / 2 : (i / (n - 1)) * iw);
  const y = (v) => M.t + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const band = n > 1 ? iw / (n - 1) : 20;
  const ticks = Array.from({ length: 5 }, (_, k) => yMin + (k * (yMax - yMin)) / 4);
  const step = Math.max(1, Math.ceil(n / 7));
  const hasFlags = rows.some((r) => r[flagKey]);

  const onMove = (e) => {
    const box = e.currentTarget.ownerSVGElement.getBoundingClientRect();
    const px = ((e.clientX - box.left) / box.width) * W;
    const i = Math.round(((px - M.l) / iw) * (n - 1));
    setHover(Math.min(n - 1, Math.max(0, i)));
  };

  const hr = hover == null ? null : rows[hover];
  const hx = hover == null ? 0 : x(hover) / W;

  return (
    <div>
      <ul className="mb-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate">
        {series.map((s) => (
          <li key={s.key} className="flex items-center gap-2">
            <svg width="22" height="8" aria-hidden="true">
              <line x1="0" y1="4" x2="22" y2="4" stroke={s.color} strokeWidth="2.5" strokeDasharray={s.dash || undefined} />
            </svg>
            {s.label}
          </li>
        ))}
        {hasFlags && (
          <li className="flex items-center gap-2">
            <span className="inline-block h-3 w-3 rounded-sm bg-brass/30" aria-hidden="true" />
            Flagged for review
          </li>
        )}
      </ul>

      <div className="relative">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" role="img" aria-label={label}>
          {ticks.map((t) => (
            <g key={t}>
              <line x1={M.l} x2={W - M.r} y1={y(t)} y2={y(t)} stroke="var(--color-paper-line)" strokeWidth="1" />
              <text x={M.l - 8} y={y(t) + 4} textAnchor="end" fontSize="11" fill="var(--color-slate)">
                {Number.isInteger(t) ? t : t.toFixed(1)}
                {suffix}
              </text>
            </g>
          ))}

          {rows.map((r, i) =>
            r[flagKey] ? (
              <rect key={`f${i}`} x={x(i) - band / 2} y={M.t} width={band} height={ih} fill="var(--color-brass)" opacity="0.18" />
            ) : null
          )}

          {hlines.map((h) => (
            <line key={h.y} x1={M.l} x2={W - M.r} y1={y(h.y)} y2={y(h.y)} stroke="var(--color-ink-700)" strokeWidth="1" strokeDasharray="5 4" opacity="0.6" />
          ))}

          {series.map((s) => (
            <path key={s.key} d={pathFor(rows, s.key, x, y)} fill="none" stroke={s.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" strokeDasharray={s.dash || undefined} />
          ))}

          {rows.map((r, i) =>
            i % step === 0 || i === n - 1 ? (
              <text key={`x${i}`} x={x(i)} y={H - 10} textAnchor="middle" fontSize="11" fill="var(--color-slate)">
                {fmtWeek(r[xKey])}
              </text>
            ) : null
          )}

          {hover != null && (
            <g pointerEvents="none">
              <line x1={x(hover)} x2={x(hover)} y1={M.t} y2={M.t + ih} stroke="var(--color-ink-900)" strokeWidth="1" opacity="0.4" />
              {series.map((s) =>
                hr[s.key] == null ? null : <circle key={s.key} cx={x(hover)} cy={y(hr[s.key])} r="4" fill={s.color} stroke="var(--color-card)" strokeWidth="2" />
              )}
            </g>
          )}

          <rect x={M.l} y={M.t} width={iw} height={ih} fill="transparent" onPointerMove={onMove} onPointerDown={onMove} onPointerLeave={() => setHover(null)} />
        </svg>

        {hr && (
          <div
            className="pointer-events-none absolute top-0 z-10 w-44 rounded-md bg-ink-950 px-3 py-2 text-xs text-paper shadow-lg"
            style={{ left: `${hx * 100}%`, transform: hx > 0.7 ? "translateX(-105%)" : "translateX(8%)" }}
          >
            <p className="mb-1 font-semibold">{fmtWeek(hr[xKey], true)}</p>
            {series.map((s) => (
              <p key={s.key} className="flex justify-between gap-3">
                <span className="text-paper/70">{s.label}</span>
                <span>{hr[s.key] == null ? "\u2013" : `${Number(hr[s.key]).toFixed(digits)}${suffix}`}</span>
              </p>
            ))}
            {hr[flagKey] && <p className="mt-1 text-brass-dim">Flagged for review</p>}
          </div>
        )}
      </div>
    </div>
  );
}
