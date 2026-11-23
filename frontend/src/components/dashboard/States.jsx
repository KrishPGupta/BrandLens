import Panel from "./Panel";

export function Loading({ children = "Loading…" }) {
  return (
    <p className="text-sm text-slate py-6" role="status">
      {children}
    </p>
  );
}

export function ErrorNote({ message }) {
  return (
    <Panel>
      <p className="text-sm text-ink-950">{message}</p>
    </Panel>
  );
}

export function PageHeader({ eyebrow, title, description, children }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="eyebrow text-brass-deep mb-2">{eyebrow}</p>
        <h1 className="font-display text-3xl text-ink-950">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-slate leading-relaxed">{description}</p>}
      </div>
      {children}
    </header>
  );
}

export function Stat({ value, label, hint }) {
  return (
    <Panel>
      <p className="font-display text-3xl text-ink-950 leading-none">{value}</p>
      <p className="mt-2 text-sm text-slate">{label}</p>
      {hint && <p className="mt-1 text-xs text-slate/80">{hint}</p>}
    </Panel>
  );
}
