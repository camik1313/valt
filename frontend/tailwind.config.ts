import type { Config } from "tailwindcss";

// ============================================================
// Tailwind configuration = our DESIGN SYSTEM in one place.
// Every color and font used across the app is defined here so
// the whole product stays visually consistent. Change a value
// here and it updates everywhere.
// ============================================================

const config: Config = {
  // Which files Tailwind scans for class names (so it can strip unused CSS).
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      // ---- COLOR SYSTEM (see README design notes) ----
      // Each color has semantic meaning, not just a look.
      colors: {
        // Cool clinical off-white — the page background. NOT cream.
        surface: "#F5F7FA",
        // Deep slate-navy — structure, dark sections, primary text.
        ink: "#132033",
        // Softer ink for secondary text.
        muted: "#5A6B7B",
        // TEAL = "tracked motion." The instrument/measurement color.
        track: {
          DEFAULT: "#0E7C86",
          soft: "#D3EAEC",
        },
        // WARM SIGNAL = reserved ONLY for risk-associated indicators.
        // Using it sparingly keeps its meaning strong.
        risk: {
          DEFAULT: "#E0552B",
          soft: "#FBE3DA",
        },
        // Hairline borders / dividers.
        line: "#E2E8EF",
        // ---- DECORATIVE PALETTE ----
        // Pink / purple / green, used ONLY for illustration accents,
        // doodles, and gradient washes (Doodles.tsx, hero/section
        // backgrounds, category icon variety). NEVER for data or status
        // meaning — status stays track (ok) / amber (watch) / risk (flag),
        // always, so a measurement's color never gets ambiguous.
        bloom: {
          DEFAULT: "#EC5A94",
          soft: "#FCE3EF",
        },
        iris: {
          DEFAULT: "#8B6BF2",
          soft: "#ECE6FD",
        },
        sprout: {
          DEFAULT: "#2FBD7E",
          soft: "#DCF6E9",
        },
      },
      // ---- TYPOGRAPHY ----
      // These names map to fonts we load in layout.tsx via next/font.
      fontFamily: {
        // Technical display face — headlines.
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        // Clean body face — paragraphs and UI.
        body: ["var(--font-body)", "system-ui", "sans-serif"],
        // Monospace — numeric readouts, so measurements look like instrument output.
        mono: ["var(--font-mono)", "monospace"],
      },
      // Gentle animations for the hero skeleton pulse and decorative doodles.
      keyframes: {
        pulseNode: {
          "0%, 100%": { opacity: "0.4", transform: "scale(0.9)" },
          "50%": { opacity: "1", transform: "scale(1.15)" },
        },
        drawIn: {
          "0%": { strokeDashoffset: "1000" },
          "100%": { strokeDashoffset: "0" },
        },
        // Slow drift for background gradient blobs — barely-there motion,
        // just enough to feel alive without being distracting.
        drift: {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "50%": { transform: "translate(14px, -18px) scale(1.06)" },
        },
        // A small playful rock, used on sparkle/star doodles.
        wiggle: {
          "0%, 100%": { transform: "rotate(-6deg)" },
          "50%": { transform: "rotate(6deg)" },
        },
      },
      animation: {
        pulseNode: "pulseNode 3s ease-in-out infinite",
        drawIn: "drawIn 2s ease-out forwards",
        drift: "drift 9s ease-in-out infinite",
        wiggle: "wiggle 4s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
