import { Link, NavLink, Outlet } from "react-router-dom";
import { BrandProvider, useBrand } from "../../context/BrandContext";
import { SITE } from "../../config/site";
import { useFetch } from "../../lib/api";
import Logo from "../layout/Logo";

const NAV = [
  { to: "/dashboard", label: "Overview", end: true },
  { to: "/dashboard/trends", label: "Trends and drift" },
  { to: "/dashboard/bots", label: "Bot filtering" },
  { to: "/dashboard/explanations", label: "Explanations" },
  { to: "/dashboard/models", label: "Models" },
];

function Sidebar() {
  const { brands, brand, setBrand } = useBrand();
  const health = useFetch("/api/health");
  const live = Boolean(health.data);

  return (
    <aside className="flex flex-col gap-6 bg-ink-950 px-5 py-6 text-paper md:sticky md:top-0 md:h-screen">
      <Link to="/" className="flex items-center gap-3">
        <Logo className="h-10 w-10" />
        <span className="font-display text-xl">{SITE.name}</span>
      </Link>

      <div>
        <label htmlFor="brand" className="mb-2 block text-xs font-semibold uppercase tracking-[0.12em] text-paper/60">
          Brand
        </label>
        <select
          id="brand"
          value={brand ?? ""}
          onChange={(e) => setBrand(e.target.value)}
          className="w-full rounded-md border border-paper/20 bg-ink-900 px-3 py-2 text-sm text-paper"
        >
          {brands.length === 0 && <option value="">Loading…</option>}
          {brands.map((b) => (
            <option key={b} value={b}>
              {b}
            </option>
          ))}
        </select>
      </div>

      <nav aria-label="Dashboard" className="-mx-1 flex gap-1 overflow-x-auto md:flex-col md:overflow-visible">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "bg-ink-900 text-brass-dim" : "text-paper/75 hover:bg-ink-900 hover:text-paper"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3 border-t border-paper/10 pt-4 text-xs text-paper/70">
        <p className="flex items-center gap-2">
          <span className={`h-2 w-2 rounded-full ${live ? "bg-emerald-400" : "bg-brass-dim"}`} aria-hidden="true" />
          {live ? "API connected" : health.loading ? "Checking API…" : "API not reachable"}
        </p>
        <p>Demo data, generated for this project.</p>
        <Link to="/" className="inline-block text-paper/80 underline underline-offset-4 decoration-paper/30 hover:text-paper">
          Back to the website
        </Link>
      </div>
    </aside>
  );
}

export default function DashboardLayout() {
  return (
    <BrandProvider>
      <div className="min-h-screen md:grid md:grid-cols-[240px_1fr]">
        <Sidebar />
        <main className="mx-auto w-full max-w-5xl px-6 py-10 md:px-10">
          <Outlet />
        </main>
      </div>
    </BrandProvider>
  );
}
