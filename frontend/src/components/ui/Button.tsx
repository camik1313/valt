// ============================================================
// Button.tsx — one reusable button used everywhere in the app.
// Writing it once means every button looks and behaves the same.
// It supports two visual "variants" (primary / outline) and can
// render either as a real <button> or as a link (via `href`).
// ============================================================

import Link from "next/link";
import { ReactNode } from "react";

type ButtonProps = {
  children: ReactNode;
  href?: string;                     // if provided, renders as a link
  variant?: "primary" | "outline";  // visual style
  onClick?: () => void;
  className?: string;
  type?: "button" | "submit";
  disabled?: boolean;                // only applies to the <button> form, not href links
};

// Shared base styles for every button.
const base =
  "inline-flex items-center justify-center gap-2 rounded-lg px-6 py-3 " +
  "font-body font-medium text-sm transition-all duration-200 hover:scale-[1.03] active:scale-[0.98] " +
  "focus:outline-none focus-visible:ring-2 focus-visible:ring-track focus-visible:ring-offset-2 " +
  "disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:shadow-none disabled:hover:scale-100";

// Variant-specific styles.
const variants = {
  primary: "bg-ink text-surface hover:bg-track hover:shadow-lg hover:shadow-track/20",
  outline: "border border-line text-ink bg-white hover:border-track hover:text-track",
};

export default function Button({
  children,
  href,
  variant = "primary",
  onClick,
  className = "",
  type = "button",
  disabled = false,
}: ButtonProps) {
  const classes = `${base} ${variants[variant]} ${className}`;

  // If an href is given, it's a navigation link. Otherwise a clickable button.
  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} disabled={disabled} className={classes}>
      {children}
    </button>
  );
}
