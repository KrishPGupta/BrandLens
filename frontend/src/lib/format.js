export function fmtWeek(iso, withYear = false) {
  const d = new Date(`${String(iso).slice(0, 10)}T00:00:00`);
  if (Number.isNaN(d.getTime())) return String(iso);
  return d.toLocaleDateString("en-GB", withYear ? { day: "numeric", month: "short", year: "numeric" } : { day: "numeric", month: "short" });
}

export const num = (n) => new Intl.NumberFormat("en-IN").format(n ?? 0);
export const pct = (n, digits = 1) => (n == null ? "\u2013" : `${Number(n).toFixed(digits)}%`);
export const signed = (n, digits = 1) => (n == null ? "\u2013" : `${n >= 0 ? "+" : "\u2212"}${Math.abs(n).toFixed(digits)}`);
