// ============================================================
// Navbar.tsx — the top navigation bar shown on every page.
// It's "sticky": it stays pinned to the top as you scroll.
// The links with "#..." jump to sections on the homepage.
// ============================================================

import Link from "next/link";
import { Video, Dumbbell, GitCompareArrows, BookOpen } from "lucide-react";
import Button from "@/components/ui/Button";

// One accent per link, cycling through the broader palette — purely
// decorative (which icon gets which color carries no meaning), so it's
// safe to vary even though track/watch/risk stay reserved for status
// elsewhere in the app.
const NAV_LINKS = [
  { href: "/capture", label: "Analyze", Icon: Video, hover: "group-hover:text-track" },
  { href: "/exercises", label: "Exercises", Icon: Dumbbell, hover: "group-hover:text-spark" },
  { href: "/compare", label: "Compare", Icon: GitCompareArrows, hover: "group-hover:text-watch" },
  { href: "/why", label: "Learn", Icon: BookOpen, hover: "group-hover:text-risk" },
] as const;

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-surface/80 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        {/* ---- Logo ---- */}
        <Link href="/" className="flex items-center gap-2">
          {/* Small SVG mark: two landmark dots joined by a line — the pose motif. */}
          <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
            <line x1="7" y1="7" x2="19" y2="19" stroke="#0E7C86" strokeWidth="2" />
            <circle cx="7" cy="7" r="4" fill="#132033" />
            <circle cx="19" cy="19" r="4" fill="#0E7C86" />
          </svg>
          <span className="font-display text-lg font-bold tracking-tight text-ink">
            VALT
          </span>
        </Link>

        {/* ---- Center links (hidden on small screens) ---- */}
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map(({ href, label, Icon, hover }) => (
            <Link
              key={href}
              href={href}
              className="group flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-ink"
            >
              <Icon size={15} className={`text-muted transition-colors ${hover}`} aria-hidden="true" />
              {label}
            </Link>
          ))}
        </div>

        {/* ---- Primary action ---- */}
        <Button href="/capture" variant="primary" className="!px-5 !py-2">
          Analyze my landing
        </Button>
      </nav>
    </header>
  );
}
