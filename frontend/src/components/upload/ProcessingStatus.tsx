"use client";

import { ProcessingStage } from "@/lib/types";

type ProcessingStatusProps = {
  stage: ProcessingStage; // which step we're on
  progress: number;       // 0–100, used for the upload bar
  fileName: string;       // the video being analyzed
};

// The three visible steps, in order.
const STEPS: { key: ProcessingStage; label: string; sub: string }[] = [
  { key: "uploading", label: "Uploading", sub: "Sending your video securely" },
  { key: "processing", label: "Processing", sub: "Detecting body landmarks frame by frame" },
  { key: "complete", label: "Analysis complete", sub: "Measurements ready to view" },
];

function stageIndex(stage: ProcessingStage): number {
  if (stage === "uploading") return 0;
  if (stage === "processing") return 1;
  if (stage === "complete") return 2;
  return -1; // idle / error
}

export default function ProcessingStatus({
  stage,
  progress,
  fileName,
}: ProcessingStatusProps) {
  const current = stageIndex(stage);

  return (
    <div className="rounded-2xl border border-line bg-white p-8">
      <div className="mb-6 flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-ink">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M4 4h16v16H4z" stroke="#F5F7FA" strokeWidth="2" />
            <path d="M10 9l5 3-5 3V9z" fill="#F5F7FA" />
          </svg>
        </span>
        <span className="truncate font-mono text-sm text-ink">{fileName}</span>
      </div>

      <div className="space-y-5">
        {STEPS.map((step, i) => {
          const isDone = current > i || stage === "complete";
          const isActive = current === i && stage !== "complete";

          return (
            <div key={step.key} className="flex items-start gap-4">
              {isDone ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-track">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M5 12l5 5L20 7" stroke="white" strokeWidth="2.5"
                          strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              ) : isActive ? (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-track-soft">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-track border-t-transparent" />
                </span>
              ) : (
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-line font-mono text-xs text-muted">
                  {i + 1}
                </span>
              )}

              <div className="flex-1">
                <p className={`font-display text-sm font-semibold ${isDone || isActive ? "text-ink" : "text-muted"}`}>
                  {step.label}
                </p>
                <p className="text-xs text-muted">{step.sub}</p>

                {isActive && step.key === "uploading" && (
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-track-soft">
                    <div
                      className="h-full rounded-full bg-track transition-all duration-150"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}