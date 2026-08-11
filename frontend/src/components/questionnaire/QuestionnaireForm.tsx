// ============================================================
// QuestionnaireForm.tsx — the OPTIONAL screening questionnaire.
//
// Shared by analyze/page.tsx and capture/page.tsx so the seven fields
// (see backend/app/risk/scoring.py QUESTIONNAIRE_CRITERIA) are only
// defined once. Every field is optional — an unanswered field is just
// left out of the object, and the backend scores only what was answered.
// ============================================================

import { QuestionnaireAnswers } from "@/lib/types";

type Props = {
  value: QuestionnaireAnswers;
  onChange: (next: QuestionnaireAnswers) => void;
};

const selectClass =
  "mt-1 w-full rounded-lg border border-line bg-white px-3 py-2 font-body text-sm text-ink " +
  "focus:border-track focus:outline-none focus:ring-2 focus:ring-track/30";

const inputClass = selectClass;

export default function QuestionnaireForm({ value, onChange }: Props) {
  function set<K extends keyof QuestionnaireAnswers>(key: K, next: QuestionnaireAnswers[K]) {
    onChange({ ...value, [key]: next });
  }

  return (
    <div className="space-y-5">
      <p className="text-xs text-muted">
        Optional. Used only to add a few well-documented epidemiological risk
        factors to the screening score alongside the video measurements —
        skip anything you&apos;d rather not answer.
      </p>

      <YesNoField
        label="Previous ACL injury (either knee)?"
        value={value.previousAclInjury ?? null}
        onChange={(v) => set("previousAclInjury", v)}
      />

      <label className="block text-sm font-medium text-ink">
        Sex
        <select
          className={selectClass}
          value={value.sex ?? ""}
          onChange={(e) =>
            set("sex", (e.target.value || null) as QuestionnaireAnswers["sex"])
          }
        >
          <option value="">Prefer not to say / skip</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label className="block text-sm font-medium text-ink">
        Primary sport type
        <select
          className={selectClass}
          value={value.sportType ?? ""}
          onChange={(e) =>
            set("sportType", (e.target.value || null) as QuestionnaireAnswers["sportType"])
          }
        >
          <option value="">Skip</option>
          <option value="pivoting_cutting">Pivoting / cutting (soccer, basketball, etc.)</option>
          <option value="field_court_other">Other field / court sport</option>
          <option value="endurance_noncontact">Endurance / non-contact (running, swimming, etc.)</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label className="block text-sm font-medium text-ink">
        Age
        <input
          type="number"
          min={0}
          max={120}
          className={inputClass}
          value={value.age ?? ""}
          placeholder="Skip"
          onChange={(e) => set("age", e.target.value === "" ? null : Number(e.target.value))}
        />
      </label>

      <label className="block text-sm font-medium text-ink">
        Activity / competition level
        <select
          className={selectClass}
          value={value.activityLevel ?? ""}
          onChange={(e) =>
            set(
              "activityLevel",
              (e.target.value || null) as QuestionnaireAnswers["activityLevel"]
            )
          }
        >
          <option value="">Skip</option>
          <option value="sedentary">Sedentary</option>
          <option value="recreational">Recreational</option>
          <option value="competitive_high_school">Competitive — high school</option>
          <option value="competitive_college_or_pro">Competitive — college / pro</option>
        </select>
      </label>

      <YesNoField
        label="Currently training/competing while fatigued or in a heavy load period?"
        value={value.fatigueReported ?? null}
        onChange={(v) => set("fatigueReported", v)}
      />

      <YesNoField
        label="Previous lower-limb injury other than ACL (e.g. ankle sprain)?"
        value={value.previousLowerLimbInjury ?? null}
        onChange={(v) => set("previousLowerLimbInjury", v)}
      />
    </div>
  );
}

// A Yes / No / Skip toggle, matching the button-group style already used
// for the camera-angle picker elsewhere in the app.
function YesNoField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean | null;
  onChange: (next: boolean | null) => void;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-medium text-ink">{label}</legend>
      <div className="mt-2 grid grid-cols-3 gap-2">
        {(
          [
            { key: true, title: "Yes" },
            { key: false, title: "No" },
            { key: null, title: "Skip" },
          ] as { key: boolean | null; title: string }[]
        ).map((opt) => (
          <button
            key={String(opt.key)}
            type="button"
            onClick={() => onChange(opt.key)}
            className={[
              "rounded-lg border px-3 py-2 text-sm transition-all",
              value === opt.key
                ? "border-track bg-track-soft text-ink"
                : "border-line bg-white text-muted hover:border-track/50",
            ].join(" ")}
          >
            {opt.title}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

// True if at least one field has been answered — used by the calling page
// to decide whether to send `questionnaire` at all (omitting it entirely
// gets a cleaner "biomechanical portion only" result than sending an
// all-empty object).
export function hasAnyAnswer(q: QuestionnaireAnswers): boolean {
  return Object.values(q).some((v) => v !== undefined && v !== null);
}
