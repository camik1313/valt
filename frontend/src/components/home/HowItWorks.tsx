// ============================================================
// HowItWorks.tsx — a 4-step sequence. Numbered markers are used
// here BECAUSE the content genuinely is an ordered pipeline:
// each step feeds the next. (Numbering decorative content is a
// design smell; numbering a real sequence is correct.)
// ============================================================

const steps = [
  {
    n: "01",
    title: "Record & upload",
    body: "Film a jump landing from the front on any smartphone. Upload the clip — no special equipment or sensors required.",
  },
  {
    n: "02",
    title: "Track landmarks",
    body: "Pose estimation locates 33 body landmarks in every frame, following joints through the full landing motion.",
  },
  {
    n: "03",
    title: "Measure at landing",
    body: "The software finds the landing frame and computes knee flexion, dynamic valgus, trunk lean, hip position, and left/right asymmetry.",
  },
  {
    n: "04",
    title: "Read the report",
    body: "Get clear graphs and a plain-language summary of which measurements fall inside or outside research-informed ranges.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how" className="border-t border-line bg-white">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="max-w-2xl">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            The pipeline
          </span>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
            From a phone clip to a movement report
          </h2>
          <p className="mt-4 text-muted">
            Four steps, in order. Each one hands its result to the next.
          </p>
        </div>

        <div className="mt-14 grid gap-8 md:grid-cols-4">
          {steps.map((s, i) => (
            <div key={s.n} className="relative">
              {/* connecting line between steps (desktop only) */}
              {i < steps.length - 1 && (
                <div className="absolute left-12 top-5 hidden h-px w-full bg-line md:block" />
              )}
              <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-ink font-mono text-sm font-bold text-surface">
                {s.n}
              </div>
              <h3 className="mt-4 font-display text-lg font-semibold text-ink">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
