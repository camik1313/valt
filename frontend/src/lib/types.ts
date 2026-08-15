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
// an injury probability. This is a small set of illustrative biomechanical
// checks PLUS a real, cited epidemiological questionnaire (prior injury,
// sex, sport, age, activity level, fatigue) — general risk-factor context
// that sits alongside, but is not part of, the LESS score below.
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

// ============================================================
// LESS (Landing Error Scoring System) — mirrors backend/app/risk/less.py.
// This is the REAL, cited 17-item LESS, not an inspired subset. See
// less.py's module docstring for the full citations and for exactly
// which items are measured from video vs. self-reported (foot rotation
// x2 and "overall impression" — items no 2D camera can resolve).
// ============================================================

// The 3 LESS items no camera can score. Every field optional — leave
// unanswered fields out and those items just won't count toward the total.
export type LessQuestionnaireAnswers = {
  footIrMaxFlexion?: boolean | null;   // item 13: toes turned in >30° at max flexion?
  footErMaxFlexion?: boolean | null;   // item 14: toes turned out >30° at max flexion?
  overallImpression?: "excellent" | "average" | "poor" | null;  // item 17
};

// One of the 17 LESS items, scored.
export type LessItemScore = {
  number: number;            // 1-17, matching the official scoring sheet
  key: string;
  view: "sagittal" | "frontal" | "overall";
  label: string;              // the official sheet's short name
  goodCriterion: string;      // the official sheet's "no error" description
  points: number;
  maxPoints: number;
  source: "measured" | "self_reported" | "unavailable";
  detail: string;             // plain-language explanation of this item's score
};

// The full LESS result attached to an Analysis.
export type LessScore = {
  totalPoints: number;
  maxPoints: number;         // only items THIS session could score count
  percentOfMax: number;
  band: "low" | "moderate" | "high";
  items: LessItemScore[];
  viewsAvailable: string[];   // which of "front"/"side" contributed
  disclaimer: string;
  cutoffCitation: string;
};

// ============================================================
// PROTOCOL CHECK — mirrors backend/app/cv/calibration.py. Not a score;
// it's a measured record of whether the real LESS box-jump setup (12in
// box, land at half the athlete's height) was actually followed, derived
// from the athlete's own body in the video rather than trusted from
// manual entry. null whenever calibration wasn't attempted (height not
// given, or a clip not from the guided box-jump capture flow) or wasn't
// confident enough to report.
// ============================================================
export type ProtocolCheck = {
  boxHeightCm: number | null;
  landingDistanceCm: number | null;
  landingDistanceTargetCm: number | null;
  landingDistanceDeltaCm: number | null;
  confident: boolean;
  note: string;
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
  // The real, cited LESS score. Also null on mock fallback.
  lessScore: LessScore | null;
  // Measured box-jump protocol fidelity. null when calibration wasn't
  // available for this analysis (see ProtocolCheck above).
  protocolCheck: ProtocolCheck | null;
};

// The status the upload screen moves through.
export type ProcessingStage =
  | "idle"
  | "uploading"
  | "processing"
  | "complete"
  | "error";
