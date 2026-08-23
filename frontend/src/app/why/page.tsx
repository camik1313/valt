// ============================================================
// why/page.tsx — the mission + the research behind VALT.
//
// Two things live here on purpose:
//   1. Real, cited statistics on ACL injury in sport — not vibes, not
//      rounded-for-effect numbers. Every figure below has a citation in
//      the References section, and every citation was looked up against
//      a real source before being used (not recalled from memory).
//   2. A full explanation of the Landing Error Scoring System (LESS),
//      the clinical tool VALT's LESS score (see LessScoreCard.tsx) is a
//      real, direct implementation of — what it is, who validated it,
//      how it's scored, and its one important caveat (the >=5 "high
//      risk" cutoff was derived in elite youth soccer players, not
//      validated as universal).
// ============================================================

import Button from "@/components/ui/Button";

type Stat = {
  value: string;
  label: string;
  detail: string;
  citation: string;
};

const STATS: Stat[] = [
  {
    value: "2–8x",
    label: "Higher ACL injury risk for female athletes",
    detail:
      "Across sports and studies, female athletes are consistently found to tear their ACL at several times the rate of male athletes in the same sport. In basketball specifically, pooled incidence rates run roughly 3–4x higher for women.",
    citation: "Prodromos et al. 2007; Martinez-Calderon et al. 2025",
  },
  {
    value: "~55–70%",
    label: "Of ACL injuries happen with no contact to the knee",
    detail:
      "Most ACL tears aren't collisions. They happen during ordinary landing, cutting, and pivoting movements, which is exactly why movement-quality screening tools like LESS exist: the mechanism is often visible in how someone lands, not in what hit them.",
    citation: "Chia et al. 2022; Martinez-Calderon et al. 2025",
  },
  {
    value: "1.1%",
    label: "Per-season ACL injury risk for a female high-school soccer player",
    detail:
      "The single highest per-season risk among common high-school sports in this data; female basketball (0.9%) and male football (0.8%) follow closely behind.",
    citation: "Children's Hospital of Philadelphia, citing Pediatrics incidence data",
  },
  {
    value: "+2.3%/yr",
    label: "Annual growth in youth ACL tears (ages 6–18), 1994–2013",
    detail:
      "ACL tears in young athletes haven't been flat. They've been climbing for decades, with the increase sharpest in younger age groups and in female athletes specifically.",
    citation: "Children's Hospital of Philadelphia, citing Pediatrics incidence data",
  },
  {
    value: "29.5%",
    label: "Suffered a second ACL injury within 2 years of returning to sport",
    detail:
      "In young athletes (mean age ~17) who reconstructed an ACL and returned to a pivoting/cutting sport: 20.5% to the opposite knee, 9.0% re-tearing the graft. Once is not just once.",
    citation: "Paterno et al. 2014",
  },
  {
    value: "0–19",
    label: "The LESS score range this app implements",
    detail:
      "A validated 17-item clinical checklist of landing-mechanics errors. Higher scores mean more errors and a stiffer, less controlled landing. See the full explanation below.",
    citation: "Padua et al. 2009",
  },
];

export default function WhyPage() {
  return (
    <>
      {/* ---------- HERO ---------- */}
      <section className="border-b border-line">
        <div className="relative mx-auto max-w-4xl px-6 py-16 md:py-20">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            Learn
          </span>
          <h1 className="mt-3 font-display text-3xl font-bold tracking-tight text-ink md:text-5xl">
            HER ACL
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted">
            ACL tears are common, costly, and, in most cases, non-contact, and
            female athletes carry a disproportionate share of that burden in
            jumping and cutting sports. Here&apos;s what the research actually
            says about why, what&apos;s modifiable, and the validated clinical
            tool (the Landing Error Scoring System) VALT puts within reach of
            any coach, athlete, or trainer with a smartphone.
          </p>
        </div>
      </section>

      {/* ---------- WHY FEMALE ATHLETES ---------- */}
      <section className="border-b border-line bg-white">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            Why female athletes?
          </span>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight text-ink md:text-3xl">
            What the research actually supports, and where it stops
          </h2>
          <ul className="mt-6 space-y-4 text-sm leading-relaxed text-muted">
            <li>
              <strong className="text-ink">Female athletes carry a disproportionate burden.</strong>{" "}
              Across sports and studies, they tear their ACL at several times
              the rate of male athletes in the same sport (see the numbers below).
            </li>
            <li>
              <strong className="text-ink">ACL injury is multifactorial.</strong>{" "}
              No single factor, biomechanical, hormonal, anatomical, or otherwise,
              determines whether any individual athlete will get hurt. Researchers
              study a mix of contributing factors, not one root cause.
            </li>
            <li>
              <strong className="text-ink">Landing mechanics and neuromuscular control are modifiable.</strong>{" "}
              Unlike anatomy, how an athlete lands, absorbs force, and controls her
              knee during a jump is something training can change, which is exactly
              why movement-quality screens like LESS exist.
            </li>
            <li>
              <strong className="text-ink">Adolescence is a critical window.</strong>{" "}
              Movement patterns are still forming during the teenage years, making
              this an especially relevant period to build good landing mechanics,
              not just correct bad ones later.
            </li>
            <li>
              <strong className="text-ink">Neuromuscular training has real evidence behind it.</strong>{" "}
              Structured injury-prevention programs that target landing and
              cutting mechanics have published evidence supporting their use in
              reducing injury risk.
            </li>
          </ul>
          <p className="mt-6 rounded-xl bg-surface p-4 text-xs leading-relaxed text-muted">
            What this page won&apos;t claim: that female athletes have
            &ldquo;weaker knees,&rdquo; or that any single biological difference
            explains the gap. The honest research answer is more complicated than
            that, and less useful for training than focusing on what&apos;s
            actually modifiable.
          </p>
        </div>
      </section>

      {/* ---------- STATS ---------- */}
      <section className="border-b border-line bg-white">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            ACL tears, by the numbers
          </span>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight text-ink md:text-3xl">
            Every figure here is cited. See References below
          </h2>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {STATS.map((s) => (
              <div key={s.label} className="rounded-2xl border border-line bg-white p-6">
                <p className="font-display text-4xl font-bold text-ink">{s.value}</p>
                <p className="mt-2 font-display text-sm font-semibold text-ink">{s.label}</p>
                <p className="mt-2 text-sm leading-relaxed text-muted">{s.detail}</p>
                <p className="mt-3 font-mono text-[11px] text-track">{s.citation}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- LESS EXPLAINER ---------- */}
      <section className="border-b border-line">
        <div className="mx-auto max-w-4xl px-6 py-16">
          <span className="font-mono text-xs uppercase tracking-widest text-track">
            The clinical tool
          </span>
          <h2 className="mt-3 font-display text-2xl font-bold tracking-tight text-ink md:text-3xl">
            What is the Landing Error Scoring System?
          </h2>
          <p className="mt-5 leading-relaxed text-muted">
            The Landing Error Scoring System (LESS) is a clinical screening tool developed
            at the University of North Carolina and published in 2009. An athlete performs
            a standardized jump, off a box, forward onto a landing line, then immediately
            up into a maximal vertical jump, while filmed from two angles at once: one
            camera facing the athlete (frontal plane) and one from the side (sagittal
            plane). A trained rater then scores the landing against 17 specific movement
            criteria, checking off an &ldquo;error&rdquo; wherever the athlete&apos;s
            mechanics fall outside what the literature associates with a well-controlled,
            lower-risk landing.
          </p>
          <p className="mt-4 leading-relaxed text-muted">
            It was validated against 3D motion capture (the gold standard, but expensive
            and lab-bound) and found to agree well enough with it that LESS could stand in
            for a full motion-capture lab in a normal gym or clinic, using nothing more than
            two video cameras and a trained eye.
          </p>

          <div className="mt-8 rounded-2xl border border-line bg-white p-6">
            <h3 className="font-display text-lg font-semibold text-ink">How it&apos;s scored</h3>
            <ul className="mt-4 space-y-3 text-sm leading-relaxed text-muted">
              <li>
                <strong className="text-ink">17 items, 0–19 points.</strong> 15 items are
                worth 1 point each (an error is either present or not); the last 2,
                overall joint stiffness and overall impression, are worth up to 2 points
                each. <strong className="text-ink">Higher scores mean more errors:</strong>{" "}
                a stiffer, less controlled landing.
              </li>
              <li>
                <strong className="text-ink">Two views, at two moments.</strong> Most items
                are scored twice: once at the instant the foot first touches the ground
                (&ldquo;initial contact&rdquo;), and again by how much that angle changes
                by the deepest point of the landing (&ldquo;displacement&rdquo;). A knee
                that looks fine at touchdown can still collapse inward as the athlete
                absorbs the landing. LESS is built to catch that.
              </li>
              <li>
                <strong className="text-ink">A published reference cutoff.</strong> A
                full-scale score of 5 or higher has been used as an illustrative
                &ldquo;higher-risk&rdquo; threshold in published research (86% sensitivity,
                64% specificity, and a roughly 10x higher one-season injury rate above that
                line versus below it), but{" "}
                <strong className="text-ink">
                  that specific cutoff was derived in elite youth soccer players
                </strong>
                , and no population-specific cutoff has been established for other sports,
                ages, or competition levels. Treat it as a reference point, not a rule.
              </li>
              <li>
                <strong className="text-ink">Normally averaged over 3 trials.</strong> The
                official protocol scores 3 jump attempts and averages them. VALT scores one
                trial per analysis, a real, stated limitation, not something to gloss over.
              </li>
            </ul>
          </div>

          <div className="mt-6 rounded-2xl border border-risk/30 bg-risk-soft/40 p-6">
            <h3 className="font-display text-lg font-semibold text-ink">
              How VALT&apos;s version differs from the original
            </h3>
            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-ink/80">
              <li>
                <strong>14 of the 17 items are measured from your video</strong> using pose
                estimation instead of a trained human rater. See each item&apos;s exact
                threshold and source on the report page.
              </li>
              <li>
                <strong>3 items are self-reported, not measured:</strong> foot rotation
                (internal and external, at the deepest point of the landing) is a
                transverse-plane motion no single 2D camera can resolve, and
                &ldquo;overall impression&rdquo; is explicitly a holistic rater judgment in
                the original tool, not a formula.
              </li>
              <li>
                <strong>Full coverage needs both camera angles</strong> in one session
                (VALT&apos;s guided capture supports this). A single-view clip only ever
                scores the items valid for that plane.
              </li>
              <li>
                This is a <strong>screening tool, not a diagnosis</strong>, not a trained
                or fitted model, and never a prediction that any individual will or
                won&apos;t be injured.
              </li>
            </ul>
          </div>

          <div className="mt-8 flex flex-wrap gap-3">
            <Button href="/capture" variant="primary">Try a guided capture →</Button>
          </div>
        </div>
      </section>

      {/* ---------- REFERENCES ---------- */}
      <section>
        <div className="mx-auto max-w-4xl px-6 py-16">
          <h2 className="font-display text-lg font-semibold text-ink">References</h2>
          <ol className="mt-4 space-y-3 text-sm leading-relaxed text-muted">
            <li>
              Padua DA, Marshall SW, Boling MC, Thigpen CA, Garrett WE Jr, Beutler AI. The
              Landing Error Scoring System (LESS) Is a Valid and Reliable Clinical
              Assessment Tool of Jump-Landing Biomechanics: The JUMP-ACL Study.{" "}
              <em>Am J Sports Med.</em> 2009;37(10):1996-2002. doi:10.1177/0363546509343200
            </li>
            <li>
              Padua DA, DiStefano LJ, Beutler AI, de la Motte SJ, DiStefano MJ, Marshall SW.
              The Landing Error Scoring System as a Screening Tool for an Anterior Cruciate
              Ligament Injury-Prevention Program in Elite-Youth Soccer Athletes.{" "}
              <em>J Athl Train.</em> 2015;50(6):589-595. doi:10.4085/1062-6050-50.1.10
            </li>
            <li>
              Hewett TE, Myer GD, Ford KR, et al. Biomechanical Measures of Neuromuscular
              Control and Valgus Loading of the Knee Predict Anterior Cruciate Ligament
              Injury Risk in Female Athletes: A Prospective Study.{" "}
              <em>Am J Sports Med.</em> 2005;33(4):492-501. doi:10.1177/0363546504269591
            </li>
            <li>
              Prodromos CC, Han Y, Rogowski J, Joyce B, Shi K. A Meta-analysis of the
              Incidence of Anterior Cruciate Ligament Tears as a Function of Gender, Sport,
              and a Knee Injury-Reduction Regimen. <em>Arthroscopy.</em>{" "}
              2007;23(12):1320-1325.e6. doi:10.1016/j.arthro.2007.07.003
            </li>
            <li>
              Martinez-Calderon J, Infante-Cano M, Matias-Soto J, et al. The Incidence of
              Sport-Related Anterior Cruciate Ligament Injuries: An Overview of Systematic
              Reviews Including 51 Meta-Analyses. <em>J Funct Morphol Kinesiol.</em>{" "}
              2025;10(2):174. doi:10.3390/jfmk10020174
            </li>
            <li>
              Chia L, De Oliveira Silva D, Whalan M, McKay MJ, Sullivan J, Fuller CW, Pappas
              E. Non-contact Anterior Cruciate Ligament Injury Epidemiology in Team-Ball
              Sports: A Systematic Review with Meta-analysis by Sex, Age, Sport,
              Participation Level, and Exposure Type. <em>Sports Medicine.</em>{" "}
              2022;52(10):2447-2467. doi:10.1007/s40279-022-01697-w
            </li>
            <li>
              Paterno MV, Rauh MJ, Schmitt LC, Ford KR, Hewett TE. Incidence of Second ACL
              Injuries 2 Years After Primary ACL Reconstruction and Return to Sport.{" "}
              <em>Am J Sports Med.</em> 2014;42(7):1567-1573. doi:10.1177/0363546514530088
            </li>
            <li>
              Children&apos;s Hospital of Philadelphia. &ldquo;What Are the Odds of Tearing
              Your ACL in the Sports You Play?&rdquo;, a patient-education summary citing
              youth ACL incidence trends from <em>Pediatrics</em> (1994-2013 cohort).
              chop.edu
            </li>
          </ol>
          <p className="mt-6 text-xs leading-relaxed text-muted">
            The remaining screening-score criteria used elsewhere in this app (age, sex,
            sport type, fatigue, prior injury, and the illustrative biomechanical
            thresholds, see the report page&apos;s &ldquo;Risk factor screening&rdquo;
            section) cite additional sources not independently re-verified for this page;
            see{" "}
            <code className="rounded bg-surface px-1 py-0.5">backend/app/risk/scoring.py</code>{" "}
            for that list.
          </p>
        </div>
      </section>
    </>
  );
}
