// ============================================================
// api.ts — the ONLY file in the frontend that talks to the backend.
//
// Every network call goes through here. If the backend URL changes,
// or we add authentication later, we edit this one file — not the
// fifty components that need data. This is why api.ts exists.
//
// The backend URL comes from an environment variable so it can be
// "localhost:8000" in development and your Render URL in production,
// without changing code.
// ============================================================

import { Analysis, CameraView, LessQuestionnaireAnswers, QuestionnaireAnswers } from "./types";

// Read the backend URL from the environment, with a sensible fallback.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Shape of the /upload response.
export type UploadResult = {
  uploadId: string;
  filename: string;
  message: string;
};

// Shape of one history entry.
export type HistoryItem = {
  id: string;
  athleteName: string;
  createdAt: string;
  summary: string;
};

// A small helper that turns a failed response into a readable error.
async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    // Try to read the backend's error message; fall back to the status.
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* response had no JSON body; keep the default message */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// ---- POST /upload : send the video file ----
export async function uploadVideo(file: File): Promise<UploadResult> {
  // FormData is how browsers send files in a POST request.
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API_URL}/upload`, {
    method: "POST",
    body: form,
  });
  return handle<UploadResult>(res);
}

// ---- POST /analyze : run analysis on an uploaded video ----
// `questionnaire` is optional — omit it to get a risk score covering the
// biomechanical portion only (see RiskScore in types.ts).
// `sideUploadId` is an optional SECOND clip from the same session, filmed
// from the opposite angle (front primary -> side second, or vice versa).
// When given, its measurements are merged with the primary clip's, so the
// screening score AND the LESS score can see both frontal- and sagittal-
// plane criteria instead of just one.
// `lessQuestionnaire` answers the 3 LESS items no camera can score (foot
// rotation x2, overall impression) — also optional.
// `athleteHeightCm`, `groundWindowSeconds`, and `boxWindowSeconds` are only
// meaningful for the guided box-jump capture flow (see capture/page.tsx) —
// omit them for the plain file-upload fallback, which has no box-jump
// choreography to calibrate against.
export async function analyzeVideo(
  uploadId: string,
  athleteName: string,
  view: CameraView,
  questionnaire?: QuestionnaireAnswers,
  sideUploadId?: string,
  lessQuestionnaire?: LessQuestionnaireAnswers,
  athleteHeightCm?: number,
  groundWindowSeconds?: [number, number],
  boxWindowSeconds?: [number, number]
): Promise<Analysis> {
  const res = await fetch(`${API_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      uploadId,
      athleteName,
      view,
      questionnaire,
      sideUploadId,
      lessQuestionnaire,
      athleteHeightCm,
      groundWindowSeconds,
      boxWindowSeconds,
    }),
  });
  return handle<Analysis>(res);
}

// ---- GET /report/{id} : fetch one saved analysis ----
export async function getReport(id: string): Promise<Analysis> {
  const res = await fetch(`${API_URL}/report/${id}`);
  return handle<Analysis>(res);
}

// ---- GET /history : list past analyses ----
export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_URL}/history`);
  return handle<HistoryItem[]>(res);
}
