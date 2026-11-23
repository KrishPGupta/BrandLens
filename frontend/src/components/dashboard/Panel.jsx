export default function Panel({ label, children, className = "", ...rest }) {
  return (
    <section className={`panel ${className}`} {...rest}>
      {label && <h2 className="panel-label">{label}</h2>}
      {children}
    </section>
  );
}
