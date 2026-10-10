// ============================================================
// report/[id]/page.tsx — the REAL report view.
//
// The [id] in the folder name is a "dynamic route": visiting
// /report/abc123 makes params.id === "abc123". We take that id,
// fetch the saved analysis from the backend, and render it.
//
// This is a client component because it fetches data in the browser
// (via lib/api.ts) and shows loading / error / loaded states.
// ============================================================
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Analysis } from "@/lib/types";
import { getReport } from "@/lib/api";
import MetricCard from "@/components/report/MetricCard";
import ReportChart from "@/components/report/ReportChart";
import ReportedFactorsCard from "@/components/risk/ReportedFactorsCard";
import LessScoreCard from "@/components/risk/LessScoreCard";
import ProtocolCheckCard from "@/components/risk/ProtocolCheckCard";
import RecommendedExercisesCard from "@/components/exercises/RecommendedExercisesCard";
import LandingProfileCard from "@/components/report/LandingProfileCard";
import Button from "@/components/ui/Button";

// The backend appends its pipeline diagnostics (frame numbers, detection
// rates, calibration caveats) to the summary after a "Technical notes:"
// paragraph. Worth keeping for anyone checking the work, but it shouldn't
// sit in the middle of the plain-language summary.
function splitSummary(text: string): { main: string; notes: string | null } {
  const marker = "\n\nTechnical notes: ";
  const at = text.indexOf(marker);
  if (at === -1) return { main: text, notes: null };
  return { main: text.slice(0, at), notes: text.slice(at + marker.length) };
}

export default function ReportPage({ params }: { params: { id: string } }) {
  // Three possible states while loading remote data.
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch the report once, when the page first loads.
  useEffect(() => {
    let active = true; // guard against setting state after unmount
    getReport(params.id)
      .then((data) => {
        if (active) {
          setAnalysis(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Could not load report.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [params.id]);

  // ---- Loading state ----
  if (loading) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-28 text-center">
        <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-track border-t-transparent" />
        <p className="mt-4 text-sm text-muted">Loading report…</p>
      </section>
    );
  }

  // ---- Error state ----
  if (error || !analysis) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-28 text-center">
        <h1 className="font-display text-2xl font-bold text-ink">Report not found</h1>
        <p className="mt-2 text-sm text-muted">{error ?? "That analysis doesn't exist."}</p>
        <div className="mt-6">
          <Button href="/capture" variant="primary">Analyze my landing</Button>
        </div>
      </section>
    );
  }

  // ---- Loaded: show the full report ----
  const created = new Date(analysis.createdAt).toLocaleString();
  const summary = splitSummary(analysis.summary);

  return (
    <section className="mx-auto max-w-4xl px-6 py-16">
      {/* Header */}
      <div className="mb-8">
        <Link href="/history" className="text-sm text-track hover:underline">
          ← All analyses
        </Link>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
          {analysis.athleteName}
        </h1>
        <p className="mt-1 font-mono text-xs text-muted">
          {created} · {analysis.videoFilename}
        </p>
      </div>

      {/* Plain-language summary */}
      <div className="rounded-2xl border border-line bg-white p-6">
        <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted">
          Summary
        </h2>
        <p className="mt-2 whitespace-pre-line leading-relaxed text-ink">{summary.main}</p>
        {summary.notes && (
          <details className="mt-3 text-xs text-muted">
            <summary className="cursor-pointer font-medium text-track">Technical details</summary>
            <p className="mt-2 leading-relaxed">{summary.notes}</p>
          </details>
        )}
      </div>

      {/* Simple summary, before any raw numbers */}
      {analysis.landingProfile && (
        <div className="mt-8">
          <LandingProfileCard profile={analysis.landingProfile} />
        </div>
      )}

      {/* Chart */}
      <div className="mt-8">
        <h2 className="mb-3 font-display text-lg font-semibold text-ink">Measurements at landing</h2>
        <ReportChart metrics={analysis.metrics} />
      </div>

      {/* Metric cards */}
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {analysis.metrics.map((m) => (
          <MetricCard key={m.key} metric={m} />
        ))}
      </div>

      {/* Box-jump protocol fidelity — context for the LESS card below it */}
      {analysis.protocolCheck && (
        <div className="mt-8">
          <ProtocolCheckCard protocolCheck={analysis.protocolCheck} />
        </div>
      )}

      {/* LESS score — the real, cited 17-item assessment */}
      <div className="mt-8">
        <LessScoreCard lessScore={analysis.lessScore} />
      </div>

      {/* Self-reported epidemiological risk factors (separate from LESS) */}
      <div className="mt-8">
        <ReportedFactorsCard factors={analysis.reportedFactors} />
      </div>

      {/* Personalized exercise recommendations from this scan's priorities */}
      <div className="mt-8">
        <RecommendedExercisesCard recommendations={analysis.recommendations} />
      </div>

      {/* Disclaimer + actions */}
      <div className="mt-10 rounded-xl bg-surface p-4">
        <p className="text-xs leading-relaxed text-muted">
          <span className="font-semibold text-ink">Not a diagnosis.</span>{" "}
          These measurements describe movement mechanics associated with ACL risk in
          research literature. They are not a medical assessment. Consult a qualified
          professional for health decisions.
        </p>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button href="/capture" variant="primary">Record another</Button>
        <Button href={`/compare?a=${analysis.id}`} variant="outline">Compare with another landing</Button>
        <Button href="/history" variant="outline">View history</Button>
      </div>
    </section>
  );
}
