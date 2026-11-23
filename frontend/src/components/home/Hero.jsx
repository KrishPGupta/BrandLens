import { Link } from "react-router-dom";
import { SITE, IMAGES } from "../../config/site";

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-ink-950 text-paper min-h-[calc(100svh-77px)] flex items-center">
      <img
        src={IMAGES.hero}
        alt=""
        className="absolute inset-0 block h-full w-full object-cover object-[70%_center]"
      />
      <div className="absolute inset-0 bg-gradient-to-r from-ink-950/95 via-ink-950/65 to-ink-950/20" />
      <div className="absolute inset-0 bg-gradient-to-t from-ink-950/40 via-transparent to-ink-950/10" />

      <div className="relative z-10 px-6 md:pl-16 lg:pl-24 py-20 w-full">
        <p className="eyebrow text-brass-dim mb-6">{SITE.tagline}</p>
        <h1 className="font-display text-4xl md:text-6xl leading-[1.08] max-w-xl">
          Know the week opinion about your brand changes.
        </h1>
        <p className="mt-6 text-paper/75 max-w-lg text-lg">
          {SITE.name} reads social media posts, sets bot activity aside, and
          flags the weeks where sentiment shifts, with the words behind every
          flag so you can see why.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link
            to="/dashboard"
            className="rounded-full bg-brass text-ink-950 px-7 py-3.5 font-semibold hover:bg-brass-dim transition-colors"
          >
            Open dashboard
          </Link>
          <a
            href="#how-it-works"
            className="text-paper/80 hover:text-paper text-sm font-medium underline underline-offset-4 decoration-paper/30"
          >
            See how it works
          </a>
        </div>
      </div>
    </section>
  );
}
