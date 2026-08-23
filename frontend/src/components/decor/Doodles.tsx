// ============================================================
// Doodles.tsx — small decorative primitives.
//
// Previously home to a multi-color "whimsy" system (gradient blobs,
// sparkles, a squiggle, a dot cluster) in pink/purple/green. Retired: it
// read as a generic pastel sports-app look, at odds with the athletic,
// data-forward identity (Nike Training Club / WHOOP / Strava, not a
// school-project illustration style) this app is going for. What's left
// is IconBadge — a single, disciplined accent color, geometric rather
// than organic, still marked aria-hidden since it's decoration, not
// content.
// ============================================================

// A small rounded-square badge behind an icon, tinted with the single
// brand accent (track). Caller sizes it (e.g. "h-9 w-9") and passes the
// icon as children.
export function IconBadge({
  className = "",
  children,
}: {
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={`flex items-center justify-center rounded-xl bg-track-soft ${className}`}
    >
      {children}
    </div>
  );
}
