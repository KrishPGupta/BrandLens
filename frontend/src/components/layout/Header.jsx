import { Link, useLocation } from "react-router-dom";
import { SITE } from "../../config/site";
import Logo from "./Logo";

export default function Header() {
  const location = useLocation();
  const isDashboard = location.pathname === "/dashboard";

  return (
    <header className="sticky top-0 z-40 bg-paper/90 backdrop-blur border-b border-ink-900/10">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 text-ink-950">
          <Logo className="h-11 w-11" />
          <span className="font-display text-xl leading-tight">{SITE.name}</span>
        </Link>

        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-ink-700">
          <a href="/#about" className="hover:text-ink-950 transition-colors">About</a>
          <a href="/#features" className="hover:text-ink-950 transition-colors">Features</a>
          <a href="/#how-it-works" className="hover:text-ink-950 transition-colors">How it works</a>
          <a href="/#contact" className="hover:text-ink-950 transition-colors">Contact</a>
        </nav>

        <Link
          to="/dashboard"
          aria-current={isDashboard ? "page" : undefined}
          className="rounded-full bg-ink-900 text-paper px-5 py-2.5 text-sm font-semibold hover:bg-ink-700 transition-colors"
        >
          Open dashboard
        </Link>
      </div>
    </header>
  );
}
