// ============================================================
// RiskScoreCard.tsx — displays the epidemiological SCREENING risk score
// on the report page. This is DIFFERENT from LessScoreCard.tsx: this one
// covers general risk-factor context (prior injury, sex, sport, age,
// activity level, fatigue) plus a small illustrative biomechanical check
// — it is NOT the LESS assessment (see LessScoreCard.tsx / risk/less.py
// for the real, cited 17-item tool).
//
// CRITICAL FRAMING (see backend/app/risk/scoring.py for the full version):
// this is a transparent, literature-informed screening checklist, not a
// diagnosis, NOT a trained model, and NEVER an injury probability. That
// framing is repeated here deliberately rather than assumed — this is
// the component someone will screenshot.
// ============================================================

import { PartialScore, RiskScore } from "@/lib/types";

const BAND_STYLES: Record<RiskScore["band"], { badge: string; text: string; label: string; bar: string }> = {
  low:      { badge: "bg-track-soft", text: "text-track",     label: "Low",      bar: "bg-track" },
  moderate: { badge: "bg-amber-100",  text: "text-amber-700", label: "Moderate", bar: "bg-amber-500" },
  elevated: { badge: "bg-risk-soft",  text: "text-risk",      label: "Elevated", bar: "bg-risk" },
};

export default function RiskScoreCard({ riskScore }: { riskScore: RiskScore | null }) {
  if (!riskScore) {
    return (
      <div className="rounded-2xl border border-line bg-white p-6">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          Risk factor screening
        </h2>
        <p className="mt-2 text-sm text-muted">
          No screening score is available for this analysis. It requires real
          measurements from the video, and this result used simulated
          placeholder data instead.
        </p>
      </div>
    );
  }

  const band = BAND_STYLES[riskScore.band];

  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <div className="flex items-start justify-between gap-3">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          Risk factor screening
        </h2>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${band.badge} ${band.text}`}>
          {band.label}
        </span>
      </div>

      {/* CRITICAL FRAMING — always shown, never collapsed or truncated. */}
      <p className="mt-3 rounded-lg bg-surface p-3 text-xs leading-relaxed text-muted">
        <span className="font-semibold text-ink">Not a diagnosis, not a prediction.</span>{" "}
        {riskScore.disclaimer}
      </p>

      {/* Percent-of-achievable-points bar. Explicitly labeled as a score,
          never phrased as a probability or likelihood of injury. */}
      <div className="mt-5">
        <div className="flex items-baseline justify-between text-xs text-muted">
          <span>Screening score</span>
          <span className="font-mono">
            {riskScore.totalPoints.toFixed(1)} / {riskScore.totalMaxPoints.toFixed(1)} pts (
            {riskScore.percentOfMax.toFixed(0)}% of achievable)
          </span>
        </div>
        <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-line">
          <div
            className={`h-full rounded-full ${band.bar}`}
            style={{ width: `${Math.min(100, Math.max(0, riskScore.percentOfMax))}%` }}
          />
        </div>
      </div>

      {/* Two subtotals, kept visually separate since they come from very
          different sources (measured video vs. self-report). */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <PartialScoreSummary title="From this video" score={riskScore.biomechanical} />
        {riskScore.questionnaire ? (
          <PartialScoreSummary title="From questionnaire" score={riskScore.questionnaire} />
        ) : (
          <div className="rounded-lg border border-dashed border-line p-3">
            <p className="text-xs font-medium text-ink">From questionnaire</p>
            <p className="mt-1 text-xs text-muted">
              Not completed. Score reflects the biomechanical portion only.
            </p>
          </div>
        )}
      </div>

      {/* Contributing factors, plain language. */}
      {riskScore.factors.length > 0 ? (
        <div className="mt-5">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
            Contributing factors
          </h3>
          <ul className="mt-2 space-y-2">
            {riskScore.factors.map((f) => (
              <li key={f.key} className="rounded-lg bg-surface p-3 text-sm text-ink">
                <div className="flex items-start justify-between gap-3">
                  <span className="font-medium">{f.label}</span>
                  <span className="shrink-0 font-mono text-xs text-muted">+{f.points.toFixed(1)} pts</span>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-muted">{f.detail}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-5 text-sm text-muted">
          No screening criteria were triggered, so there are no factors to list.
        </p>
      )}
    </div>
  );
}

function PartialScoreSummary({ title, score }: { title: string; score: PartialScore }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <p className="text-xs font-medium text-ink">{title}</p>
      <p className="mt-1 font-mono text-sm text-ink">
        {score.points.toFixed(1)} / {score.maxPoints.toFixed(1)} pts
      </p>
    </div>
  );
}
