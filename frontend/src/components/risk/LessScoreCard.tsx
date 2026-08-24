// ============================================================
// LessScoreCard.tsx — displays the REAL Landing Error Scoring System
// (LESS) result on the report page. See backend/app/risk/less.py for
// the full citations and item-by-item sourcing.
//
// CRITICAL FRAMING, repeated here on purpose (this is the component
// someone will screenshot): a real LESS score is a validated CLINICAL
// SCREENING tool, not a diagnosis, not a trained model, and never a
// prediction that any individual will or won't be injured. The official
// protocol averages 3 jump trials; this app scores one. Three of the 17
// items are self-reported, not measured — see the item list below for
// which, and why.
// ============================================================

import { LessItemScore, LessScore } from "@/lib/types";

const BAND_STYLES: Record<LessScore["band"], { badge: string; text: string; label: string; bar: string }> = {
  low:      { badge: "bg-track-soft", text: "text-track",     label: "Low",      bar: "bg-track" },
  moderate: { badge: "bg-watch-soft", text: "text-watch",     label: "Moderate", bar: "bg-watch" },
  high:     { badge: "bg-risk-soft",  text: "text-risk",      label: "High",     bar: "bg-risk" },
};

const VIEW_GROUP_LABEL: Record<LessItemScore["view"], string> = {
  sagittal: "Sagittal plane (side view)",
  frontal: "Frontal plane (front view)",
  overall: "Overall",
};

export default function LessScoreCard({ lessScore }: { lessScore: LessScore | null }) {
  if (!lessScore) {
    return (
      <div className="rounded-2xl border border-line bg-white p-6">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          LESS score
        </h2>
        <p className="mt-2 text-sm text-muted">
          No LESS score is available for this analysis. It requires real
          measurements from the video, and this result used simulated
          placeholder data instead.
        </p>
      </div>
    );
  }

  const band = BAND_STYLES[lessScore.band];
  const hasItems = lessScore.items.length > 0;

  const groups: LessItemScore["view"][] = ["sagittal", "frontal", "overall"];

  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
            LESS score
          </h2>
          <p className="text-[11px] text-muted">Landing Error Scoring System</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${band.badge} ${band.text}`}>
          {band.label}
        </span>
      </div>

      {/* CRITICAL FRAMING — always shown, never collapsed or truncated. */}
      <p className="mt-3 rounded-lg bg-surface p-3 text-xs leading-relaxed text-muted">
        <span className="font-semibold text-ink">Not a diagnosis, not a prediction.</span>{" "}
        {lessScore.disclaimer}
      </p>

      {hasItems ? (
        <>
          {/* Score bar */}
          <div className="mt-5">
            <div className="flex items-baseline justify-between text-xs text-muted">
              <span>LESS score for this session</span>
              <span className="font-mono">
                {lessScore.totalPoints.toFixed(0)} / {lessScore.maxPoints.toFixed(0)} pts (
                {lessScore.percentOfMax.toFixed(0)}% of achievable)
              </span>
            </div>
            <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-line">
              <div
                className={`h-full rounded-full ${band.bar}`}
                style={{ width: `${Math.min(100, Math.max(0, lessScore.percentOfMax))}%` }}
              />
            </div>
            <p className="mt-2 text-[11px] leading-relaxed text-muted">
              Reference: a full-scale LESS score of 5 or higher has been used in
              published research as an illustrative cutoff for a higher-risk
              landing pattern.{" "}
              <span className="italic">{lessScore.cutoffCitation}</span>
            </p>
          </div>

          {/* Views available */}
          <p className="mt-4 text-xs text-muted">
            Views used: {lessScore.viewsAvailable.length > 0
              ? lessScore.viewsAvailable.join(" + ")
              : "none"}
            {lessScore.viewsAvailable.length < 2 && (
              <>. Record both a front and side clip in the same session for the full item set.</>
            )}
          </p>

          {/* All scored items, grouped by which plane/camera they came from */}
          <div className="mt-5 space-y-5">
            {groups.map((group) => {
              const items = lessScore.items.filter((i) => i.view === group);
              if (items.length === 0) return null;
              return (
                <div key={group}>
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
                    {VIEW_GROUP_LABEL[group]}
                  </h3>
                  <ul className="mt-2 space-y-2">
                    {items
                      .slice()
                      .sort((a, b) => a.number - b.number)
                      .map((item) => (
                        <LessItemRow key={item.number} item={item} />
                      ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <p className="mt-5 text-sm text-muted">
          No LESS items could be scored for this analysis.
        </p>
      )}
    </div>
  );
}

function LessItemRow({ item }: { item: LessItemScore }) {
  const flagged = item.points > 0;
  return (
    <li
      className={`rounded-lg p-3 text-sm text-ink ${flagged ? "bg-risk-soft/40" : "bg-surface"}`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="font-medium">
          #{item.number} {item.label}
        </span>
        <span className={`shrink-0 font-mono text-xs ${flagged ? "text-risk" : "text-muted"}`}>
          {item.points}/{item.maxPoints} pts
        </span>
      </div>
      <p className="mt-1 text-xs leading-relaxed text-muted">
        No-error criterion: &ldquo;{item.goodCriterion}&rdquo;. {item.detail}
        {item.source === "self_reported" && " (self-reported)"}
      </p>
    </li>
  );
}
