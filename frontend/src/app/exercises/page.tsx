// ============================================================
// exercises/page.tsx — the browsable exercise library.
//
// NOT personalized — this lists the full research-backed library from
// GET /exercises (backend/app/exercises/database.py) with simple
// client-side filters. Personalized, ranked recommendations tied to a
// specific scan live on the report page instead (see
// RecommendedExercisesCard.tsx) — this page exists so someone can
// browse the library on its own, before or without ever running a scan.
// ============================================================
"use client";

import { useEffect, useMemo, useState } from "react";
import { ExerciseInfo } from "@/lib/types";
import { getExercises } from "@/lib/api";
import Button from "@/components/ui/Button";

// The same small vocabulary the backend ranks against (see
// backend/app/exercises/database.py's MovementTarget) — kept in sync by
// hand since it's a fixed, short list, not generated data.
const TARGET_FILTERS: { value: string; label: string }[] = [
  { value: "landing_control", label: "Landing control" },
  { value: "frontal_knee_control", label: "Knee control" },
  { value: "knee_flexion", label: "Landing depth" },
  { value: "trunk_control", label: "Trunk control" },
  { value: "symmetry", label: "Symmetry" },
  { value: "hip_strength", label: "Strength" },
  { value: "hamstring_strength", label: "Strength" },
  { value: "calf_ankle_strength", label: "Strength" },
  { value: "core_stability", label: "Strength" },
  { value: "balance", label: "Balance" },
  { value: "deceleration", label: "Neuromuscular control" },
];
// Collapse duplicates (several targets share a display label above).
const TARGET_FILTER_OPTIONS = Array.from(
  new Map(TARGET_FILTERS.map((t) => [t.label, t])).values()
);

const DIFFICULTIES: ExerciseInfo["difficulty"][] = ["beginner", "intermediate", "advanced"];

export default function ExercisesPage() {
  const [exercises, setExercises] = useState<ExerciseInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [targetFilter, setTargetFilter] = useState<string | null>(null);
  const [difficultyFilter, setDifficultyFilter] = useState<ExerciseInfo["difficulty"] | null>(null);
  const [noEquipmentOnly, setNoEquipmentOnly] = useState(false);

  useEffect(() => {
    let active = true;
    getExercises()
      .then((data) => {
        if (active) {
          setExercises(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Could not load the exercise library.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const matchingTargets = useMemo(() => {
    if (!targetFilter) return null;
    return new Set(TARGET_FILTERS.filter((t) => t.label === targetFilter).map((t) => t.value));
  }, [targetFilter]);

  const filtered = exercises.filter((e) => {
    if (matchingTargets && !e.movementTargets.some((t) => matchingTargets.has(t))) return false;
    if (difficultyFilter && e.difficulty !== difficultyFilter) return false;
    if (noEquipmentOnly && !e.equipment.toLowerCase().startsWith("none")) return false;
    return true;
  });

  return (
    <section className="mx-auto max-w-5xl px-6 py-16">
      <div className="mb-8 text-center">
        <span className="font-mono text-xs uppercase tracking-widest text-track">Exercises</span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
          The research-backed exercise library
        </h1>
        <p className="mx-auto mt-3 max-w-2xl text-muted">
          Every exercise here is drawn from a real, cited injury-prevention program, FIFA
          11+ and the PEP Program, not invented. Run a scan to see which of these are
          matched to your own landing.
        </p>
        <div className="mt-5">
          <Button href="/capture" variant="primary">Analyze my landing →</Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-center gap-2 border-y border-line py-4">
        <FilterChip active={targetFilter === null} onClick={() => setTargetFilter(null)}>
          All
        </FilterChip>
        {TARGET_FILTER_OPTIONS.map((t) => (
          <FilterChip key={t.label} active={targetFilter === t.label} onClick={() => setTargetFilter(t.label)}>
            {t.label}
          </FilterChip>
        ))}
        <span className="mx-1 h-4 w-px bg-line" aria-hidden="true" />
        {DIFFICULTIES.map((d) => (
          <FilterChip
            key={d}
            active={difficultyFilter === d}
            onClick={() => setDifficultyFilter(difficultyFilter === d ? null : d)}
          >
            {d}
          </FilterChip>
        ))}
        <span className="mx-1 h-4 w-px bg-line" aria-hidden="true" />
        <FilterChip active={noEquipmentOnly} onClick={() => setNoEquipmentOnly(!noEquipmentOnly)}>
          No equipment
        </FilterChip>
      </div>

      {/* Loading / error */}
      {loading && (
        <div className="py-16 text-center">
          <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-track border-t-transparent" />
        </div>
      )}
      {error && !loading && (
        <div className="mt-8 rounded-xl border border-risk/30 bg-risk-soft/40 p-6 text-center text-sm text-muted">
          {error}
        </div>
      )}

      {/* Grid */}
      {!loading && !error && (
        <>
          <p className="mt-6 text-xs text-muted">
            {filtered.length} of {exercises.length} exercises
          </p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map((e) => (
              <ExerciseLibraryCard key={e.exerciseId} exercise={e} />
            ))}
          </div>
          {filtered.length === 0 && (
            <p className="mt-8 text-center text-sm text-muted">
              No exercises match these filters.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-full border px-3 py-1 text-xs capitalize transition-all",
        active ? "border-track bg-track-soft text-track" : "border-line bg-white text-muted hover:border-track/50",
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function ExerciseLibraryCard({ exercise }: { exercise: ExerciseInfo }) {
  return (
    <div className="rounded-xl border border-line bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-base font-semibold text-ink">{exercise.exerciseName}</h3>
        <span className="shrink-0 rounded-full bg-track-soft px-2 py-0.5 text-[11px] font-medium capitalize text-track">
          {exercise.difficulty}
        </span>
      </div>
      <p className="mt-1 text-sm text-muted">{exercise.shortDescription}</p>
      <details className="mt-3 text-sm">
        <summary className="cursor-pointer font-medium text-track">How to perform it</summary>
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
      <p className="mt-2 text-[11px] italic text-muted">Source: {exercise.sourceProgram}</p>
    </div>
  );
}
