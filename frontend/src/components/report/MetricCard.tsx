// ============================================================
// MetricCard.tsx — displays ONE measured metric.
// Shows the label, the value in monospace (instrument readout),
// and a status badge colored by ok / watch / flag.
// ============================================================

import { Metric } from "@/lib/types";

// Map each status to its colors and human label.
// ok = teal (fine), watch = amber (borderline), flag = orange (notable).
const STATUS_STYLES: Record<Metric["status"], { badge: string; text: string; label: string }> = {
  ok:    { badge: "bg-track-soft",  text: "text-track", label: "Typical" },
  watch: { badge: "bg-watch-soft",  text: "text-watch",     label: "Borderline" },
  flag:  { badge: "bg-risk-soft",   text: "text-risk", label: "Notable" },
};

export default function MetricCard({ metric }: { metric: Metric }) {
  const s = STATUS_STYLES[metric.status];

  return (
    <div className="rounded-xl border border-line bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="font-display text-sm font-semibold text-ink">{metric.label}</h3>
        {/* Status badge */}
        <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${s.badge} ${s.text}`}>
          {s.label}
        </span>
      </div>

      {/* The measured value, big and monospace like an instrument. */}
      <div className="mt-3 flex items-baseline gap-1">
        <span className={`font-mono text-3xl font-bold ${s.text}`}>{metric.value}</span>
        <span className="font-mono text-sm text-muted">{metric.unit}</span>
      </div>
    </div>
  );
}
