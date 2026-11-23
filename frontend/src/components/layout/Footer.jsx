import { Link } from "react-router-dom";
import { SITE, LINKS, API_URL } from "../../config/site";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer id="contact" className="bg-ink-950 text-paper">
      <div className="mx-auto max-w-6xl px-6 py-12 grid gap-10 md:grid-cols-3">
        <div>
          <div className="flex items-center gap-3 text-paper">
            <Logo className="h-11 w-11" />
            <span className="font-display text-xl">{SITE.name}</span>
          </div>
          <p className="mt-4 text-sm text-paper/70 max-w-xs">{SITE.tagline}.</p>
        </div>

        <div className="text-sm text-paper/80 space-y-2">
          <p className="font-display text-base text-brass-dim mb-3">Explore</p>
          <p><a href="/#about" className="hover:text-paper transition-colors">About</a></p>
          <p><a href="/#features" className="hover:text-paper transition-colors">Features</a></p>
          <p><a href="/#how-it-works" className="hover:text-paper transition-colors">How it works</a></p>
          <p><Link to="/dashboard" className="hover:text-paper transition-colors">Dashboard</Link></p>
        </div>

        <div className="text-sm text-paper/80 space-y-2">
          <p className="font-display text-base text-brass-dim mb-3">Project</p>
          <p>
            <a href={LINKS.github} target="_blank" rel="noopener noreferrer" className="hover:text-paper transition-colors">
              Source code on GitHub
            </a>
          </p>
          <p>
            <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer" className="hover:text-paper transition-colors">
              API documentation
            </a>
          </p>
          <p>
            <a href={LINKS.issues} target="_blank" rel="noopener noreferrer" className="hover:text-paper transition-colors">
              Report an issue or ask a question
            </a>
          </p>
        </div>
      </div>

      <div className="border-t border-paper/10">
        <div className="mx-auto max-w-6xl px-6 py-5 text-xs text-paper/50 flex flex-col sm:flex-row justify-between gap-2">
          <span>© {new Date().getFullYear()} {SITE.name}. A final-year B.Tech project.</span>
          <span>Photos by Ilgmyzin and Jay Openiano on Unsplash. Demo data is synthetic.</span>
        </div>
      </div>
    </footer>
  );
}
