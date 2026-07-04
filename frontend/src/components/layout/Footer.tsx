// ============================================================
// Footer.tsx — bottom of every page. Importantly, it repeats the
// "not a diagnostic tool" disclaimer. Keeping this visible on
// every page is both ethically right and smart for a science
// project: it shows judges you understand the limits of the tool.
// ============================================================

export default function Footer() {
  return (
    <footer className="border-t border-line bg-white">
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
              <span className="font-display font-bold text-ink">ACL MotionCheck</span>
            </div>
            <p className="mt-3 text-sm text-muted">
              Movement analysis for jump landings, built to support ACL injury-prevention
              education.
            </p>
          </div>

          {/* Simple link columns */}
          <div className="flex gap-12 text-sm">
            <div className="flex flex-col gap-2">
              <span className="font-medium text-ink">Product</span>
              <a href="/#how" className="text-muted hover:text-ink">How it works</a>
              <a href="/#features" className="text-muted hover:text-ink">Features</a>
              <a href="/analyze" className="text-muted hover:text-ink">Analyze a video</a>
            </div>
            <div className="flex flex-col gap-2">
              <span className="font-medium text-ink">Project</span>
              <a href="/#about" className="text-muted hover:text-ink">About</a>
              <a href="/history" className="text-muted hover:text-ink">History</a>
            </div>
          </div>
        </div>

        {/* The disclaimer — kept prominent on purpose. */}
        <div className="mt-8 rounded-lg bg-surface p-4">
          <p className="text-xs leading-relaxed text-muted">
            <span className="font-semibold text-ink">Not a medical device.</span>{" "}
            ACL MotionCheck does not diagnose ACL injuries or any medical condition. It
            measures movement mechanics that injury-prevention research associates with
            risk, for educational and screening-support purposes only. Always consult a
            qualified medical professional for health decisions.
          </p>
        </div>

        <p className="mt-6 text-xs text-muted">
          © {new Date().getFullYear()} ACL MotionCheck. Built for ISEF &amp; the
          Congressional App Challenge.
        </p>
      </div>
    </footer>
  );
}
