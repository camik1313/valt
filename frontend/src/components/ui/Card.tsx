// ============================================================
// Card.tsx — a simple white panel with a subtle border.
// Used for feature tiles, metric boxes, etc. Reusable so every
// "card" in the app shares the same look.
// ============================================================

import { ReactNode } from "react";

type CardProps = {
  children: ReactNode;
  className?: string;
};

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={
        "rounded-xl border border-line bg-white p-6 " +
        "transition-shadow duration-200 hover:shadow-md " +
        className
      }
    >
      {children}
    </div>
  );
}
