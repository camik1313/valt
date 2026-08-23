// ============================================================
// Footer.tsx — bottom of every page. Importantly, it repeats the
// "not a diagnostic tool" disclaimer. Keeping this visible on
// every page is both ethically right and smart for a science
// project: it shows judges you understand the limits of the tool.
// ============================================================

export default function Footer() {
  return (
    <footer className="border-t border-line bg-white">
      {/* A thin hairline in the brand accent — a small, quiet signature touch. */}
      <div aria-hidden="true" className="h-[3px] w-full bg-track" />
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          {/* Brand + one-line description */}
          <div className="max-w-sm">
            <div className="flex items-center gap-2">
              <svg width="22" height="22" viewBox="0 0 26 26" aria-hidden="true">
                <line x1="7" y1="7" x2="19" y2="19" stroke="#0E7C86" strokeWidth="2" />
                <circle cx="7" cy="7" r="4" fill="#132033" />
                <circle cx="19" cy="19" r="4" fill="#0E7C86" />
              </svg>
              <span className="font-display font-bold text-ink">VALT</span>
            </div>
            <p className="mt-3 text-sm text-muted">
              Movement analysis built for female athletes, making ACL
              injury-prevention research accessible from a smartphone.
            </p>
          </div>

          {/* Simple link columns */}
          <div className="flex gap-12 text-sm">
            <div className="flex flex-col gap-2">
              <span className="font-medium text-ink">Product</span>
              <a href="/capture" className="text-muted hover:text-ink">Analyze</a>
              <a href="/exercises" className="text-muted hover:text-ink">Exercises</a>
              <a href="/compare" className="text-muted hover:text-ink">Compare</a>
            </div>
            <div className="flex flex-col gap-2">
              <span className="font-medium text-ink">Learn</span>
              <a href="/why" className="text-muted hover:text-ink">HER ACL</a>
              <a href="/#about" className="text-muted hover:text-ink">About</a>
            </div>
          </div>
        </div>

        {/* The disclaimer — kept prominent on purpose. */}
        <div className="mt-8 rounded-lg bg-surface p-4">
          <p className="text-xs leading-relaxed text-muted">
            <span className="font-semibold text-ink">Not a medical device.</span>{" "}
            VALT does not diagnose ACL injuries or any medical condition. It
            measures movement mechanics that injury-prevention research associates with
            risk, for educational and screening-support purposes only. Always consult a
            qualified medical professional for health decisions.
          </p>
        </div>

      </div>
    </footer>
  );
}
