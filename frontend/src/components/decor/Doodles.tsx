// ============================================================
// Doodles.tsx — small, hand-drawn decorative shapes: gradient blobs,
// sparkles, squiggles, dot clusters.
//
// PURELY DECORATIVE. These never carry data or status meaning — that's
// what track (ok) / amber (watch) / risk (flag) are for, defined in
// tailwind.config.ts and used only on MetricCard / RiskScoreCard / report
// surfaces. Doodles live in marketing sections and empty-state backgrounds,
// so the "instrument readout" parts of the app stay unambiguous.
//
// Every shape takes a `className` for position/size (caller controls
// placement with Tailwind's absolute/inset utilities) and is marked
// aria-hidden since it's decoration, not content.
// ============================================================

const HEX: Record<string, string> = {
  bloom: "#EC5A94",
  iris: "#8B6BF2",
  sprout: "#2FBD7E",
  track: "#0E7C86",
};

type Hue = keyof typeof HEX;

// A soft, blurred gradient glow — the "color wash" behind hero/section
// content. Caller sizes and positions it (e.g. "h-72 w-72 -top-10 -left-10").
export function GradientBlob({
  id,
  className = "",
  from = "bloom",
  to = "iris",
}: {
  id: string;
  className?: string;
  from?: Hue;
  to?: Hue;
}) {
  return (
    <svg
      viewBox="0 0 200 200"
      className={`pointer-events-none absolute blur-3xl ${className}`}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={HEX[from]} />
          <stop offset="100%" stopColor={HEX[to]} />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="100" fill={`url(#${id})`} />
    </svg>
  );
}

// A four-point sparkle/star — the classic "whimsy" glyph.
export function Sparkle({
  className = "",
  color = "bloom",
}: {
  className?: string;
  color?: Hue;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
    >
      <path
        d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z"
        fill={HEX[color]}
      />
    </svg>
  );
}

// A gentle wavy line — a hand-drawn underline / divider accent.
export function Squiggle({
  className = "",
  color = "iris",
}: {
  className?: string;
  color?: Hue;
}) {
  return (
    <svg
      viewBox="0 0 100 20"
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
      preserveAspectRatio="none"
    >
      <path
        d="M0 12 Q 12.5 2, 25 12 T 50 12 T 75 12 T 100 12"
        fill="none"
        stroke={HEX[color]}
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

// A loose scatter of small dots — a lightweight "confetti" accent.
export function DotCluster({
  className = "",
  color = "sprout",
}: {
  className?: string;
  color?: Hue;
}) {
  const dots = [
    { cx: 4, cy: 6, r: 3 },
    { cx: 20, cy: 2, r: 2 },
    { cx: 32, cy: 14, r: 2.5 },
    { cx: 12, cy: 20, r: 1.75 },
  ];
  return (
    <svg
      viewBox="0 0 36 24"
      className={`pointer-events-none ${className}`}
      aria-hidden="true"
    >
      {dots.map((d, i) => (
        <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill={HEX[color]} opacity={0.85} />
      ))}
    </svg>
  );
}

// A soft, squircle-ish blob outline — used behind small icons for a
// friendlier alternative to a plain rounded square.
export function BlobBadge({
  className = "",
  color = "bloom",
  children,
}: {
  className?: string;
  color?: Hue;
  children?: React.ReactNode;
}) {
  return (
    <div className={`relative flex items-center justify-center ${className}`}>
      <svg viewBox="0 0 40 40" className="absolute inset-0 h-full w-full" aria-hidden="true">
        <path
          d="M28.9,-13.6C33.8,-4.9,33.2,7.9,27,17.4C20.8,26.9,10.4,33,-0.9,33.4C-12.2,33.9,-24.4,28.6,-30.6,19C-36.8,9.4,-37,-4.5,-31.2,-14.9C-25.5,-25.3,-13.7,-32,-1.6,-31.6C10.6,-31.1,21.1,-23.6,28.9,-13.6Z"
          fill={HEX[color]}
          fillOpacity="0.16"
          transform="translate(20 20)"
        />
      </svg>
      <div className="relative">{children}</div>
    </div>
  );
}
