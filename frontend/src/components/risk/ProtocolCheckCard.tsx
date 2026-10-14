// ============================================================
// ProtocolCheckCard.tsx — shows whether the real LESS box-jump protocol
// setup (12in/31cm box, land at half the athlete's height — Padua et al.
// 2009) was actually followed, MEASURED from the athlete's own body in
// the video rather than trusted from a tape measure. See
// backend/app/cv/calibration.py for the method.
//
// NOT a score — this is context for how much to trust the LESS card
// below it, which is why it renders directly above LessScoreCard on the
// report page.
// ============================================================

import { ProtocolCheck } from "@/lib/types";

const STANDARD_BOX_HEIGHT_CM = 31; // 12in

function cmToFeetInches(cm: number): string {
  const totalInches = cm / 2.54;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round(totalInches % 12);
  return `${feet} ft ${inches} in`;
}

export default function ProtocolCheckCard({
  protocolCheck,
}: {
  protocolCheck: ProtocolCheck | null;
}) {
  if (!protocolCheck) {
    return null;
  }

  const { boxHeightCm, landingDistanceCm, landingDistanceTargetCm, landingDistanceDeltaCm, confident, note } =
    protocolCheck;
  const hasNumbers = boxHeightCm !== null || landingDistanceCm !== null;

  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
            Box-jump protocol check
          </h2>
          <p className="text-[11px] text-muted">Estimated from your video, not self-reported</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            confident ? "bg-track-soft text-track" : "bg-watch-soft text-watch"
          }`}
        >
          {confident ? "Estimate" : "Uncertain"}
        </span>
      </div>

      {hasNumbers ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-surface px-3 py-2">
            <div className="font-mono text-[10px] uppercase tracking-wide text-muted">
              Box height
            </div>
            <div className="font-mono text-lg font-bold text-ink">
              {boxHeightCm !== null ? `${boxHeightCm.toFixed(1)} cm` : "Not measured"}
            </div>
            {boxHeightCm !== null && (
              <div className="mt-0.5 text-[11px] text-muted">
                Standard is {STANDARD_BOX_HEIGHT_CM} cm ({cmToFeetInches(STANDARD_BOX_HEIGHT_CM)})
              </div>
            )}
          </div>

          <div className="rounded-lg bg-surface px-3 py-2">
            <div className="font-mono text-[10px] uppercase tracking-wide text-muted">
              Landing distance
            </div>
            <div className="font-mono text-lg font-bold text-ink">
              {landingDistanceCm !== null ? `${landingDistanceCm.toFixed(1)} cm` : "Not measured"}
            </div>
            {landingDistanceCm !== null && landingDistanceTargetCm !== null && (
              <div className="mt-0.5 text-[11px] text-muted">
                Target {landingDistanceTargetCm.toFixed(1)} cm (half of height)
                {landingDistanceDeltaCm !== null && (
                  <>
                    {" "}
                    &middot; {landingDistanceDeltaCm >= 0 ? "+" : ""}
                    {landingDistanceDeltaCm.toFixed(1)} cm from target
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted">
          Box height and landing distance couldn&apos;t be measured for this clip.
        </p>
      )}

      {note && <p className="mt-3 text-xs leading-relaxed text-muted">{note}</p>}
    </div>
  );
}
