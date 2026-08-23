// ============================================================
// LandingProfileCard.tsx — the simple, four-category summary shown
// BEFORE the technical metric grid and 17-item LESS breakdown, per the
// "don't overwhelm with raw numbers first" product requirement. See
// backend/app/reports/landing_profile.py.
//
// Shares its rating vocabulary (ok/watch/flag) with Metric.status and
// the risk/LESS cards — one banding system across the whole report, not
// a second one with different words for the same thing.
// ============================================================

import { LandingProfile, LandingProfileCategory } from "@/lib/types";

const RATING_STYLES: Record<LandingProfileCategory["rating"], { badge: string; text: string; label: string }> = {
  ok:          { badge: "bg-track-soft", text: "text-track",     label: "Good" },
  watch:       { badge: "bg-amber-100",  text: "text-amber-700", label: "Borderline" },
  flag:        { badge: "bg-risk-soft",  text: "text-risk",      label: "Notable" },
  unavailable: { badge: "bg-surface",    text: "text-muted",     label: "Not measured" },
};

export default function LandingProfileCard({ profile }: { profile: LandingProfile | null }) {
  if (!profile) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
        Your landing profile
      </h2>
      <p className="mt-1 text-[11px] text-muted">
        A quick summary. See the full measurements and LESS breakdown below.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {profile.categories.map((c) => {
          const style = RATING_STYLES[c.rating];
          return (
            <div key={c.category} className="rounded-xl bg-surface p-4">
              <div className="flex items-start justify-between gap-2">
                <span className="font-display text-sm font-semibold text-ink">{c.label}</span>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold ${style.badge} ${style.text}`}>
                  {style.label}
                </span>
              </div>
              {c.value !== null && (
                <p className="mt-1 font-mono text-lg font-bold text-ink">
                  {c.value.toFixed(1)}
                  <span className="ml-1 text-xs font-normal text-muted">{c.unit}</span>
                </p>
              )}
              <p className="mt-1 text-xs leading-relaxed text-muted">{c.explanation}</p>
              {c.sourceView && (
                <p className="mt-1 text-[10px] uppercase tracking-wide text-muted">
                  Source: {c.sourceView} view
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
