// ============================================================
// ReportedFactorsCard.tsx — displays the self-reported epidemiological
// risk factors on the report page. This is DIFFERENT from LessScoreCard
// (the real, measured 17-item LESS assessment) and from the Metric cards
// / Landing Profile (the measured biomechanics): this card covers general
// risk-factor context from the questionnaire only — prior injury, sex,
// sport, age, activity level, fatigue.
//
// CRITICAL FRAMING (see backend/app/risk/reported_factors.py for the full
// version): this is a plain list of literature-cited factors, not a
// score. There is no points total, no weighting, and no band — an
// earlier version of this app combined these with illustrative
// biomechanical thresholds into a single weighted number; that composite
// was removed because the weights weren't defensible. Each factor below
// is shown on its own with its own citation, not summed into anything.
// ============================================================

import { ReportedFactor } from "@/lib/types";

export default function ReportedFactorsCard({ factors }: { factors: ReportedFactor[] }) {
  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
        Self-reported risk factors
      </h2>

      <p className="mt-3 rounded-lg bg-surface p-3 text-xs leading-relaxed text-muted">
        <span className="font-semibold text-ink">Not a score, not a diagnosis.</span>{" "}
        These are individual factors the questionnaire matched to published research on
        ACL injury epidemiology — listed separately, with their own citations, not
        combined into a single number. They reflect population-level patterns, not a
        prediction for this athlete.
      </p>

      {factors.length > 0 ? (
        <ul className="mt-5 space-y-3">
          {factors.map((f) => (
            <li key={f.key} className="rounded-lg bg-surface p-3 text-sm text-ink">
              <span className="font-medium">{f.label}</span>
              <p className="mt-1 text-xs leading-relaxed text-muted">{f.detail}</p>
              <p className="mt-1 text-xs leading-relaxed text-muted">{f.citation}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-5 text-sm text-muted">
          No self-reported factors matched a literature-associated category, or no
          questionnaire was completed for this analysis.
        </p>
      )}
    </div>
  );
}
