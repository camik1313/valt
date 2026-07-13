// ============================================================
// ReportChart.tsx — a Plotly bar chart of the five measurements.
//
// TWO IMPORTANT DETAILS:
// 1) "use client" — Plotly draws in the browser using the DOM, so this
//    component must run client-side, not on the server.
// 2) dynamic(..., { ssr: false }) — we load react-plotly.js ONLY in the
//    browser. If Next.js tried to render Plotly on the server it would
//    crash (no `window` there). This is the standard Plotly + Next fix.
//
// The bars are colored by status so the chart tells the same story as
// the cards. Units differ between metrics (deg vs %), so we show the
// unit in the hover text rather than pretending one axis fits all.
// ============================================================
"use client";

import dynamic from "next/dynamic";
import { Metric } from "@/lib/types";

// Load Plotly only on the client.
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

// Status → bar color (matches the design tokens).
const COLOR: Record<Metric["status"], string> = {
  ok: "#0E7C86",     // teal
  watch: "#D97706",  // amber-600
  flag: "#E0552B",   // risk orange
};

export default function ReportChart({ metrics }: { metrics: Metric[] }) {
  // Plotly wants arrays. We build them from the metrics, top-to-bottom.
  const labels = metrics.map((m) => m.label);
  const values = metrics.map((m) => m.value);
  const colors = metrics.map((m) => COLOR[m.status]);
  const hover = metrics.map((m) => `${m.label}: ${m.value} ${m.unit}`);

  return (
    <div className="rounded-xl border border-line bg-white p-4">
      <Plot
        data={[
          {
            type: "bar",
            orientation: "h",          // horizontal bars
            x: values,
            y: labels,
            marker: { color: colors },
            hovertext: hover,
            hoverinfo: "text",
          },
        ]}
        layout={{
          height: 300,
          margin: { l: 140, r: 20, t: 10, b: 30 },
          font: { family: "Inter, sans-serif", size: 12, color: "#132033" },
          paper_bgcolor: "transparent",
          plot_bgcolor: "transparent",
          xaxis: { title: { text: "measured value (units vary)" }, gridcolor: "#E2E8EF" },
          yaxis: { automargin: true },
          bargap: 0.35,
        }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
      />
    </div>
  );
}
