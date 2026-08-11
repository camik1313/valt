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

// Which camera angle a video was filmed from. This determines which
// measurements are scientifically valid — see backend cv/pipeline.py.
//   front -> frontal plane  -> knee valgus, lateral trunk lean
//   side  -> sagittal plane -> knee/hip flexion, forward trunk lean
export type CameraView = "front" | "side";

// ============================================================
// SCREENING RISK SCORE — mirrors backend/app/risk/scoring.py and
// backend/app/models/schemas.py. See scoring.py for the full "what this
// is and isn't" explanation: NOT a diagnosis, NOT a trained model, NEVER
// an injury probability — just a transparent points-based checklist over
// (a) the biomechanical error criteria this app's 2D pipeline can measure
// (a LESS-inspired SUBSET, not the full 17-item LESS) and (b) an optional
// self-report questionnaire.
// ============================================================

// The optional self-report questionnaire. Every field is optional —
// leave the whole object out to skip it entirely.
export type QuestionnaireAnswers = {
  previousAclInjury?: boolean | null;
  sex?: "female" | "male" | "other" | "prefer_not_to_say" | null;
  sportType?:
    | "pivoting_cutting"
    | "field_court_other"
    | "endurance_noncontact"
    | "other"
    | null;
  age?: number | null;
  activityLevel?:
    | "sedentary"
    | "recreational"
    | "competitive_high_school"
    | "competitive_college_or_pro"
    | null;
  fatigueReported?: boolean | null;
  previousLowerLimbInjury?: boolean | null;
};

// One factor that moved the screening score, in plain language.
export type ContributingFactor = {
  key: string;
  label: string;
  points: number;
  detail: string;
};

// Subtotal for one half of the score (biomechanical or questionnaire).
export type PartialScore = {
  points: number;
  maxPoints: number;
  factors: ContributingFactor[];
};

// The full screening result attached to an Analysis.
export type RiskScore = {
  band: "low" | "moderate" | "elevated";
  percentOfMax: number;      // 0..100, percent of ACHIEVABLE points — not a probability
  totalPoints: number;
  totalMaxPoints: number;
  biomechanical: PartialScore;
  // null when no questionnaire was submitted — show the biomechanical
  // portion only in that case.
  questionnaire: PartialScore | null;
  factors: ContributingFactor[];   // biomechanical + questionnaire, combined
  disclaimer: string;
};

// A single completed analysis of one video.
export type Analysis = {
  id: string;
  athleteName: string;
  createdAt: string;      // ISO date string
  videoFilename: string;
  // "front", "side", or "front+side" / "side+front" when a same-session
  // second clip from the opposite angle was combined into this analysis.
  view: string;
  metrics: Metric[];
  summary: string;        // plain-language overview
  // null when the real pipeline didn't run (e.g. mock fallback) — there
  // are no real measurements to screen in that case.
  riskScore: RiskScore | null;
};

// The status the upload screen moves through.
export type ProcessingStage =
  | "idle"
  | "uploading"
  | "processing"
  | "complete"
  | "error";
