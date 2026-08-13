// ============================================================
// history/page.tsx — the REAL history list.
//
// Fetches every saved analysis from GET /history and lists them,
// newest first, each linking to its full report. Client component
// because it fetches in the browser and has loading/empty states.
// ============================================================
"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getHistory, HistoryItem } from "@/lib/api";
import Button from "@/components/ui/Button";

export default function HistoryPage() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getHistory()
      .then((data) => {
        if (active) {
          setItems(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Could not load history.");
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <div className="mb-8 flex items-end justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
            Analysis history
          </h1>
          <p className="mt-1 text-muted">Every saved analysis, newest first.</p>
        </div>
        <Button href="/capture" variant="primary" className="!px-5 !py-2">Record a video</Button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-16 text-center">
          <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-track border-t-transparent" />
          <p className="mt-3 text-sm text-muted">Loading…</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="rounded-xl border border-risk/30 bg-risk-soft/40 p-6 text-center text-sm text-muted">
          {error}
          <p className="mt-1 text-xs">Make sure the backend is running at localhost:8000.</p>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && items.length === 0 && (
        <div className="rounded-2xl border border-dashed border-line bg-white p-12 text-center">
          <p className="font-display text-lg font-semibold text-ink">No analyses yet</p>
          <p className="mt-1 text-sm text-muted">Record a jump-landing video to see it here.</p>
          <div className="mt-5">
            <Button href="/capture" variant="primary">Record a video</Button>
          </div>
        </div>
      )}

      {/* The list */}
      {!loading && !error && items.length > 0 && (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id}>
              <Link
                href={`/report/${item.id}`}
                className="block rounded-xl border border-line bg-white p-5 transition-shadow hover:shadow-md"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-display font-semibold text-ink">{item.athleteName}</p>
                    <p className="mt-1 line-clamp-1 text-sm text-muted">{item.summary}</p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="font-mono text-xs text-muted">
                      {new Date(item.createdAt).toLocaleDateString()}
                    </p>
                    <span className="text-sm text-track">Open →</span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
