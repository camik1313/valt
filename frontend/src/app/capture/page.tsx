// ============================================================
// capture/page.tsx — GUIDED VIDEO CAPTURE. This is the ONLY way to
// submit a video in this app — there is no separate "upload a file"
// entry point in normal use (see /analyze, which still exists only as
// a fallback if camera access genuinely fails).
//
// Records a jump-landing video in the browser with on-screen (and now
// audible) guidance so the clip ALWAYS has the structure the science
// needs:
//   [ stand still (baseline) ] -> [ JUMP ] -> [ hold the landing ]
//
// The standing segment at the start is exactly what the backend's
// auto-baseline detector looks for — so guided captures get
// perspective-corrected valgus automatically.
//
// FULLY AUTOMATIC RECORDING: there's no "Stop recording" button anymore.
// The JUMP cue holds for roughly as long as an average jump takes (reaction
// + takeoff + brief airborne time), then the app automatically guides a
// short "hold your landing" period and stops recording on its own — one
// less thing to fumble with mid-jump. Short beeps mark each countdown
// step and phase change so you don't have to watch the screen closely.
//
// TWO-ANGLE SESSION: after the first clip, the athlete is guided to turn
// 90° (camera stays put) and record a second clip from the OPPOSITE angle
// in the same session. Both clips are uploaded and merged into one
// analysis on the backend (see AnalyzeRequest.sideUploadId), which lets
// the screening score see both frontal- and sagittal-plane criteria
// instead of just one. The second clip is optional — skippable from
// either the first clip's review screen or the transition screen.
//
// FLOW (state machine in `phase`, `clipIndex` tracks which of the up-to-2
// clips is currently being recorded/reviewed):
//   setup         -> checklist + athlete name + starting angle, then "Open camera"
//   ready         -> live camera preview (flip front/back here), "Start recording"
//   positioning   -> ~5s to walk into frame (NOT yet recording), beeps each second
//   standing      -> 3s "stand still" countdown (recording starts here), beeps
//   jump          -> big "JUMP!" cue, auto-timed to ~an average jump, then auto-advances
//   hold          -> "hold your landing" cue, auto-timed, then auto-stops recording
//   review        -> play back the clip; continue/retake/skip
//   transition    -> guided "turn to the other angle" instructions (clip 1 -> 2 only)
//   questionnaire -> ONE required questionnaire, asked once you've seen your landing
//   uploading / processing -> hand off to the existing analyze pipeline
//   error         -> camera or analysis problem (only place /analyze is offered, as a fallback)
//
// Uses the browser MediaRecorder + getUserMedia APIs, plus the Web Audio
// API for the countdown beeps (synthesized, no audio file needed).
// Requires HTTPS in production (localhost is exempt for local testing).
// ============================================================
"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Button from "@/components/ui/Button";
import { CameraView, ProcessingStage } from "@/lib/types";
import { uploadVideo, analyzeVideo } from "@/lib/api";
import ProcessingStatus from "@/components/upload/ProcessingStatus";
import RequiredQuestionnaire, {
  RequiredAnswers,
  isQuestionnaireComplete,
} from "@/components/questionnaire/RequiredQuestionnaire";

type Phase =
  | "setup"
  | "ready"
  | "positioning"
  | "standing"
  | "jump"
  | "hold"
  | "review"
  | "transition"
  | "questionnaire"
  | "uploading"
  | "processing"
  | "error";

type RecordedClip = { blob: Blob; url: string; ext: string };
type FacingMode = "environment" | "user";

// Timing for the guided phases (seconds).
const POSITION_SECONDS = 5;  // time to walk into frame after tapping record
const STANDING_SECONDS = 3;  // baseline period that must be recorded
const JUMP_SECONDS = 1.3;    // roughly the reaction + takeoff + airborne time of an average jump
const HOLD_SECONDS = 2;      // stay still after landing so the frame the pipeline needs is clean

function viewLabel(v: CameraView): string {
  return v === "front" ? "front-on" : "side-on";
}

// ---- Web Audio beeps (synthesized — no audio file needed) ----
type AudioContextConstructor = typeof AudioContext;

function getAudioContextConstructor(): AudioContextConstructor | undefined {
  if (typeof window === "undefined") return undefined;
  return (
    window.AudioContext ??
    (window as unknown as { webkitAudioContext?: AudioContextConstructor }).webkitAudioContext
  );
}

export default function CapturePage() {
  const router = useRouter();

  const [phase, setPhase] = useState<Phase>("setup");
  const [athleteName, setAthleteName] = useState("Athlete");
  const [view, setView] = useState<CameraView>("front"); // starting angle (clip 1)
  const [clipIndex, setClipIndex] = useState<0 | 1>(0);
  const [facing, setFacing] = useState<FacingMode>("environment");
  const [requiredAnswers, setRequiredAnswers] = useState<RequiredAnswers>({});
  const [pendingIncludeSecond, setPendingIncludeSecond] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const otherView: CameraView = view === "front" ? "side" : "front";
  const currentClipView: CameraView = clipIndex === 0 ? view : otherView;

  // Refs to browser objects that live outside React's render cycle.
  const videoRef = useRef<HTMLVideoElement | null>(null);      // live preview
  const reviewRef = useRef<HTMLVideoElement | null>(null);     // playback
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioCtxRef = useRef<AudioContext | null>(null);
  // Up to two recorded clips, indexed by clipIndex (0 = starting angle, 1 = opposite angle).
  const clipsRef = useRef<(RecordedClip | undefined)[]>([undefined, undefined]);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  // Clean up camera + timers + recorded clip URLs when leaving the page.
  useEffect(() => {
    return () => {
      stopStream();
      timersRef.current.forEach(clearTimeout);
      clipsRef.current.forEach((c) => c && URL.revokeObjectURL(c.url));
      audioCtxRef.current?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function stopStream() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }

  // Re-attach the live stream to the <video> preview whenever we enter a
  // camera phase. The preview element unmounts during "review"/"transition"
  // (a different block renders), so on clip 2's "ready" phase React mounts
  // a BRAND NEW <video> node — without this, it would show a blank preview
  // since openCamera() (which sets srcObject) only runs once, before clip 1.
  useEffect(() => {
    const isCameraPhase =
      phase === "ready" || phase === "positioning" || phase === "standing" ||
      phase === "jump" || phase === "hold";
    if (isCameraPhase && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [phase]);

  // ---- Beep helpers ----
  function ensureAudioContext(): AudioContext | null {
    const Ctor = getAudioContextConstructor();
    if (!Ctor) return null;
    if (!audioCtxRef.current) {
      audioCtxRef.current = new Ctor();
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }

  function playBeep(frequency: number, durationMs: number) {
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = frequency;
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + durationMs / 1000);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + durationMs / 1000 + 0.03);
  }

  // ---- Open the camera and show the live preview ----
  async function openCamera(useFacing: FacingMode = facing) {
    setErrorMsg(null);
    try {
      // "environment" = rear camera, "user" = front/selfie camera.
      // audio off — we only need video.
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: useFacing, width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setPhase("ready");
    } catch (err) {
      setErrorMsg(
        "Could not access the camera. Check that you granted camera permission " +
          "(and that you're on https:// or localhost)."
      );
      setPhase("error");
    }
  }

  // ---- Switch between front and back camera (iPhone/Android both support this) ----
  async function flipCamera() {
    const next: FacingMode = facing === "environment" ? "user" : "environment";
    stopStream();
    setFacing(next);
    await openCamera(next);
  }

  // ---- Choose a recording format the browser supports ----
  function pickMimeType(): { mime: string; ext: string } {
    const prefs = [
      { mime: "video/mp4;codecs=h264", ext: "mp4" },
      { mime: "video/mp4", ext: "mp4" },
      { mime: "video/webm;codecs=vp9", ext: "webm" },
      { mime: "video/webm", ext: "webm" },
    ];
    for (const p of prefs) {
      // isTypeSupported may be missing on very old browsers; guard it.
      if (typeof MediaRecorder !== "undefined" &&
          MediaRecorder.isTypeSupported &&
          MediaRecorder.isTypeSupported(p.mime)) {
        return p;
      }
    }
    return { mime: "", ext: "webm" }; // let the browser pick a default
  }

  // ---- Begin the guided recording sequence for the CURRENT clip ----
  function startRecording() {
    if (!streamRef.current) return;
    setErrorMsg(null);
    ensureAudioContext(); // unlock audio now, inside this user-gesture click

    // Phase 1: give the athlete time to walk into frame. Not recording yet.
    setPhase("positioning");
    runCountdown(POSITION_SECONDS, () => beginStandingAndRecord());
  }

  function beginStandingAndRecord() {
    // Start the actual recording NOW, so the clip begins with the standing
    // baseline (clean frame-0 standing period for the detector).
    const { mime, ext } = pickMimeType();
    const recordingClipIndex = clipIndex; // capture for the closure below
    chunksRef.current = [];
    const recorder = mime
      ? new MediaRecorder(streamRef.current!, { mimeType: mime })
      : new MediaRecorder(streamRef.current!);

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const type = recorder.mimeType || "video/webm";
      const blob = new Blob(chunksRef.current, { type });
      const url = URL.createObjectURL(blob);
      clipsRef.current[recordingClipIndex] = { blob, url, ext };
      if (reviewRef.current) reviewRef.current.src = url;
      setPhase("review");
    };
    recorder.start();
    recorderRef.current = recorder;

    // Phase 2: standing baseline countdown (recorded).
    setPhase("standing");
    runCountdown(STANDING_SECONDS, () => beginJumpAndHold());
  }

  // Phase 3+4, fully automatic: JUMP cue for ~ an average jump's duration,
  // then a guided landing hold, then the recording stops itself.
  function beginJumpAndHold() {
    playBeep(1400, 250); // the "go" signal
    setPhase("jump");
    timersRef.current.push(
      setTimeout(() => {
        playBeep(660, 150); // "you should be landing about now, hold still"
        setPhase("hold");
        timersRef.current.push(
          setTimeout(() => {
            playBeep(1046, 200); // done
            recorderRef.current?.stop(); // triggers onstop -> review
          }, HOLD_SECONDS * 1000)
        );
      }, JUMP_SECONDS * 1000)
    );
  }

  // Simple countdown helper: counts `seconds` down to 0, beeping each
  // second, then calls done().
  function runCountdown(seconds: number, done: () => void) {
    setCountdown(seconds);
    playBeep(880, 100);
    let remaining = seconds;
    const tick = () => {
      remaining -= 1;
      setCountdown(remaining);
      if (remaining > 0) {
        playBeep(880, 100);
        timersRef.current.push(setTimeout(tick, 1000));
      } else {
        done();
      }
    };
    timersRef.current.push(setTimeout(tick, 1000));
  }

  function retake() {
    // Discard the CURRENT clip and go back to the live preview.
    const current = clipsRef.current[clipIndex];
    if (current) URL.revokeObjectURL(current.url);
    clipsRef.current[clipIndex] = undefined;
    setPhase("ready");
  }

  // ---- Move on to guided instructions for the second (opposite) angle ----
  function goToTransition() {
    setPhase("transition");
  }

  // ---- User confirms they've turned; start recording the second clip ----
  function beginSecondClip() {
    setClipIndex(1);
    setPhase("ready");
  }

  function startOver() {
    stopStream();
    clipsRef.current.forEach((c) => c && URL.revokeObjectURL(c.url));
    clipsRef.current = [undefined, undefined];
    setClipIndex(0);
    setErrorMsg(null);
    setRequiredAnswers({});
    setPhase("setup");
  }

  // ---- All clips are done; ask the one required questionnaire before submitting ----
  function goToQuestionnaire(includeSecond: boolean) {
    setPendingIncludeSecond(includeSecond);
    setPhase("questionnaire");
  }

  // ---- Upload the recorded clip(s) and run analysis ----
  async function finish(includeSecond: boolean) {
    const primaryClip = clipsRef.current[0];
    if (!primaryClip) return;

    try {
      setPhase("uploading");
      setProgress(0);
      let pct = 0;
      const t = setInterval(() => {
        pct = Math.min(pct + 7, 90);
        setProgress(pct);
      }, 100);

      const primaryFile = new File(
        [primaryClip.blob],
        `capture_${view}_${Date.now()}.${primaryClip.ext}`,
        { type: primaryClip.blob.type }
      );
      const primaryUpload = await uploadVideo(primaryFile);

      let sideUploadId: string | undefined;
      const secondClip = clipsRef.current[1];
      if (includeSecond && secondClip) {
        const secondFile = new File(
          [secondClip.blob],
          `capture_${otherView}_${Date.now()}.${secondClip.ext}`,
          { type: secondClip.blob.type }
        );
        const secondUpload = await uploadVideo(secondFile);
        sideUploadId = secondUpload.uploadId;
      }

      clearInterval(t);
      setProgress(100);

      setPhase("processing");
      const analysis = await analyzeVideo(
        primaryUpload.uploadId,
        athleteName,
        view,
        requiredAnswers,
        sideUploadId,
        requiredAnswers
      );

      stopStream();
      router.push(`/report/${analysis.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      setErrorMsg(message);
      setPhase("error");
    }
  }

  // Map our capture phases onto the shared ProcessingStatus component.
  const processingStage: ProcessingStage =
    phase === "uploading" ? "uploading" : phase === "processing" ? "processing" : "idle";

  const recording = phase === "standing" || phase === "jump" || phase === "hold";
  const cameraPhase =
    phase === "ready" || phase === "positioning" || phase === "standing" ||
    phase === "jump" || phase === "hold";

  return (
    <section className="mx-auto max-w-2xl px-6 py-12">
      <div className="mb-6 text-center">
        <span className="font-mono text-xs uppercase tracking-widest text-track">
          Guided capture
        </span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink">
          Record a jump landing
        </h1>
      </div>

      {/* ---------- SETUP ---------- */}
      {phase === "setup" && (
        <div className="rounded-2xl border border-line bg-white p-6">
          <h2 className="font-display font-semibold text-ink">Before you record</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li className="flex gap-2"><span className="text-track">1.</span> Prop your phone on something stable, about chest height.</li>
            <li className="flex gap-2"><span className="text-track">2.</span> Stand back 3–4 m (10–13 ft) so the whole body fits in frame.</li>
            <li className="flex gap-2"><span className="text-track">3.</span> Center the camera squarely on the athlete, not off to one side.</li>
            <li className="flex gap-2"><span className="text-track">4.</span> Good, even lighting. Fitted clothing works best.</li>
            <li className="flex gap-2"><span className="text-track">5.</span> After you tap record: {POSITION_SECONDS}s to get in position, a {STANDING_SECONDS}s &quot;stand still&quot;, a JUMP cue, then a moment to hold your landing. All automatic, with beeps to guide you, no need to tap stop.</li>
            <li className="flex gap-2"><span className="text-track">6.</span> Afterward you&apos;ll be guided to turn and record the opposite angle too (optional, but it roughly doubles what the screening score can see).</li>
            <li className="flex gap-2"><span className="text-track">7.</span> A few required questions come right after recording, once you&apos;ve seen your landing.</li>
          </ul>

          <label className="mt-6 block text-sm font-medium text-ink">
            Athlete name
            <input
              type="text"
              value={athleteName}
              onChange={(e) => setAthleteName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-line px-3 py-2 text-sm focus:border-track focus:outline-none focus:ring-2 focus:ring-track/30"
              placeholder="e.g. Jordan Lee"
            />
          </label>

          <fieldset className="mt-4">
            <legend className="text-sm font-medium text-ink">Starting angle</legend>
            <p className="mt-1 text-xs text-muted">
              You&apos;ll be guided to add the opposite angle right after this one.
            </p>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {([
                { key: "front", title: "Front-on", sub: "Knee valgus" },
                { key: "side", title: "Side-on", sub: "Knee & hip flexion" },
              ] as { key: CameraView; title: string; sub: string }[]).map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setView(opt.key)}
                  className={[
                    "rounded-lg border p-3 text-left transition-all",
                    view === opt.key ? "border-track bg-track-soft" : "border-line hover:border-track/50",
                  ].join(" ")}
                >
                  <span className="block font-display text-sm font-semibold text-ink">{opt.title}</span>
                  <span className="mt-0.5 block text-xs text-muted">{opt.sub}</span>
                </button>
              ))}
            </div>
          </fieldset>

          <div className="mt-6">
            <Button onClick={() => openCamera()} variant="primary" className="w-full">Open camera</Button>
          </div>
        </div>
      )}

      {/* ---------- CAMERA (ready / recording phases, either clip) ---------- */}
      {cameraPhase && (
        <div>
          <div className="relative overflow-hidden rounded-2xl border border-line bg-black">
            {/* Live camera preview. muted + playsInline are required for autoplay, especially on iOS. */}
            <video ref={videoRef} autoPlay muted playsInline className="h-auto w-full" />

            {/* Which clip this is, when doing a two-angle session. */}
            <div className="absolute right-3 top-3 rounded-full bg-black/60 px-3 py-1">
              <span className="font-mono text-xs text-white">
                {clipIndex === 0 ? "Clip 1" : "Clip 2"} · {viewLabel(currentClipView)}
              </span>
            </div>

            {/* Recording dot */}
            {recording && (
              <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-black/60 px-3 py-1">
                <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-risk" />
                <span className="font-mono text-xs text-white">REC</span>
              </div>
            )}

            {/* Flip camera — only while not recording. */}
            {phase === "ready" && (
              <button
                type="button"
                onClick={flipCamera}
                aria-label="Flip camera"
                className="absolute bottom-3 right-3 flex h-10 w-10 items-center justify-center rounded-full bg-black/60 text-white hover:bg-black/80"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M17 2l4 4-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M3 12v-2a4 4 0 0 1 4-4h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M7 22l-4-4 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                  <path d="M21 12v2a4 4 0 0 1-4 4H3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}

            {/* Big guided overlays */}
            {phase === "positioning" && (
              <Overlay label="Get in position" big={String(countdown)} />
            )}
            {phase === "standing" && (
              <Overlay label="Stand still" big={String(countdown)} />
            )}
            {phase === "jump" && (
              <Overlay label="" big="JUMP!" tone="risk" />
            )}
            {phase === "hold" && (
              <Overlay label="Stay still for the landing" big="HOLD" />
            )}
          </div>

          {/* Controls */}
          <div className="mt-4 flex flex-col items-center gap-2">
            {phase === "ready" && (
              <>
                <Button onClick={startRecording} variant="primary">Start recording</Button>
                {facing === "user" && (
                  <p className="text-center text-xs text-muted">
                    Front camera can mirror left/right in the video, so use the back
                    camera when you can for the most accurate results.
                  </p>
                )}
              </>
            )}
            {(phase === "positioning" || phase === "standing" || phase === "jump" || phase === "hold") && (
              <p className="text-sm text-muted">Recording will guide you automatically…</p>
            )}
          </div>
        </div>
      )}

      {/* ---------- REVIEW ---------- */}
      {phase === "review" && (
        <div className="rounded-2xl border border-line bg-white p-6">
          <h2 className="font-display font-semibold text-ink">
            Review your {viewLabel(currentClipView)} clip
          </h2>
          <video ref={reviewRef} controls playsInline className="mt-3 w-full rounded-lg bg-black" />
          <p className="mt-3 text-xs text-muted">
            Check that your whole body is in frame for the whole jump, and that the
            landing is captured. {clipsRef.current[clipIndex]?.ext === "webm" && (
              <span>
                (Recorded as .webm, which works, but phones record .mp4, which
                analyzes most reliably.)
              </span>
            )}
          </p>

          {clipIndex === 0 ? (
            <div className="mt-5 space-y-3">
              <div className="flex gap-3">
                <Button onClick={goToTransition} variant="primary" className="flex-1">
                  Continue, add {viewLabel(otherView)} angle
                </Button>
                <Button onClick={retake} variant="outline">Retake</Button>
              </div>
              <button
                type="button"
                onClick={() => goToQuestionnaire(false)}
                className="w-full text-center text-xs text-muted hover:text-track hover:underline"
              >
                Skip, analyze with just this clip
              </button>
            </div>
          ) : (
            <div className="mt-5 flex gap-3">
              <Button onClick={() => goToQuestionnaire(true)} variant="primary" className="flex-1">
                Use both clips
              </Button>
              <Button onClick={retake} variant="outline">Retake</Button>
            </div>
          )}
        </div>
      )}

      {/* ---------- TRANSITION (guided repositioning between clip 1 and 2) ---------- */}
      {phase === "transition" && (
        <div className="rounded-2xl border border-track-soft bg-track-soft/30 p-6 text-center">
          <p className="font-mono text-xs uppercase tracking-widest text-track">Nice work</p>
          <h2 className="mt-2 font-display text-xl font-semibold text-ink">
            Now let&apos;s get the {viewLabel(otherView)} angle
          </h2>
          <p className="mt-3 text-sm text-muted">
            Keep the camera exactly where it is, just the athlete moves.{" "}
            {otherView === "front"
              ? "Turn to face the camera directly."
              : "Turn 90° so your side faces the camera."}{" "}
            Same setup as before: stand still for a moment, then jump on the cue.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Button onClick={beginSecondClip} variant="primary">
              I&apos;m turned, start recording
            </Button>
          </div>
          <button
            type="button"
            onClick={() => goToQuestionnaire(false)}
            className="mt-4 text-xs text-muted hover:text-track hover:underline"
          >
            Skip, analyze with just the {viewLabel(view)} clip
          </button>
        </div>
      )}

      {/* ---------- QUESTIONNAIRE (required, asked once you've seen the landing) ---------- */}
      {phase === "questionnaire" && (
        <div className="rounded-2xl border border-line bg-white p-6">
          <h2 className="font-display font-semibold text-ink">A few required questions</h2>
          <p className="mt-2 text-sm text-muted">
            Last step. These add real, cited context to the score alongside your video.
          </p>
          <div className="mt-5">
            <RequiredQuestionnaire value={requiredAnswers} onChange={setRequiredAnswers} />
          </div>
          <div className="mt-6">
            <Button
              onClick={() => finish(pendingIncludeSecond)}
              variant="primary"
              className="w-full"
              disabled={!isQuestionnaireComplete(requiredAnswers)}
            >
              Submit and analyze
            </Button>
            {!isQuestionnaireComplete(requiredAnswers) && (
              <p className="mt-2 text-center text-xs text-muted">
                Answer every question above to continue.
              </p>
            )}
          </div>
        </div>
      )}

      {/* ---------- UPLOADING / PROCESSING ---------- */}
      {(phase === "uploading" || phase === "processing") && (
        <ProcessingStatus stage={processingStage} progress={progress} fileName="Your recording" />
      )}

      {/* ---------- ERROR ---------- */}
      {phase === "error" && (
        <div className="rounded-2xl border border-risk/30 bg-risk-soft/40 p-6 text-center">
          <p className="font-display font-semibold text-ink">Something went wrong</p>
          <p className="mt-2 text-sm text-muted">{errorMsg}</p>
          <div className="mt-5 flex justify-center gap-3">
            <Button onClick={startOver} variant="outline">Start over</Button>
            <Button href="/analyze" variant="primary">Upload a file instead</Button>
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

// A large centered overlay used for the guided cues.
function Overlay({ label, big, tone = "track" }: { label: string; big: string; tone?: "track" | "risk" }) {
  const color = tone === "risk" ? "text-risk" : "text-white";
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/40">
      {label && <span className="font-display text-lg font-medium text-white/90">{label}</span>}
      <span className={`font-display font-bold ${color} ${big.length > 2 ? "text-6xl" : "text-8xl"}`}>
        {big}
      </span>
    </div>
  );
}
