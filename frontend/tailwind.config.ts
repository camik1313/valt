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
        // "Watch" / borderline status — formalizes what several report
        // components already rendered ad hoc with Tailwind's default
        // amber-700/amber-100. Same status meaning as risk/track (ok /
        // watch / flag), just now a real token instead of a magic string.
        watch: {
          DEFAULT: "#B45309",
          soft: "#FEF3C7",
        },
        // SPARK = decorative/engagement accent only — nav, badges, hero
        // highlights, marketing copy. Never used for a measurement,
        // score, status, or anything the athlete is meant to read as
        // clinical data; track/watch/risk keep doing that job alone.
        spark: {
          DEFAULT: "#2F6FED",
          soft: "#DCE7FE",
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
      // The pulse on the hero skeleton's landmark dots — a "live data" cue,
      // not decoration. Everything else animated used to live here too
      // (drift/wiggle for the retired doodle system, an unused drawIn) and
      // has been removed along with the components that used it.
      keyframes: {
        pulseNode: {
          "0%, 100%": { opacity: "0.4", transform: "scale(0.9)" },
          "50%": { opacity: "1", transform: "scale(1.15)" },
        },
      },
      animation: {
        pulseNode: "pulseNode 3s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
