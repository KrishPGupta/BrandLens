import { FEATURES, IMAGES } from "../../config/site";

export default function Features() {
  return (
    <section id="features" className="scroll-mt-20 relative bg-paper-dim overflow-hidden">
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url('${IMAGES.features}')` }}
      />
      <div className="absolute inset-0 bg-paper-dim/85" />

      <div className="relative mx-auto max-w-6xl px-6 py-20 md:py-28">
        <h2 className="font-display text-3xl md:text-4xl text-ink-950 max-w-xl mb-14">
          Three checks before a trend is called a trend.
        </h2>

        <div className="grid md:grid-cols-3 gap-6">
          {FEATURES.map((feature, i) => (
            <div
              key={feature.title}
              className={`p-8 rounded-lg ${
                i === 1 ? "bg-ink-950 text-paper" : "bg-paper text-ink-950"
              }`}
            >
              <h3 className="font-display text-xl mb-3">{feature.title}</h3>
              <p
                className={`text-sm leading-relaxed ${
                  i === 1 ? "text-paper/70" : "text-slate"
                }`}
              >
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
