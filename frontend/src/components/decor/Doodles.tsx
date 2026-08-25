// ============================================================
// Doodles.tsx — small decorative primitives.
//
// Previously home to a multi-color "whimsy" system (gradient blobs,
// sparkles, a squiggle, a dot cluster) in pink/purple/green. Retired: it
// read as a generic pastel sports-app look, at odds with the athletic,
// data-forward identity (Nike Training Club / WHOOP / Strava, not a
// school-project illustration style) this app is going for. What's left
// is IconBadge — geometric rather than organic, still marked aria-hidden
// since it's decoration, not content. It now cycles through a broader
// palette (track/spark/watch/bloom) than the single-accent version that
// originally replaced the whimsy system, but every one of those colors
// is a deliberate, disciplined choice, never a pastel grab-bag, and
// still never used to signal status on a report page.
// ============================================================

const BADGE_BG: Record<"track" | "spark" | "watch" | "bloom", string> = {
  track: "bg-track-soft",
  spark: "bg-spark-soft",
  watch: "bg-watch-soft",
  bloom: "bg-bloom-soft",
};

// A small rounded-square badge behind an icon. Caller sizes it (e.g.
// "h-9 w-9"), optionally picks which accent tints it (defaults to the
// single brand accent, track), and passes the icon as children. The
// color choice is decorative only — never used to signal status.
export function IconBadge({
  className = "",
  color = "track",
  children,
}: {
  className?: string;
  color?: "track" | "spark" | "watch" | "bloom";
  children?: React.ReactNode;
}) {
  return (
    <div
      className={`flex items-center justify-center rounded-xl ${BADGE_BG[color]} ${className}`}
    >
      {children}
    </div>
  );
}
