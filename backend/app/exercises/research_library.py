# ============================================================
# research_library.py — the citations behind every exercise in
# database.py, kept in one place for the same reason risk/less.py and
# risk/scoring.py keep their citations centralized: every claim in this
# app should trace to a real, checkable source, and centralizing them
# makes that traceable at a glance rather than scattered across exercise
# entries.
#
# FOUR PROGRAMS, EACH WITH ITS OWN VALIDATION TRIAL. None of the
# exercises below were invented for this app — every one is drawn
# directly from the cited program's own published manual or protocol
# description, in this app's own words, not copied verbatim.
#
# WHAT THIS APP DOES NOT CLAIM: that any individual exercise, by itself,
# was tested in isolation. These programs were validated as COMPLETE
# ROUTINES (a full warm-up, a full training session). An exercise drawn
# from a validated program inherits that program's evidence context, not
# a standalone efficacy claim of its own — stated once here rather than
# repeated on every exercise entry.
# ============================================================

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgramCitation:
    program_id: str
    program_name: str
    summary: str          # what the program is, in plain language
    citation: str          # full citation of the primary validation trial
    key_finding: str        # the trial's headline result, precisely stated
    source_url: str | None = None


FIFA_11_PLUS = ProgramCitation(
    program_id="fifa_11_plus",
    program_name="FIFA 11+",
    summary=(
        "A complete ~20-minute warm-up developed by FIFA's Medical Assessment "
        "and Research Centre (F-MARC): running exercises, then strength, "
        "plyometric, and balance exercises across increasing difficulty "
        "levels, then more running. Designed to replace a standard warm-up, "
        "performed at least twice a week."
    ),
    citation=(
        "Soligard T, Myklebust G, Steffen K, Holme I, Silvers H, Bizzini M, "
        "Junge A, Dvorak J, Bahr R, Andersen TE. Comprehensive warm-up "
        "programme to prevent injuries in young female footballers: cluster "
        "randomised controlled trial. BMJ. 2008 Dec 9;337:a2469. "
        "doi:10.1136/bmj.a2469"
    ),
    key_finding=(
        "2,540 young female football players across 125 clubs; teams using "
        "the programme had significantly fewer severe injuries and overall "
        "injuries than teams warming up as usual."
    ),
)

FIFA_11_PLUS_KIDS = ProgramCitation(
    program_id="fifa_11_plus_kids",
    program_name="FIFA 11+ Kids",
    summary=(
        "A youth-adapted version of FIFA 11+ for players under 14: seven "
        "exercises across a running game, two jumping drills, a balance/"
        "coordination task, two stability exercises, and a falling-technique "
        "drill, structured in stages of increasing difficulty."
    ),
    citation=(
        "Rössler R, Junge A, Bizzini M, Verhagen E, Chomiak J, aus der "
        "Fünten K, Meyer T, Dvorak J, Lichtenstein E, Beaudouin F, Faude O. "
        "A Multinational Cluster Randomised Controlled Trial to Assess the "
        "Efficacy of '11+ Kids': A Warm-Up Programme to Prevent Injuries in "
        "Children's Football. Sports Med. 2017. doi:10.1007/s40279-017-0834-8"
    ),
    key_finding=(
        "Multinational cluster-randomised trial in children's football; the "
        "programme reduced injury rates versus standard warm-up practice."
    ),
)

PEP_PROGRAM = ProgramCitation(
    program_id="pep_program",
    program_name="PEP Program (Prevent injury, Enhance Performance)",
    summary=(
        "A 15-20 minute soccer-specific session developed by the Santa "
        "Monica Sports Medicine Research Foundation, replacing a standard "
        "warm-up: warm-up jogging, strengthening, plyometrics, and agility "
        "drills, with an explicit emphasis on soft landings and avoiding "
        "inward knee collapse in every exercise."
    ),
    citation=(
        "Mandelbaum BR, Silvers HJ, Watanabe DS, Knarr JF, Thomas SD, "
        "Griffin LY, Kirkendall DT, Garrett W. Effectiveness of a "
        "neuromuscular and proprioceptive training program in preventing "
        "anterior cruciate ligament injuries in female athletes: 2-year "
        "follow-up. Am J Sports Med. 2005 Jul;33(7):1003-1010. "
        "doi:10.1177/0363546504272261"
    ),
    key_finding=(
        "Female collegiate/club soccer players; the intervention group's ACL "
        "injury rate was substantially lower than the control group's over "
        "two seasons of follow-up."
    ),
)

SPORTSMETRICS = ProgramCitation(
    program_id="sportsmetrics",
    program_name="Sportsmetrics",
    summary=(
        "A structured jump-training program (dynamic warm-up, plyometrics, "
        "strengthening, flexibility) developed by Frank Noyes and colleagues "
        "at the Cincinnati Sportsmedicine Research and Education Foundation, "
        "progressing from basic double-leg jumps toward multi-directional "
        "and single-leg landing control."
    ),
    citation=(
        "Hewett TE, Lindenfeld TN, Riccobene JV, Noyes FR. The Effect of "
        "Neuromuscular Training on the Incidence of Knee Injury in Female "
        "Athletes: A Prospective Study. Am J Sports Med. 1999 "
        "Nov-Dec;27(6):699-706. doi:10.1177/03635465990270060301"
    ),
    key_finding=(
        "Trained female athletes sustained serious knee injuries at a "
        "markedly lower rate than untrained female athletes across a "
        "high-school soccer/volleyball/basketball season; the untrained "
        "female rate was also markedly higher than the male comparison group."
    ),
)

ALL_PROGRAMS: list[ProgramCitation] = [
    FIFA_11_PLUS, FIFA_11_PLUS_KIDS, PEP_PROGRAM, SPORTSMETRICS,
]

PROGRAMS_BY_ID: dict[str, ProgramCitation] = {p.program_id: p for p in ALL_PROGRAMS}
