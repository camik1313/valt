// ============================================================
// compare/page.tsx — compare two landings, side by side, once.
//
// Deliberately NOT long-term tracking: no account, no dashboard, no
// history of comparisons. Two analyses, picked by the athlete (from
// their own recent history, or a pasted id), diffed once. Whatever
// session/local memory exists is just a convenience default (the
// "compare with your last attempt" prefill from capture/page.tsx),
// not a tracked record — see sessionStorage's `valt:lastAnalysisId`.
//
// The diff is entirely CLIENT-SIDE: both analyses are fetched with the
// existing GET /report/{id} (no new backend endpoint needed), and their
// already-computed `landingProfile` categories (backend/app/reports/
// landing_profile.py) are compared directly. No new server-side
// comparison logic to duplicate what single-analysis scoring already did.
// ============================================================
"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Analysis, LandingProfileCategory } from "@/lib/types";
import { getHistory, getReport, HistoryItem } from "@/lib/api";
import Button from "@/components/ui/Button";

const RATING_RANK: Record<LandingProfileCategory["rating"], number> = {
  flag: 0,
  watch: 1,
  ok: 2,
  unavailable: -1,
};

const RATING_LABEL: Record<LandingProfileCategory["rating"], string> = {
  ok: "Good",
  watch: "Borderline",
  flag: "Notable",
  unavailable: "Not measured",
};

const RATING_TEXT_CLASS: Record<LandingProfileCategory["rating"], string> = {
  ok: "text-track",
  watch: "text-amber-700",
  flag: "text-risk",
  unavailable: "text-muted",
};

export default function ComparePage() {
  const searchParams = useSearchParams();

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [idA, setIdA] = useState<string>(searchParams.get("a") ?? "");
  const [idB, setIdB] = useState<string>(searchParams.get("b") ?? "");
  const [analysisA, setAnalysisA] = useState<Analysis | null>(null);
  const [analysisB, setAnalysisB] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Load recent history for the pickers, and default attempt 1 to the
  // last analysis this session recorded, if nothing was passed in the URL.
  useEffect(() => {
    getHistory().then(setHistory).catch(() => setHistory([]));
    if (!searchParams.get("a")) {
      try {
        const last = sessionStorage.getItem("valt:lastAnalysisId");
        if (last) setIdA(last);
      } catch {
        /* sessionStorage unavailable — no default, not fatal */
      }
    }
  }, [searchParams]);

  // Fetch both analyses once both ids are chosen.
  useEffect(() => {
    if (!idA || !idB) {
      setAnalysisA(null);
      setAnalysisB(null);
      return;
    }
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([getReport(idA), getReport(idB)])
      .then(([a, b]) => {
        if (!active) return;
        setAnalysisA(a);
        setAnalysisB(b);
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Could not load one of these landings.");
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [idA, idB]);

  const comparison = useMemo(() => {
    if (!analysisA?.landingProfile || !analysisB?.landingProfile) return null;
    const byCategory = new Map(analysisB.landingProfile.categories.map((c) => [c.category, c]));
    const rows = analysisA.landingProfile.categories
      .map((catA) => {
        const catB = byCategory.get(catA.category);
        if (!catB) return null;
        return { category: catA.category, label: catA.label, a: catA, b: catB };
      })
      .filter((r): r is { category: string; label: string; a: LandingProfileCategory; b: LandingProfileCategory } => r !== null);

    const comparable = rows.filter((r) => RATING_RANK[r.a.rating] >= 0 && RATING_RANK[r.b.rating] >= 0);
    const improved = comparable.filter((r) => RATING_RANK[r.b.rating] > RATING_RANK[r.a.rating]).length;
    const worsened = comparable.filter((r) => RATING_RANK[r.b.rating] < RATING_RANK[r.a.rating]).length;

    return { rows, comparableCount: comparable.length, improved, worsened };
  }, [analysisA, analysisB]);

  return (
    <section className="mx-auto max-w-4xl px-6 py-16">
      <div className="mb-8 text-center">
        <span className="font-mono text-xs uppercase tracking-widest text-track">Compare</span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
          See what changed between two landings
        </h1>
        <p className="mx-auto mt-3 max-w-xl text-muted">
          Pick two of your recorded landings to compare, side by side, once. No account,
          no ongoing tracking, just two scans and what changed.
        </p>
      </div>

      {/* Pickers */}
      <div className="grid gap-4 sm:grid-cols-2">
        <AttemptPicker label="Attempt 1" value={idA} onChange={setIdA} history={history} />
        <AttemptPicker label="Attempt 2" value={idB} onChange={setIdB} history={history} />
      </div>

      {(!idA || !idB) && (
        <p className="mt-6 text-center text-sm text-muted">
          Choose two landings above to compare them.
        </p>
      )}

      {loading && (
        <div className="mt-10 text-center">
          <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-track border-t-transparent" />
        </div>
      )}

      {error && !loading && (
        <div className="mt-8 rounded-xl border border-risk/30 bg-risk-soft/40 p-6 text-center text-sm text-muted">
          {error}
        </div>
      )}

      {analysisA && analysisB && !comparison && !loading && !error && (
        <div className="mt-10 rounded-2xl border border-line bg-white p-6 text-center text-sm text-muted">
          One or both of these landings don&apos;t have measured results to compare (a
          simulated or placeholder result can&apos;t be compared against a real one).
        </div>
      )}

      {comparison && analysisA && analysisB && !loading && !error && (
        <div className="mt-10">
          {/* What changed */}
          <div className="rounded-2xl border border-line bg-white p-6 text-center">
            <span className="font-mono text-xs uppercase tracking-widest text-muted">What changed?</span>
            <p className="mt-2 font-display text-lg font-semibold text-ink">
              {comparison.comparableCount === 0
                ? "These two landings don't share enough measured categories to compare."
                : `Attempt 2 showed improvement in ${comparison.improved} of ${comparison.comparableCount} measured movement categories.`}
            </p>
            {comparison.worsened > 0 && (
              <p className="mt-1 text-sm text-muted">
                {comparison.worsened} of {comparison.comparableCount} moved the other direction.
              </p>
            )}
          </div>

          {/* Table */}
          <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-white">
            <table className="w-full min-w-[480px] text-sm">
              <thead>
                <tr className="border-b border-line text-left">
                  <th className="p-4 font-display font-semibold text-ink">Category</th>
                  <th className="p-4 font-display font-semibold text-ink">
                    Attempt 1
                    <span className="block text-[11px] font-normal text-muted">{analysisA.athleteName}</span>
                  </th>
                  <th className="p-4 font-display font-semibold text-ink">
                    Attempt 2
                    <span className="block text-[11px] font-normal text-muted">{analysisB.athleteName}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {comparison.rows.map((row) => (
                  <tr key={row.category} className="border-b border-line last:border-0">
                    <td className="p-4 font-medium text-ink">{row.label}</td>
                    <RatingCell category={row.a} />
                    <RatingCell category={row.b} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-6 rounded-lg bg-surface p-4 text-xs leading-relaxed text-muted">
            This compares movement-quality categories between two recorded attempts. It is
            not a measure of ACL injury risk and does not estimate how that risk changed.
          </p>
        </div>
      )}

      <div className="mt-8 flex justify-center gap-3">
        <Button href="/capture" variant="primary">Record another landing</Button>
        <Button href="/history" variant="outline">Browse history</Button>
      </div>
    </section>
  );
}

function RatingCell({ category }: { category: LandingProfileCategory }) {
  return (
    <td className="p-4">
      <span className={`font-semibold ${RATING_TEXT_CLASS[category.rating]}`}>
        {RATING_LABEL[category.rating]}
      </span>
      {category.value !== null && (
        <span className="ml-2 font-mono text-xs text-muted">
          {category.value.toFixed(1)} {category.unit}
        </span>
      )}
    </td>
  );
}

function AttemptPicker({
  label,
  value,
  onChange,
  history,
}: {
  label: string;
  value: string;
  onChange: (id: string) => void;
  history: HistoryItem[];
}) {
  return (
    <label className="block text-sm font-medium text-ink">
      {label}
      <select
        className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2 font-body text-sm text-ink focus:border-track focus:outline-none focus:ring-2 focus:ring-track/30"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">Choose a landing…</option>
        {history.map((item) => (
          <option key={item.id} value={item.id}>
            {item.athleteName} — {new Date(item.createdAt).toLocaleDateString()}
          </option>
        ))}
      </select>
    </label>
  );
}
