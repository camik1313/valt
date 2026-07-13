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
import Button from "@/components/ui/Button";

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
          <Button href="/analyze" variant="primary">Analyze a video</Button>
        </div>
      </section>
    );
  }

  // ---- Loaded: show the full report ----
  const created = new Date(analysis.createdAt).toLocaleString();

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
        <p className="mt-2 leading-relaxed text-ink">{analysis.summary}</p>
      </div>

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

      {/* Disclaimer + actions */}
      <div className="mt-10 rounded-xl bg-surface p-4">
        <p className="text-xs leading-relaxed text-muted">
          <span className="font-semibold text-ink">Not a diagnosis.</span>{" "}
          These measurements describe movement mechanics associated with ACL risk in
          research literature. They are not a medical assessment. Consult a qualified
          professional for health decisions.
        </p>
      </div>

      <div className="mt-6 flex gap-3">
        <Button href="/analyze" variant="primary">Analyze another</Button>
        <Button href="/history" variant="outline">View history</Button>
      </div>
    </section>
  );
}
