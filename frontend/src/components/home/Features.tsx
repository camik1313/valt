// ============================================================
// Features.tsx — two groups:
//   1) The biomechanical MEASUREMENTS the tool computes.
//   2) The product FEATURES (reports, history, exports).
// Copy is specific and plain — no vague marketing filler.
// ============================================================

import Card from "@/components/ui/Card";

// The scientific measurements. Each maps to real literature.
const metrics = [
  {
    title: "Knee flexion",
    body: "Angle of the knee at landing. Stiff, low-flexion landings are associated with higher joint loading.",
  },
  {
    title: "Dynamic knee valgus",
    body: "Inward collapse of the knee relative to hip and ankle — one of the most-studied ACL-risk patterns.",
  },
  {
    title: "Trunk lean",
    body: "Forward and lateral tilt of the torso, which shifts load and affects knee control on landing.",
  },
  {
    title: "Left / right asymmetry",
    body: "Differences between limbs. Large asymmetries can indicate compensation or reduced control on one side.",
  },
  {
    title: "Hip position",
    body: "Hip flexion and drop at landing, part of how force is absorbed up the kinetic chain.",
  },
];

// Product-level features.
const product = [
  { title: "Clear reports", body: "Plain-language summaries with graphs, exportable to PDF and CSV." },
  { title: "Multiple athletes", body: "Organize analyses by athlete and revisit them over time." },
  { title: "Saved history", body: "Every analysis is stored so you can compare sessions and track change." },
];

export default function Features() {
  return (
    <section id="features" className="border-t border-line">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            What it measures
          </span>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
            Five movement measurements, one landing
          </h2>
          <p className="mt-4 text-muted">
            Each measurement is drawn from ACL injury-prevention research. Together they
            describe how an athlete absorbs a landing.
          </p>
        </div>

        {/* The measurement cards */}
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((m) => (
            <Card key={m.title}>
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-track-soft">
                {/* small target/crosshair icon */}
                <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                  <circle cx="9" cy="9" r="7" fill="none" stroke="#0E7C86" strokeWidth="1.5" />
                  <circle cx="9" cy="9" r="2" fill="#0E7C86" />
                </svg>
              </div>
              <h3 className="font-display text-lg font-semibold text-ink">{m.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{m.body}</p>
            </Card>
          ))}
        </div>

        {/* The product feature strip */}
        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {product.map((p) => (
            <div key={p.title} className="rounded-xl bg-ink p-6 text-surface">
              <h3 className="font-display text-lg font-semibold">{p.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-surface/70">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
