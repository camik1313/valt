// ============================================================
// RequiredQuestionnaire.tsx — the ONE questionnaire step, asked once,
// after the athlete has actually seen their landing (not before —
// "overall impression" can't be honestly answered before there's
// footage to look at).
//
// Combines two things that used to be separate, optional, side-by-side
// sections (which read as duplicated UI):
//   - The epidemiological risk-factor questions (age, sex, sport, etc.
//     — see backend/app/risk/scoring.py)
//   - LESS item 17, "overall impression" (see backend/app/risk/less.py)
//
// LESS items 13/14 (foot rotation) are deliberately NOT here — judging
// whether a foot turned in/out more than 30 degrees at the deepest
// point of a landing, from a phone video, is too hard to call reliably
// by eye. Better to not ask than to collect a guess.
//
// Every field here is REQUIRED — no skip option. Use isQuestionnaireComplete()
// to gate the "Continue"/"Submit" action.
// ============================================================

import { LessQuestionnaireAnswers, QuestionnaireAnswers } from "@/lib/types";

export type RequiredAnswers = QuestionnaireAnswers & LessQuestionnaireAnswers;

type Props = {
  value: RequiredAnswers;
  onChange: (next: RequiredAnswers) => void;
};

const selectClass =
  "mt-1 w-full rounded-lg border border-line bg-white px-3 py-2 font-body text-sm text-ink " +
  "focus:border-track focus:outline-none focus:ring-2 focus:ring-track/30";

export function isQuestionnaireComplete(a: RequiredAnswers): boolean {
  return (
    a.previousAclInjury !== undefined && a.previousAclInjury !== null &&
    !!a.sex &&
    !!a.sportType &&
    a.age !== undefined && a.age !== null && a.age > 0 &&
    !!a.activityLevel &&
    a.fatigueReported !== undefined && a.fatigueReported !== null &&
    a.previousLowerLimbInjury !== undefined && a.previousLowerLimbInjury !== null &&
    a.currentPainOrInjury !== undefined && a.currentPainOrInjury !== null &&
    !!a.overallImpression
  );
}

export default function RequiredQuestionnaire({ value, onChange }: Props) {
  function set<K extends keyof RequiredAnswers>(key: K, next: RequiredAnswers[K]) {
    onChange({ ...value, [key]: next });
  }

  return (
    <div className="space-y-5">
      <p className="text-xs text-muted">
        A few quick questions. These add real, cited risk-factor context (and
        one LESS item) to the score. All required, it only takes a minute.
      </p>

      <YesNoField
        required
        label="Previous ACL injury (either knee)?"
        value={value.previousAclInjury ?? null}
        onChange={(v) => set("previousAclInjury", v)}
      />

      <label className="block text-sm font-medium text-ink">
        Sex <span className="text-risk">*</span>
        <select
          className={selectClass}
          value={value.sex ?? ""}
          onChange={(e) => set("sex", e.target.value as QuestionnaireAnswers["sex"])}
        >
          <option value="" disabled>Choose one</option>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="other">Other</option>
          <option value="prefer_not_to_say">Prefer not to say</option>
        </select>
      </label>

      <label className="block text-sm font-medium text-ink">
        Primary sport type <span className="text-risk">*</span>
        <select
          className={selectClass}
          value={value.sportType ?? ""}
          onChange={(e) => set("sportType", e.target.value as QuestionnaireAnswers["sportType"])}
        >
          <option value="" disabled>Choose one</option>
          <option value="pivoting_cutting">Pivoting / cutting (soccer, basketball, etc.)</option>
          <option value="field_court_other">Other field / court sport</option>
          <option value="endurance_noncontact">Endurance / non-contact (running, swimming, etc.)</option>
          <option value="other">Other</option>
        </select>
      </label>

      <label className="block text-sm font-medium text-ink">
        Age <span className="text-risk">*</span>
        <input
          type="number"
          min={1}
          max={120}
          className={selectClass}
          value={value.age ?? ""}
          placeholder="Required"
          onChange={(e) => set("age", e.target.value === "" ? null : Number(e.target.value))}
        />
      </label>

      <label className="block text-sm font-medium text-ink">
        Activity / competition level <span className="text-risk">*</span>
        <select
          className={selectClass}
          value={value.activityLevel ?? ""}
          onChange={(e) => set("activityLevel", e.target.value as QuestionnaireAnswers["activityLevel"])}
        >
          <option value="" disabled>Choose one</option>
          <option value="sedentary">Sedentary</option>
          <option value="recreational">Recreational</option>
          <option value="competitive_high_school">Competitive, high school</option>
          <option value="competitive_college_or_pro">Competitive, college or pro</option>
        </select>
      </label>

      <YesNoField
        required
        label="Currently training/competing while fatigued or in a heavy load period?"
        value={value.fatigueReported ?? null}
        onChange={(v) => set("fatigueReported", v)}
      />

      <YesNoField
        required
        label="Previous lower-limb injury other than ACL (e.g. ankle sprain)?"
        value={value.previousLowerLimbInjury ?? null}
        onChange={(v) => set("previousLowerLimbInjury", v)}
      />

      <div>
        <YesNoField
          required
          label="Currently experiencing pain or injury?"
          value={value.currentPainOrInjury ?? null}
          onChange={(v) => set("currentPainOrInjury", v)}
        />
        {value.currentPainOrInjury === true && (
          <p className="mt-2 rounded-lg bg-risk-soft/40 p-3 text-xs leading-relaxed text-ink">
            This tool is intended for movement education, not injury diagnosis
            or rehabilitation. Because you reported current pain or injury,
            no exercise recommendations will be generated for this scan.
            Follow the guidance of your physician, physical therapist, or
            athletic trainer.
          </p>
        )}
      </div>

      <fieldset>
        <legend className="text-sm font-medium text-ink">
          Overall impression of the landing you just recorded <span className="text-risk">*</span>
        </legend>
        <div className="mt-2 grid grid-cols-3 gap-2">
          {(
            [
              { key: "excellent", title: "Excellent", sub: "Soft, controlled, no sideways motion" },
              { key: "average", title: "Average", sub: "Some sideways or stiff motion" },
              { key: "poor", title: "Poor", sub: "Large sideways motion or very stiff" },
            ] as { key: "excellent" | "average" | "poor"; title: string; sub: string }[]
          ).map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => set("overallImpression", opt.key)}
              className={[
                "rounded-lg border p-3 text-left transition-all",
                value.overallImpression === opt.key
                  ? "border-track bg-track-soft"
                  : "border-line bg-white hover:border-track/50",
              ].join(" ")}
            >
              <span className="block font-display text-sm font-semibold text-ink">
                {opt.title}
              </span>
              <span className="mt-0.5 block text-[11px] leading-snug text-muted">
                {opt.sub}
              </span>
            </button>
          ))}
        </div>
      </fieldset>
    </div>
  );
}

function YesNoField({
  label,
  value,
  onChange,
  required,
}: {
  label: string;
  value: boolean | null;
  onChange: (next: boolean | null) => void;
  required?: boolean;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-medium text-ink">
        {label} {required && <span className="text-risk">*</span>}
      </legend>
      <div className="mt-2 grid grid-cols-2 gap-2">
        {(
          [
            { key: true, title: "Yes" },
            { key: false, title: "No" },
          ] as { key: boolean; title: string }[]
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
