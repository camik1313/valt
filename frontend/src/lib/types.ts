// ============================================================
// types.ts — shared TypeScript "shapes" for the app's data.
// Defining these once means the whole frontend agrees on what an
// Analysis or a Metric looks like. These MUST stay in sync with
// the backend's Pydantic schemas (Stage 5). Think of this file as
// the frontend half of the contract between frontend and backend.
// ============================================================

// One measured biomechanical value in a report.
export type Metric = {
  key: string;        // machine name, e.g. "knee_flexion"
  label: string;      // human name, e.g. "Knee flexion"
  value: number;      // the measured number
  unit: string;       // e.g. "deg"
  status: "ok" | "watch" | "flag"; // research-informed banding
};

// A single completed analysis of one video.
export type Analysis = {
  id: string;
  athleteName: string;
  createdAt: string;      // ISO date string
  videoFilename: string;
  metrics: Metric[];
  summary: string;        // plain-language overview
};

// The status the upload screen moves through.
export type ProcessingStage =
  | "idle"
  | "uploading"
  | "processing"
  | "complete"
  | "error";
