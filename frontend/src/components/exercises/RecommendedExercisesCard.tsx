// ============================================================
// RecommendedExercisesCard.tsx — the personalized "what to work on"
// section of the report page. See backend/app/exercises/priorities.py
// (what's flagged) and ranking.py (what's recommended for it, and why).
//
// THREE DISTINCT STATES, never conflated:
//   1. recommendations === null: no questionnaire to rank against
//      (shouldn't happen via guided capture, where it's required).
//   2. gatedReason !== null: the athlete reported current pain or
//      injury, so recommendations were deliberately withheld — this is
//      a safety choice, not a missing-data state, and reads that way.
//   3. Computed: real priorities and ranked exercises, or an honest
//      "nothing was flagged" empty state if the landing looked clean.
// ============================================================

import { ExerciseRecommendations, RecommendedExercise } from "@/lib/types";

// Purely decorative scanning aid — exercise cards are encouraging,
// actionable content, not clinical data, unlike the report's score cards.
const DIFFICULTY_EMOJI: Record<RecommendedExercise["difficulty"], string> = {
  beginner: "🌱",
  intermediate: "🔥",
  advanced: "⚡",
};

export default function RecommendedExercisesCard({
  recommendations,
}: {
  recommendations: ExerciseRecommendations | null;
}) {
  if (!recommendations) {
    return (
      <div className="rounded-2xl border border-line bg-white p-6">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          Recommended for you
        </h2>
        <p className="mt-2 text-sm text-muted">
          No exercise recommendations are available for this analysis.
        </p>
      </div>
    );
  }

  if (recommendations.gatedReason) {
    return (
      <div className="rounded-2xl border border-line bg-white p-6">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          Recommended for you
        </h2>
        <p className="mt-3 rounded-lg bg-risk-soft/40 p-4 text-sm leading-relaxed text-ink">
          {recommendations.gatedReason}
        </p>
      </div>
    );
  }

  const [topPriority, ...otherPriorities] = recommendations.priorities;

  return (
    <div className="rounded-2xl border border-line bg-white p-6">
      <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
        Recommended for you
      </h2>
      <p className="mt-1 text-[11px] text-muted">
        Matched to this scan&apos;s flagged movement patterns, from a
        research-backed exercise library.
      </p>

      {recommendations.priorities.length === 0 ? (
        <p className="mt-4 text-sm text-muted">
          This landing didn&apos;t flag any specific movement priorities, so
          there&apos;s nothing targeted to recommend here. Nice landing! 🎉
        </p>
      ) : (
        <>
          {/* YOUR TOP FOCUS + other areas */}
          <div className="mt-5 space-y-3">
            <div>
              <span className="font-mono text-[10px] uppercase tracking-widest text-track">
                Your top focus
              </span>
              <p className="mt-1 font-display text-lg font-semibold text-ink">
                {topPriority.targetLabel}
              </p>
              {topPriority.evidence[0] && (
                <p className="mt-1 text-xs text-muted">{topPriority.evidence[0]}</p>
              )}
            </div>
            {otherPriorities.length > 0 && (
              <div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
                  Other areas to work on
                </span>
                <ul className="mt-1 flex flex-wrap gap-2">
                  {otherPriorities.map((p) => (
                    <li
                      key={p.target}
                      className="rounded-full bg-surface px-3 py-1 text-xs text-ink"
                    >
                      {p.targetLabel}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Ranked exercises */}
          {recommendations.exercises.length > 0 ? (
            <div className="mt-6 space-y-4">
              {recommendations.exercises.map((exercise) => (
                <ExerciseCard key={exercise.exerciseId} exercise={exercise} />
              ))}
            </div>
          ) : (
            <p className="mt-6 text-sm text-muted">
              No exercises in the library currently match this athlete&apos;s
              age range for the flagged priorities above.
            </p>
          )}
        </>
      )}

      <p className="mt-6 rounded-lg bg-surface p-3 text-[11px] leading-relaxed text-muted">
        {recommendations.disclaimer}
      </p>
    </div>
  );
}

function ExerciseCard({ exercise }: { exercise: RecommendedExercise }) {
  return (
    <div className="rounded-xl border border-line p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-base font-semibold text-ink">
          {exercise.exerciseName}
        </h3>
        <span className="shrink-0 rounded-full bg-track-soft px-2 py-0.5 text-[11px] font-medium text-track">
          <span aria-hidden="true">{DIFFICULTY_EMOJI[exercise.difficulty]}</span> {exercise.difficulty}
        </span>
      </div>
      <p className="mt-1 text-sm text-muted">{exercise.shortDescription}</p>

      <div className="mt-3 rounded-lg bg-surface p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
          Why this was recommended
        </p>
        <p className="mt-1 text-xs leading-relaxed text-ink">{exercise.why}</p>
      </div>

      <details className="mt-3 text-sm">
        <summary className="cursor-pointer font-medium text-track">
          How to perform it
        </summary>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-xs leading-relaxed text-muted">
          {exercise.instructions.map((step, i) => (
            <li key={i}>{step}</li>
          ))}
        </ol>
      </details>

      <p className="mt-3 text-xs text-muted">
        <span className="font-medium text-ink">Equipment:</span> {exercise.equipment}
      </p>
      <p className="mt-1 text-xs text-muted">{exercise.safetyNotes}</p>
      <p className="mt-2 text-[11px] italic text-muted">
        Source: {exercise.sourceProgram}
      </p>
    </div>
  );
}
