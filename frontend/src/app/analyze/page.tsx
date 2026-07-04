"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import VideoUploader from "@/components/upload/VideoUploader";
import ProcessingStatus from "@/components/upload/ProcessingStatus";
import Button from "@/components/ui/Button";
import { ProcessingStage } from "@/lib/types";

export default function AnalyzePage() {
  const [stage, setStage] = useState<ProcessingStage>("idle"); // which step
  const [file, setFile] = useState<File | null>(null);          // chosen file
  const [progress, setProgress] = useState(0);                  // 0–100

  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  function prettySize(bytes: number): string {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function handleFileSelected(chosen: File) {
    setFile(chosen);
    setStage("idle");
    setProgress(0);
  }

  // THE FAKE PIPELINE — the one place we'll swap in real API calls later.
  function startAnalysis() {
    if (!file) return;

    // 1) Uploading: animate progress 0 → 100.
    setStage("uploading");
    setProgress(0);
    let pct = 0;
    const uploadInterval = setInterval(() => {
      pct += 8;
      setProgress(Math.min(pct, 100));
      if (pct >= 100) clearInterval(uploadInterval);
    }, 120);

    // 2) Processing after ~2s, 3) Complete after ~4.5s.
    const toProcessing = setTimeout(() => setStage("processing"), 2000);
    const toComplete = setTimeout(() => setStage("complete"), 4500);
    timers.current.push(toProcessing, toComplete);
  }

  function reset() {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setStage("idle");
    setFile(null);
    setProgress(0);
  }

  return (
    <section className="mx-auto max-w-2xl px-6 py-16 md:py-24">
      <div className="mb-8 text-center">
        <span className="font-mono text-xs uppercase tracking-widest text-track">
          Analyze
        </span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-4xl">
          Upload a jump-landing video
        </h1>
        <p className="mt-3 text-muted">
          Front-facing clip, athlete landing in frame. We&apos;ll measure the mechanics.
        </p>
      </div>

      {stage === "idle" && (
        <>
          {!file ? (
            <VideoUploader onFileSelected={handleFileSelected} />
          ) : (
            <div className="rounded-2xl border border-line bg-white p-8">
              <div className="flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-track-soft">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M4 4h16v16H4z" stroke="#0E7C86" strokeWidth="2" />
                    <path d="M10 9l5 3-5 3V9z" fill="#0E7C86" />
                  </svg>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-mono text-sm text-ink">{file.name}</p>
                  <p className="text-xs text-muted">{prettySize(file.size)} · ready to analyze</p>
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <Button onClick={startAnalysis} variant="primary" className="flex-1">
                  Start analysis
                </Button>
                <Button onClick={reset} variant="outline">
                  Choose another
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {stage !== "idle" && file && (
        <div className="space-y-6">
          <ProcessingStatus stage={stage} progress={progress} fileName={file.name} />

          {stage === "complete" && (
            <div className="rounded-2xl border border-track-soft bg-track-soft/40 p-6 text-center">
              <p className="font-display text-lg font-semibold text-ink">
                Your movement report is ready
              </p>
              <p className="mt-1 text-sm text-muted">
                (Preview data for now — real measurements arrive when we connect the analysis engine.)
              </p>
              <div className="mt-5 flex justify-center gap-3">
                <Button href="/report/demo-001" variant="primary">
                  View report →
                </Button>
                <Button onClick={reset} variant="outline">
                  Analyze another
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      <p className="mt-8 text-center text-xs text-muted">
        Measures movement mechanics. Does not diagnose injuries.{" "}
        <Link href="/#about" className="text-track hover:underline">Learn more</Link>
      </p>
    </section>
  );
}