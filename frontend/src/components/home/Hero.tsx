// ============================================================
// Hero.tsx — the first thing visitors see.
// The SIGNATURE element is on the right: a dark "instrument card"
// with an SVG pose skeleton and live-looking readouts, styled after
// a data-forward athletic product (WHOOP-style readout, not a soft
// illustration) — this is a measurement instrument, not a doodle.
// ============================================================

import Button from "@/components/ui/Button";

export default function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* faint background grid to reinforce the "measurement instrument" feel */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(#E2E8EF 1px, transparent 1px), linear-gradient(90deg, #E2E8EF 1px, transparent 1px)",
          backgroundSize: "44px 44px",
        }}
      />

      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-6 py-20 md:grid-cols-2 md:py-28">
        {/* ---- Left: the message ---- */}
        <div className="relative">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            Movement science for female athletes
          </span>

          <h1 className="mt-4 font-display text-4xl font-bold leading-[1.05] tracking-tight text-ink md:text-6xl">
            Understand your{" "}
            <span className="relative inline-block">
              landing.
              <span
                aria-hidden="true"
                className="absolute -bottom-1 left-0 h-1 w-full rounded-full bg-track"
              />
            </span>
          </h1>

          <p className="mt-6 max-w-md text-lg leading-relaxed text-muted">
            Female athletes face a substantially higher burden of ACL injury in
            jumping and cutting sports, and most tears happen with no contact to
            the knee at all. VALT uses two smartphone videos to measure the
            landing mechanics researchers study as modifiable risk factors, the
            kind of analysis that&apos;s usually locked inside a biomechanics lab.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/capture" variant="primary">
              Analyze my landing →
            </Button>
            <Button href="/#how" variant="outline">
              See how it works
            </Button>
          </div>

          <p className="mt-6 text-xs text-muted">
            Measures movement mechanics. Does not diagnose injuries.
          </p>
        </div>

        {/* ---- Right: the signature pose skeleton, a dark instrument card ---- */}
        <div className="relative">
          <div className="relative overflow-hidden rounded-2xl bg-ink p-6 shadow-lg">
            {/* Little header row that mimics an analysis readout */}
            <div className="mb-4 flex items-center justify-between">
              <span className="font-mono text-xs text-surface/60">landing_frame.pose</span>
              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-[10px] text-track">
                33 landmarks
              </span>
            </div>

            <PoseSkeleton />

            {/* Fake metric readout under the figure — reinforces the concept */}
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Readout label="Knee flexion" value="72°" />
              <Readout label="Valgus" value="14°" risk />
              <Readout label="Trunk lean" value="9°" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// A small labeled numeric readout in monospace ("instrument output").
function Readout({
  label,
  value,
  risk = false,
}: {
  label: string;
  value: string;
  risk?: boolean;
}) {
  return (
    <div className="rounded-lg bg-white/5 px-3 py-2">
      <div className="font-mono text-[10px] uppercase tracking-wide text-surface/50">{label}</div>
      <div className={`font-mono text-lg font-bold ${risk ? "text-risk" : "text-surface"}`}>
        {value}
      </div>
    </div>
  );
}

// ------------------------------------------------------------
// PoseSkeleton — hand-placed landmark coordinates for an athlete
// in a landing position, connected into a stick figure. Nodes
// pulse via the Tailwind "pulseNode" animation. This is purely
// decorative for now; the real one comes from MediaPipe later.
// ------------------------------------------------------------
function PoseSkeleton() {
  // Landmark coordinates (x, y) in the SVG's 260x300 space.
  const P = {
    head: [130, 40],
    shoulderL: [100, 80],
    shoulderR: [160, 80],
    elbowL: [80, 120],
    elbowR: [180, 120],
    wristL: [70, 160],
    wristR: [190, 160],
    hipL: [110, 160],
    hipR: [150, 160],
    kneeL: [92, 220], // knees drawn slightly inward = the valgus story
    kneeR: [168, 220],
    ankleL: [104, 280],
    ankleR: [156, 280],
  } as const;

  // Which landmarks connect to which (the "bones").
  const bones: [keyof typeof P, keyof typeof P][] = [
    ["head", "shoulderL"], ["head", "shoulderR"],
    ["shoulderL", "shoulderR"],
    ["shoulderL", "elbowL"], ["elbowL", "wristL"],
    ["shoulderR", "elbowR"], ["elbowR", "wristR"],
    ["shoulderL", "hipL"], ["shoulderR", "hipR"],
    ["hipL", "hipR"],
    ["hipL", "kneeL"], ["kneeL", "ankleL"],
    ["hipR", "kneeR"], ["kneeR", "ankleR"],
  ];

  return (
    <svg viewBox="0 0 260 300" className="mx-auto h-64 w-auto" role="img"
         aria-label="Illustration of a body's tracked landmarks in a landing pose">
      {/* Bones */}
      {bones.map(([a, b], i) => (
        <line
          key={i}
          x1={P[a][0]} y1={P[a][1]}
          x2={P[b][0]} y2={P[b][1]}
          stroke="#0E7C86"
          strokeWidth="2.5"
          strokeLinecap="round"
          opacity="0.55"
        />
      ))}

      {/* Landmark nodes. Knees use the RISK color to highlight the key joint. */}
      {(Object.keys(P) as (keyof typeof P)[]).map((k, i) => {
        const isKnee = k === "kneeL" || k === "kneeR";
        return (
          <circle
            key={k}
            cx={P[k][0]}
            cy={P[k][1]}
            r={isKnee ? 6 : 4.5}
            fill={isKnee ? "#E0552B" : "#F5F7FA"}
            className="animate-pulseNode"
            style={{ animationDelay: `${(i % 6) * 0.25}s`, transformOrigin: "center",
                     transformBox: "fill-box" as const }}
          />
        );
      })}
    </svg>
  );
}
