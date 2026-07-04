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
      // A gentle animation used for the hero skeleton pulse.
      keyframes: {
        pulseNode: {
          "0%, 100%": { opacity: "0.4", transform: "scale(0.9)" },
          "50%": { opacity: "1", transform: "scale(1.15)" },
        },
        drawIn: {
          "0%": { strokeDashoffset: "1000" },
          "100%": { strokeDashoffset: "0" },
        },
      },
      animation: {
        pulseNode: "pulseNode 3s ease-in-out infinite",
        drawIn: "drawIn 2s ease-out forwards",
      },
    },
  },
  plugins: [],
};

export default config;
