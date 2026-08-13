// ============================================================
// Features.tsx — two groups:
//   1) The biomechanical MEASUREMENTS the tool computes.
//   2) The product FEATURES (reports, history, exports).
// Copy is specific and plain — no vague marketing filler.
// ============================================================

import Card from "@/components/ui/Card";
import { BlobBadge } from "@/components/decor/Doodles";

// The scientific measurements. Each maps to real literature. `hue` is
// purely a categorical accent (which measurement is which at a glance) —
// it never means "risk" the way the report page's ok/watch/flag colors do.
const metrics = [
  {
    title: "Knee flexion",
    body: "Angle of the knee at landing. Stiff, low-flexion landings are associated with higher joint loading.",
    hue: "bloom" as const,
  },
  {
    title: "Dynamic knee valgus",
    body: "Inward collapse of the knee relative to hip and ankle. One of the most-studied ACL-risk patterns.",
    hue: "iris" as const,
  },
  {
    title: "Trunk lean",
    body: "Forward and lateral tilt of the torso, which shifts load and affects knee control on landing.",
    hue: "sprout" as const,
  },
  {
    title: "Left / right asymmetry",
    body: "Differences between limbs. Large asymmetries can indicate compensation or reduced control on one side.",
    hue: "track" as const,
  },
  {
    title: "Hip position",
    body: "Hip flexion and drop at landing, part of how force is absorbed up the kinetic chain.",
    hue: "bloom" as const,
  },
];

// Product-level features.
const product = [
  { title: "Clear reports", body: "Plain-language summaries with graphs, exportable to PDF and CSV." },
  { title: "Multiple athletes", body: "Organize analyses by athlete and revisit them over time." },
  { title: "Saved history", body: "Every analysis is stored so you can compare sessions and track change." },
];

// Hex for the little crosshair icon inside each BlobBadge — kept in sync
// with the badge's own hue.
const ICON_HEX: Record<string, string> = {
  bloom: "#EC5A94",
  iris: "#8B6BF2",
  sprout: "#2FBD7E",
  track: "#0E7C86",
};

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
              <BlobBadge color={m.hue} className="mb-3 h-9 w-9">
                {/* small target/crosshair icon, tinted to match the badge */}
                <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
                  <circle cx="9" cy="9" r="7" fill="none" stroke={ICON_HEX[m.hue]} strokeWidth="1.5" />
                  <circle cx="9" cy="9" r="2" fill={ICON_HEX[m.hue]} />
                </svg>
              </BlobBadge>
              <h3 className="font-display text-lg font-semibold text-ink">{m.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{m.body}</p>
            </Card>
          ))}
        </div>

        {/* The product feature strip */}
        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {product.map((p) => (
            <div
              key={p.title}
              className="rounded-xl bg-gradient-to-br from-ink to-ink/80 p-6 text-surface relative overflow-hidden"
            >
              {/* a faint corner glow — subtle, doesn't fight the text */}
              <div
                aria-hidden="true"
                className="pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full bg-iris opacity-20 blur-2xl"
              />
              <h3 className="relative font-display text-lg font-semibold">{p.title}</h3>
              <p className="relative mt-2 text-sm leading-relaxed text-surface/70">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
