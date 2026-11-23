import { useEffect, useRef, useState } from "react";
import { STAGES } from "../../config/site";

const SLIDE_MS = 4500;

function Chevron({ flip }) {
  return (
    <svg viewBox="0 0 20 20" className={`h-4 w-4 ${flip ? "rotate-180" : ""}`} fill="none" aria-hidden="true">
      <path d="M7 4l6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function Pipeline() {
  const trackRef = useRef(null);
  const [hovering, setHovering] = useState(false);
  const [userPaused, setUserPaused] = useState(false);
  const paused = hovering || userPaused;

  const step = (dir) => {
    const el = trackRef.current;
    if (!el) return;
    const card = el.querySelector("li");
    const width = card ? card.getBoundingClientRect().width + 24 : el.clientWidth;
    const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 4;
    if (dir > 0 && atEnd) el.scrollTo({ left: 0, behavior: "smooth" });
    else if (dir < 0 && el.scrollLeft <= 4) el.scrollTo({ left: el.scrollWidth, behavior: "smooth" });
    else el.scrollBy({ left: dir * width, behavior: "smooth" });
  };

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (paused || reduce) return undefined;
    const id = setInterval(() => {
      if (!document.hidden) step(1);
    }, SLIDE_MS);
    return () => clearInterval(id);
  }, [paused]);

  const btn =
    "grid h-10 w-10 place-items-center rounded-full border border-ink-900/20 text-ink-900 hover:bg-ink-900 hover:text-paper transition-colors";

  return (
    <section
      id="how-it-works"
      className="scroll-mt-20 mx-auto max-w-6xl px-6 py-20 md:py-28"
      onMouseEnter={() => setHovering(true)}
      onMouseLeave={() => setHovering(false)}
      onFocus={() => setHovering(true)}
      onBlur={() => setHovering(false)}
    >
      <div className="flex flex-wrap items-end justify-between gap-6 mb-14">
        <h2 className="font-display text-3xl md:text-4xl text-ink-950 max-w-xl">
          From raw posts to a flagged week in six steps.
        </h2>
        <div className="flex items-center gap-3">
          <button type="button" className={btn} onClick={() => step(-1)} aria-label="Previous step">
            <Chevron flip />
          </button>
          <button type="button" className={btn} onClick={() => step(1)} aria-label="Next step">
            <Chevron />
          </button>
          <button
            type="button"
            onClick={() => setUserPaused((p) => !p)}
            className="text-sm font-medium text-ink-700 underline underline-offset-4 decoration-ink-900/30 hover:text-ink-950"
          >
            {userPaused ? "Play slideshow" : "Pause slideshow"}
          </button>
        </div>
      </div>

      <ul ref={trackRef} className="no-scrollbar flex gap-6 overflow-x-auto snap-x snap-mandatory scroll-smooth">
        {STAGES.map((stage, i) => (
          <li
            key={stage.title}
            className="snap-start shrink-0 basis-full sm:basis-[calc(50%-12px)] md:basis-[calc(33.333%-16px)]"
          >
            <div className="p-8 rounded-lg border border-paper-line bg-paper-dim/60 h-full flex flex-col">
              <span className="font-display text-3xl text-brass mb-4">{i + 1}</span>
              <h3 className="font-display text-xl text-ink-950 mb-3">{stage.title}</h3>
              <p className="text-sm text-slate leading-relaxed">{stage.description}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
