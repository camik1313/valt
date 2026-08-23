// ============================================================
// compare/page.tsx — placeholder for comparing two landing attempts
// side by side (see project plan: ranking engine + Compare).
//
// By design this will NOT be long-term progress tracking or an account
// system — the plan is two analyses, compared once, using session/local
// storage or a downloadable JSON result rather than a persistent server
// history. Placeholder rather than a fabricated comparison in the
// meantime.
// ============================================================

import Button from "@/components/ui/Button";

export default function ComparePage() {
  return (
    <section className="mx-auto max-w-2xl px-6 py-20 text-center">
      <span className="font-mono text-xs uppercase tracking-widest text-track">
        Compare
      </span>
      <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
        See what changed between two landings
      </h1>
      <p className="mt-5 leading-relaxed text-muted">
        Analyze two attempts, then see them side by side: knee flexion,
        symmetry, frontal knee control, and trunk control, attempt one versus
        attempt two, with a plain-language summary of what improved. No
        account, no long-term dashboard, just two scans compared once.
      </p>
      <p className="mt-4 text-sm text-muted">
        This isn&apos;t built yet. Run a scan now, and this page will be able
        to compare it against a second one once it&apos;s live.
      </p>
      <div className="mt-8">
        <Button href="/capture" variant="primary">
          Analyze my landing →
        </Button>
      </div>
    </section>
  );
}
