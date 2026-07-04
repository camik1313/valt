// ============================================================
// About.tsx — the mission, and (crucially) an honest statement
// of what the tool is and isn't. For a science project, being
// clear about scope and limitations is a strength, not a weakness.
// ============================================================

export default function About() {
  return (
    <section id="about" className="border-t border-line bg-white">
      <div className="mx-auto max-w-6xl px-6 py-20">
        <div className="grid gap-12 md:grid-cols-2 md:items-start">
          {/* Mission */}
          <div>
            <span className="font-mono text-xs uppercase tracking-widest text-track">
              About the project
            </span>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
              Injury-prevention screening, made accessible
            </h2>
            <p className="mt-5 leading-relaxed text-muted">
              ACL tears are among the most common and serious injuries in youth and
              amateur sport, and they often follow identifiable movement patterns during
              landing. The tools that measure those patterns usually live in
              biomechanics labs with expensive motion-capture systems.
            </p>
            <p className="mt-4 leading-relaxed text-muted">
              ACL MotionCheck brings a version of that analysis to any smartphone, so
              coaches, athletes, and trainers can start a conversation about movement
              quality — and know when to seek a professional assessment.
            </p>
          </div>

          {/* Scope / honesty panel */}
          <div className="rounded-2xl border border-risk/30 bg-risk-soft/40 p-8">
            <h3 className="font-display text-lg font-semibold text-ink">
              What this tool is — and isn't
            </h3>
            <ul className="mt-4 space-y-4 text-sm leading-relaxed text-ink/80">
              <li className="flex gap-3">
                <span className="mt-1 font-mono text-track">is</span>
                <span>
                  A screening-support tool that <strong>measures</strong> movement
                  mechanics linked to ACL risk in published research.
                </span>
              </li>
              <li className="flex gap-3">
                <span className="mt-1 font-mono text-track">is</span>
                <span>An educational way to visualize and track landing quality over time.</span>
              </li>
              <li className="flex gap-3">
                <span className="mt-1 font-mono text-risk">not</span>
                <span>
                  A diagnostic device. It does <strong>not</strong> diagnose ACL injuries
                  or any medical condition.
                </span>
              </li>
              <li className="flex gap-3">
                <span className="mt-1 font-mono text-risk">not</span>
                <span>A replacement for evaluation by a qualified medical professional.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
