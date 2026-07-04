// ============================================================
// analyze/page.tsx — the upload workflow, NOW WIRED TO THE BACKEND.
//
// The flow is the same as before, but startAnalysis() no longer
// fakes it with timers. It calls the real API:
//   uploadVideo()  -> POST /upload
//   analyzeVideo() -> POST /analyze
// and then routes the user to the real report by id.
//
// All network calls go through lib/api.ts (never fetch() directly
// here) — that's the boundary that keeps this component clean.
// ============================================================
"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import VideoUploader from "@/components/upload/VideoUploader";
import ProcessingStatus from "@/components/upload/ProcessingStatus";
import Button from "@/components/ui/Button";
import { ProcessingStage } from "@/lib/types";
import { uploadVideo, analyzeVideo } from "@/lib/api";

export default function AnalyzePage() {
  const [stage, setStage] = useState<ProcessingStage>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [athleteName, setAthleteName] = useState("Athlete");
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Ref to the progress-animation interval so we can stop it.
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  function prettySize(bytes: number): string {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function handleFileSelected(chosen: File) {
    setFile(chosen);
    setStage("idle");
    setProgress(0);
    setErrorMsg(null);
  }

  // ---- THE REAL PIPELINE (calls the backend) ----
  async function startAnalysis() {
    if (!file) return;
    setErrorMsg(null);

    try {
      // 1) UPLOADING. Real uploads are fast locally, so we animate the
      //    bar up to ~90% while we wait, then snap to 100% when done.
      setStage("uploading");
      setProgress(0);
      let pct = 0;
      progressTimer.current = setInterval(() => {
        pct = Math.min(pct + 7, 90);
        setProgress(pct);
      }, 100);

      const upload = await uploadVideo(file); // POST /upload

      if (progressTimer.current) clearInterval(progressTimer.current);
      setProgress(100);

      // 2) PROCESSING. Ask the backend to analyze the uploaded video.
      setStage("processing");
      const analysis = await analyzeVideo(upload.uploadId, athleteName); // POST /analyze

      // 3) COMPLETE. Remember the id so we can link to the real report.
      setAnalysisId(analysis.id);
      setStage("complete");
    } catch (err) {
      if (progressTimer.current) clearInterval(progressTimer.current);
      // Show a friendly error. Most common cause: backend not running.
      const message =
        err instanceof Error ? err.message : "Something went wrong.";
      setErrorMsg(message);
      setStage("error");
    }
  }

  function reset() {
    if (progressTimer.current) clearInterval(progressTimer.current);
    setStage("idle");
    setFile(null);
    setProgress(0);
    setAnalysisId(null);
    setErrorMsg(null);
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

      {/* ---- IDLE: pick a file, name the athlete, start ---- */}
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

              {/* Athlete name — sets up multi-athlete support. */}
              <label className="mt-6 block text-sm font-medium text-ink">
                Athlete name
                <input
                  type="text"
                  value={athleteName}
                  onChange={(e) => setAthleteName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-line px-3 py-2 font-body text-sm text-ink focus:border-track focus:outline-none focus:ring-2 focus:ring-track/30"
                  placeholder="e.g. Jordan Lee"
                />
              </label>

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

      {/* ---- BUSY / COMPLETE ---- */}
      {(stage === "uploading" || stage === "processing" || stage === "complete") && file && (
        <div className="space-y-6">
          <ProcessingStatus stage={stage} progress={progress} fileName={file.name} />

          {stage === "complete" && analysisId && (
            <div className="rounded-2xl border border-track-soft bg-track-soft/40 p-6 text-center">
              <p className="font-display text-lg font-semibold text-ink">
                {athleteName}&apos;s movement report is ready
              </p>
              <p className="mt-1 text-sm text-muted">
                Measurements saved. Open the report to see the full breakdown.
              </p>
              <div className="mt-5 flex justify-center gap-3">
                <Button href={`/report/${analysisId}`} variant="primary">
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

      {/* ---- ERROR ---- */}
      {stage === "error" && (
        <div className="rounded-2xl border border-risk/30 bg-risk-soft/40 p-6 text-center">
          <p className="font-display text-lg font-semibold text-ink">
            We couldn&apos;t complete the analysis
          </p>
          <p className="mt-2 text-sm text-muted">{errorMsg}</p>
          <p className="mt-2 text-xs text-muted">
            Tip: make sure the backend server is running at localhost:8000.
          </p>
          <div className="mt-5">
            <Button onClick={reset} variant="outline">
              Try again
            </Button>
          </div>
        </div>
      )}

      <p className="mt-8 text-center text-xs text-muted">
        Measures movement mechanics. Does not diagnose injuries.{" "}
        <Link href="/#about" className="text-track hover:underline">Learn more</Link>
      </p>
    </section>
  );
}
