export default function Logo({ className = "h-10 w-10" }) {
  return (
    <svg viewBox="0 0 48 48" fill="none" className={className} aria-hidden="true">
      <circle cx="22" cy="22" r="12" stroke="currentColor" strokeWidth="3.5" />
      <path
        d="M15 26l5-5 4 3 6-7"
        stroke="var(--color-brass)"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M31.5 31.5L40 40" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" />
    </svg>
  );
}
