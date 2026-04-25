"""
main.py
=======
Medical Diagnosis Expert System - User Interface & Session Controller

This is the entry point. It provides:
  - A hybrid CLI with visual panels, color coding, and Unicode framing
  - Domain selection menu
  - Grouped input collection with smart skipping (headache=no skips
    headache_location/intensity, etc.)
  - Mandatory-field warning (user-requested enhancement)
  - Three output modes: Standard / Trace / Demo
  - Live demonstration shortcuts via --demo flag

Course:     AIE212 - Knowledge-Based Systems
University: Alamein International University
Instructor: Dr. Essam Abdellatef
Semester:   Spring 2025/2026
"""

import argparse
import os
import sys
import datetime
from typing import Optional

from knowledge_base import DOMAINS, OUTPUT_RULES
from working_memory import WorkingMemory
from inference_engine import InferenceEngine
import explanation as exp
from explanation import Theme, make_box, pad, BOX_WIDTH_DEFAULT, divider, urgency_badge


# =============================================================================
# BANNER
# =============================================================================

ASCII_LOGO = r"""
    __  ___         __ ___             ______
   /  |/  /__  ____/ /|__ \ __  __   _/ ____/
  / /|_/ / _ \/ __  / __/ // / / /  / __/
 / /  / /  __/ /_/ / / __// /_/ /  / /___
/_/  /_/\___/\__,_/ /____/\__,_/  /_____/

     MEDICAL DIAGNOSIS EXPERT SYSTEM
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """Print the startup banner with university credit."""
    clear_screen()
    print()
    print(Theme.TITLE + ASCII_LOGO + Theme.RESET)
    print()
    header_lines = [
        "",
        pad(f"  {Theme.LABEL}Course:{Theme.RESET}      AIE212 - Knowledge-Based Systems", BOX_WIDTH_DEFAULT - 2),
        pad(f"  {Theme.LABEL}University:{Theme.RESET}  Alamein International University", BOX_WIDTH_DEFAULT - 2),
        pad(f"  {Theme.LABEL}Instructor:{Theme.RESET}  Dr. Essam Abdellatef", BOX_WIDTH_DEFAULT - 2),
        pad(f"  {Theme.LABEL}Semester:{Theme.RESET}    Spring 2025/2026", BOX_WIDTH_DEFAULT - 2),
        pad(f"  {Theme.LABEL}Project:{Theme.RESET}     Phase 4 - Implementation", BOX_WIDTH_DEFAULT - 2),
        "",
    ]
    print(make_box(f"{Theme.ACCENT}SESSION INFORMATION{Theme.RESET}", header_lines, style="double"))
    print()


def print_status_bar(domain_display: str, facts_recorded: int):
    """A slim live-status line at the top of the input phase."""
    left = f" Domain: {Theme.ACCENT}{domain_display}{Theme.RESET} "
    right = f" Facts recorded: {Theme.ACCENT}{facts_recorded}{Theme.RESET} "
    sep = Theme.DIM + "│" + Theme.RESET
    print(f"{sep}{left}{sep}{right}{sep}")
    print(divider())


# =============================================================================
# DOMAIN SELECTION MENU
# =============================================================================

# ASCII-style domain icons (cyan) - evokes the dashboard aesthetic
DOMAIN_ICONS = {
    "RESPIRATORY": [
        "    ___      ___    ",
        "  ,'   `.  ,'   `.  ",
        " /       \\/       \\ ",
        " |  LUNGS         | ",
        "  \\     /\\/\\     /  ",
        "   `---'    `---'   ",
    ],
    "GASTROINTESTINAL": [
        "    .--------.      ",
        "   /  STOMACH \\     ",
        "  |   ______   |    ",
        "  |  / GI   \\  |    ",
        "   \\ \\______/ /     ",
        "    `--------'      ",
    ],
    "NEUROLOGICAL": [
        "    __________      ",
        "   /  .--.    \\     ",
        "  |  | BR |    |    ",
        "  |  | AIN |   |    ",
        "   \\ `----'   /     ",
        "    `--------'      ",
    ],
}


def select_domain() -> Optional[str]:
    """Domain selection menu. Returns domain ID or None if cancelled."""
    print(Theme.HEADER + "  STEP 1  │  SELECT PRIMARY COMPLAINT DOMAIN" + Theme.RESET)
    print(divider())
    print()

    domain_ids = list(DOMAINS.keys())

    for i, dom_id in enumerate(domain_ids, 1):
        dom = DOMAINS[dom_id]
        icon = DOMAIN_ICONS.get(dom_id, [""] * 6)
        conditions_summary = ", ".join(dom["conditions"][:3]) + ", ..."
        emergency = dom["emergency_condition"]

        # Render each domain as a compact card
        card_lines = [
            f"  {Theme.TITLE}[{i}]{Theme.RESET}  {Theme.LABEL}{dom['display_name']}{Theme.RESET}",
            f"       {Theme.DIM}6 conditions: {conditions_summary}{Theme.RESET}",
            f"       {Theme.WARN}Emergency: {emergency}{Theme.RESET}",
        ]
        for line in card_lines:
            print(line)
        print()

    print(f"  {Theme.DIM}[q] Quit{Theme.RESET}")
    print()
    print(divider())

    while True:
        try:
            choice = input(f"  {Theme.ACCENT}Enter your choice (1-{len(domain_ids)} or q):{Theme.RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if choice == "q":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(domain_ids):
            return domain_ids[int(choice) - 1]
        print(f"  {Theme.WARN}Invalid choice. Please enter 1-{len(domain_ids)} or q.{Theme.RESET}")


# =============================================================================
# INPUT COLLECTION - grouped questions with smart skipping
# =============================================================================

# Per-domain input groups: (Group title, [(fact_name, human_prompt, type, options_or_range), ...])
# Types: 'bool' -> yes/no/skip, 'enum' -> numbered options, 'numeric' -> number input
# A fact may have a 'depends_on' key (in input_plan) that short-circuits if the
# parent fact is answered 'no' (smart skipping).

RESPIRATORY_INPUT_PLAN = [
    ("PRIMARY SYMPTOMS", [
        ("fever", "Do you have a fever?", "bool", None, None),
        ("cough", "Do you have a cough?", "enum_optional",
         [("dry", "Dry cough"), ("productive", "Productive (with phlegm)"), ("no", "No cough")], None),
        ("runny_nose", "Do you have a runny or blocked nose?", "bool", None, None),
        ("sore_throat", "Do you have a sore throat?", "bool", None, None),
        ("shortness_of_breath", "Do you have shortness of breath?", "bool", None, None),
    ]),
    ("SECONDARY SYMPTOMS", [
        ("body_aches", "Do you have body aches or muscle pain?", "bool", None, None),
        ("fatigue", "Do you feel fatigued or exhausted?", "bool", None, None),
        ("loss_of_smell", "Have you lost your sense of smell?", "bool", None, None),
        ("loss_of_taste", "Have you lost your sense of taste?", "bool", None, None),
        ("chest_tightness", "Do you have chest tightness or chest pain?", "bool", None, None),
    ]),
    ("ONSET & DURATION", [
        ("symptom_duration", "How many days have symptoms lasted?", "numeric", None, (0, 60)),
        ("symptom_onset", "How did symptoms start?", "enum",
         [("sudden", "Suddenly (within hours)"), ("gradual", "Gradually (over days)")], None),
        ("fever_duration", "If fever is present, how many days?", "numeric_optional", None, (0, 30)),
    ]),
    ("OPTIONAL VITALS", [
        ("fever_temp", "Body temperature in Celsius (skip if unknown)", "numeric_optional", None, (35.0, 42.0)),
        ("SpO2", "Oxygen saturation / SpO2 in % (skip if unknown)", "numeric_optional", None, (70, 100)),
    ]),
    ("PATIENT HISTORY", [
        ("influenza_vaccinated", "Have you received the Influenza vaccine this season?", "bool", None, None),
    ]),
]

GASTROINTESTINAL_INPUT_PLAN = [
    ("PRIMARY SYMPTOMS", [
        ("abdominal_pain", "Do you have abdominal pain?", "bool", None, None),
        ("pain_location", "Where is the pain located?", "enum",
         [("upper", "Upper abdomen"), ("central", "Central/around navel"),
          ("lower_right", "Lower-right"), ("lower_left", "Lower-left"), ("none", "No pain / N/A")], None),
        ("pain_onset", "How did the pain start?", "enum",
         [("sudden", "Sudden onset"), ("gradual", "Gradual onset"), ("none", "No pain / N/A")], None),
        ("pain_pattern", "What pattern does the pain follow?", "enum",
         [("constant", "Constant"), ("intermittent", "Comes and goes"),
          ("worse_when_hungry", "Worse when hungry"), ("none", "No pain / N/A")], None),
    ]),
    ("DIGESTIVE SYMPTOMS", [
        ("nausea", "Do you have nausea?", "bool", None, None),
        ("vomiting", "Have you been vomiting?", "bool", None, None),
        ("diarrhea", "Do you have diarrhea?", "bool", None, None),
        ("constipation", "Are you constipated?", "bool", None, None),
        ("loss_of_appetite", "Have you lost your appetite?", "bool", None, None),
    ]),
    ("OTHER SYMPTOMS", [
        ("fever", "Do you have a fever?", "bool", None, None),
        ("heartburn", "Do you have heartburn / burning sensation?", "bool", None, None),
        ("regurgitation", "Do you have acid regurgitation?", "bool", None, None),
        ("bloating", "Do you have bloating or gas?", "bool", None, None),
    ]),
    ("ONSET & CONTEXT", [
        ("symptom_duration", "How many days have symptoms lasted?", "numeric", None, (0, 60)),
        ("symptom_trigger", "Did symptoms start after eating?", "enum",
         [("after_eating_outside", "After eating outside / shared meal"),
          ("after_meals", "After regular meals"),
          ("none", "No specific trigger")], None),
        ("symptom_history", "Is this a recurring pattern?", "enum",
         [("recurring", "Recurring (happened before)"), ("first_time", "First time")], None),
    ]),
    ("OPTIONAL VITALS & HISTORY", [
        ("fever_temp", "Body temperature in Celsius (skip if unknown)", "numeric_optional", None, (35.0, 42.0)),
        ("nsaid_use", "Do you regularly use NSAIDs or aspirin?", "bool_optional", None, None),
        ("prior_appendectomy", "Have you had your appendix removed?", "bool_optional", None, None),
    ]),
]

NEUROLOGICAL_INPUT_PLAN = [
    ("HEADACHE ASSESSMENT", [
        ("headache", "Do you have a headache?", "bool", None, None),
        ("headache_location", "Where is the headache?", "enum",
         [("unilateral", "One side of head"), ("bilateral", "Both sides"), ("none", "No headache / N/A")], None),
        ("headache_onset", "How did the headache start?", "enum",
         [("sudden", "Suddenly (thunderclap)"), ("gradual", "Gradually"), ("none", "No headache / N/A")], None),
    ]),
    ("FAST STROKE SCREENING", [
        ("facial_drooping", "Is one side of your face drooping?", "bool", None, None),
        ("arm_weakness", "Do you have arm or leg weakness?", "bool", None, None),
        ("arm_weakness_side", "If yes, which side?", "enum",
         [("unilateral", "One side only"), ("bilateral", "Both sides"), ("none", "No weakness / N/A")], None),
        ("slurred_speech", "Is your speech slurred?", "bool", None, None),
        ("confused_speech", "Is your speech confused or difficult to understand?", "bool", None, None),
    ]),
    ("OTHER NEUROLOGICAL SIGNS", [
        ("neck_stiffness", "Do you have neck stiffness?", "bool", None, None),
        ("photophobia", "Sensitivity to light or sound?", "bool", None, None),
        ("visual_aura", "Any visual disturbances or aura?", "bool", None, None),
        ("loss_of_consciousness", "Have you lost consciousness?", "bool", None, None),
        ("muscle_jerking", "Any involuntary muscle jerking?", "bool", None, None),
        ("dizziness", "Do you feel dizzy?", "bool", None, None),
        ("balance_loss", "Any loss of balance?", "bool", None, None),
        ("fever", "Do you have a fever?", "bool", None, None),
    ]),
    ("ONSET", [
        ("symptom_onset", "How did symptoms start?", "enum",
         [("sudden", "Suddenly"), ("gradual", "Gradually")], None),
        ("symptom_duration_minutes", "How many minutes since symptom onset?", "numeric", None, (0, 10080)),
    ]),
    ("PATIENT HISTORY (OPTIONAL)", [
        ("migraine_history", "Do you have a history of migraines?", "bool_optional", None, None),
        ("hypertension_history", "Do you have a history of hypertension?", "bool_optional", None, None),
        ("family_history_stroke", "Family history of stroke?", "bool_optional", None, None),
    ]),
]

INPUT_PLANS = {
    "RESPIRATORY": RESPIRATORY_INPUT_PLAN,
    "GASTROINTESTINAL": GASTROINTESTINAL_INPUT_PLAN,
    "NEUROLOGICAL": NEUROLOGICAL_INPUT_PLAN,
}

# Smart-skip: if (parent, value) matches, skip these child fields
SMART_SKIPS = {
    "RESPIRATORY": {
        ("cough", "no"): [],  # cough is itself enum, no children
        ("fever", "no"): ["fever_temp", "fever_duration"],
    },
    "GASTROINTESTINAL": {
        ("abdominal_pain", "no"): ["pain_location", "pain_onset", "pain_pattern"],
        ("fever", "no"): ["fever_temp"],
    },
    "NEUROLOGICAL": {
        ("headache", "no"): ["headache_location", "headache_onset"],
        ("arm_weakness", "no"): ["arm_weakness_side"],
    },
}


def ask_bool(prompt: str, optional: bool = False) -> Optional[str]:
    """Ask a yes/no question. Returns 'yes' / 'no' / None (if skipped)."""
    suffix = " [y/n" + ("/s" if optional else "") + "]: "
    while True:
        try:
            ans = input(f"  {Theme.ACCENT}> {Theme.RESET}{prompt}{suffix}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if ans in ("y", "yes"):
            return "yes"
        if ans in ("n", "no"):
            return "no"
        if optional and ans in ("s", "skip", ""):
            return None
        print(f"    {Theme.WARN}Please answer y or n" + (" or s to skip" if optional else "") + ".{Theme.RESET}")


def ask_enum(prompt: str, options: list, optional: bool = False) -> Optional[str]:
    """Ask a multiple-choice question. Options: [(value, label), ...]."""
    print(f"  {Theme.ACCENT}> {Theme.RESET}{prompt}")
    for i, (val, label) in enumerate(options, 1):
        print(f"      [{i}] {label}")
    if optional:
        print(f"      [s] Skip")
    while True:
        try:
            ans = input(f"    Enter choice: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if optional and ans in ("s", "skip", ""):
            return None
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return options[int(ans) - 1][0]
        print(f"    {Theme.WARN}Please enter 1-{len(options)}" + (" or s.{Theme.RESET}" if optional else ".{Theme.RESET}"))


def ask_numeric(prompt: str, range_tuple: tuple, optional: bool = False) -> Optional[float]:
    """Ask for a number. range_tuple is (min, max)."""
    lo, hi = range_tuple
    suffix = f" [range {lo}-{hi}" + ("/s to skip" if optional else "") + "]: "
    while True:
        try:
            ans = input(f"  {Theme.ACCENT}> {Theme.RESET}{prompt}{suffix}").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return None
        if optional and ans in ("s", "skip", ""):
            return None
        try:
            val = float(ans)
            if lo <= val <= hi:
                # Return int if it's a whole number
                return int(val) if val == int(val) else val
            print(f"    {Theme.WARN}Value must be between {lo} and {hi}.{Theme.RESET}")
        except ValueError:
            print(f"    {Theme.WARN}Please enter a number" + (" or s to skip.{Theme.RESET}" if optional else ".{Theme.RESET}"))


def collect_inputs(domain_id: str, wm: WorkingMemory):
    """
    Grouped input collection with smart skipping.
    """
    plan = INPUT_PLANS[domain_id]
    skips = SMART_SKIPS.get(domain_id, {})
    skipped_fields: set = set()

    facts_recorded = 0

    for group_idx, (group_title, questions) in enumerate(plan, 1):
        print()
        print(Theme.HEADER + f"  GROUP {group_idx}  │  {group_title}" + Theme.RESET)
        print(divider())

        for fact_name, prompt, qtype, options, rng in questions:
            # Smart skip: if a parent answer triggers skipping this field
            if fact_name in skipped_fields:
                print(f"  {Theme.DIM}[skipped: {fact_name} not relevant given earlier answer]{Theme.RESET}")
                continue

            if qtype == "bool":
                value = ask_bool(prompt, optional=False)
                if value is None:
                    wm.flag_missing_mandatory(fact_name)
                    continue
            elif qtype == "bool_optional":
                value = ask_bool(prompt, optional=True)
                if value is None:
                    continue
            elif qtype == "enum":
                value = ask_enum(prompt, options, optional=False)
                if value is None:
                    wm.flag_missing_mandatory(fact_name)
                    continue
            elif qtype == "enum_optional":
                value = ask_enum(prompt, options, optional=True)
                if value is None:
                    continue
            elif qtype == "numeric":
                value = ask_numeric(prompt, rng, optional=False)
                if value is None:
                    wm.flag_missing_mandatory(fact_name)
                    continue
            elif qtype == "numeric_optional":
                value = ask_numeric(prompt, rng, optional=True)
                if value is None:
                    continue
            else:
                continue

            wm.add_patient_fact(fact_name, value)
            facts_recorded += 1

            # Apply smart-skip rules based on this answer
            skip_key = (fact_name, value)
            if skip_key in skips:
                for child in skips[skip_key]:
                    skipped_fields.add(child)

        # Special derivation: fever_duration from fever + symptom_duration
        if (group_title == "ONSET & DURATION" and domain_id == "RESPIRATORY"
                and wm.has_fact("fever") and wm.get_fact("fever").value == "yes"
                and wm.has_fact("symptom_duration") and not wm.has_fact("fever_duration")):
            # If user didn't provide fever_duration explicitly, infer from symptom_duration
            dur = wm.get_fact("symptom_duration").value
            wm.add_patient_fact("fever_duration", dur)
            facts_recorded += 1

    print()
    print(divider())
    print(f"  {Theme.OK}Input collection complete. {facts_recorded} facts recorded.{Theme.RESET}")
    if wm.missing_mandatory:
        print(f"  {Theme.WARN}{len(wm.missing_mandatory)} mandatory field(s) skipped.{Theme.RESET}")
    print()


# =============================================================================
# OUTPUT MODE SELECTION
# =============================================================================

def select_output_mode() -> str:
    """
    Ask the user which output mode they want.
    Returns 'standard' | 'trace' | 'both'.
    """
    print(Theme.HEADER + "  STEP 3  │  SELECT OUTPUT MODE" + Theme.RESET)
    print(divider())
    print()
    print(f"  {Theme.TITLE}[1]{Theme.RESET}  {Theme.LABEL}Standard Diagnosis{Theme.RESET}")
    print(f"       {Theme.DIM}Clean patient-facing output (no technical trace){Theme.RESET}")
    print()
    print(f"  {Theme.TITLE}[2]{Theme.RESET}  {Theme.LABEL}Diagnosis + Full Trace{Theme.RESET}")
    print(f"       {Theme.DIM}Includes WM/CS/Rule/Deductions table (for grading/demo){Theme.RESET}")
    print()
    print(f"  {Theme.TITLE}[3]{Theme.RESET}  {Theme.LABEL}Export .txt file only{Theme.RESET}")
    print(f"       {Theme.DIM}Save full trace to file without terminal noise{Theme.RESET}")
    print()
    print(divider())
    while True:
        try:
            ans = input(f"  {Theme.ACCENT}Enter choice (1-3):{Theme.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            return "standard"
        if ans == "1":
            return "standard"
        if ans == "2":
            return "both"
        if ans == "3":
            return "file"
        print(f"  {Theme.WARN}Please enter 1, 2, or 3.{Theme.RESET}")


# =============================================================================
# DIAGNOSIS WORKFLOW
# =============================================================================

def run_diagnosis_session(domain_id: str, preloaded_facts: Optional[list] = None,
                          output_mode: str = "both", save_trace: bool = True) -> dict:
    """
    Run a full diagnostic session end-to-end.
    If preloaded_facts is provided (for --demo mode), skip input collection.
    """
    dom = DOMAINS[domain_id]
    wm = WorkingMemory(domain_id, dom["conditions"])

    if preloaded_facts is not None:
        for name, val in preloaded_facts:
            wm.add_patient_fact(name, val)
    else:
        collect_inputs(domain_id, wm)

    # Inference phase with spinner
    print(Theme.HEADER + "  STEP 4  │  RUNNING INFERENCE ENGINE" + Theme.RESET)
    print(divider())
    print(f"  {Theme.DIM}Forward Chaining with Lowest Index CR...{Theme.RESET}")

    engine = InferenceEngine(dom["rules"], wm)
    engine.run()

    classification = engine.classify_output()
    engine.finalize_urgency(classification, domain_id)

    print(f"  {Theme.OK}Inference complete. {len(engine.trace)} cycles fired.{Theme.RESET}")
    print()

    # -------------------------------------------------------------------------
    # Render output based on mode
    # -------------------------------------------------------------------------

    if output_mode in ("standard", "both"):
        # Missing-fields warning (if any)
        missing_warn = exp.render_missing_fields_warning(wm)
        if missing_warn:
            print(missing_warn)
            print()

        # Main diagnosis panel
        print(exp.render_diagnosis_panel(classification, wm.urgency, wm, domain_id))
        print()

        # Conflict notices (if any)
        conflict_notice = exp.build_conflict_notices(engine.mixed_sign_conflicts)
        if conflict_notice:
            from explanation import _wrap_text
            wrapped = []
            for line in conflict_notice.split("\n"):
                if not line:
                    wrapped.append("")
                else:
                    wrapped.extend(_wrap_text(line, 74))
            notice_lines = [""] + [pad(f"  {Theme.WARN}{l}{Theme.RESET}", BOX_WIDTH_DEFAULT - 2)
                                    for l in wrapped] + [""]
            print(make_box(f"{Theme.WARN}CONFLICTING EVIDENCE{Theme.RESET}", notice_lines, style="single"))
            print()

        # Ambiguity notice (if relevant)
        ambig = exp.build_ambiguity_notice(classification)
        if ambig:
            from explanation import _wrap_text
            wrapped = []
            for line in ambig.split("\n"):
                if not line:
                    wrapped.append("")
                else:
                    wrapped.extend(_wrap_text(line, 74))
            ambig_lines = [""] + [pad(f"  {l}", BOX_WIDTH_DEFAULT - 2) for l in wrapped] + [""]
            print(make_box(f"{Theme.WARN}AMBIGUOUS OUTPUT{Theme.RESET}", ambig_lines, style="single"))
            print()

        # Ranked differentials
        print(exp.render_differentials_panel(classification))
        print()

        # Patient-facing summary
        summary = exp.build_patient_summary(
            classification, engine.fired_order, dom["rules"], wm.urgency, domain_id
        )
        # Wrap each summary paragraph to fit the box (interior width = 74)
        from explanation import _wrap_text
        summary_wrapped = []
        for line in summary.split("\n"):
            if not line:
                summary_wrapped.append("")
                continue
            # Preserve bullet indentation
            if line.startswith("  •"):
                prefix = "  • "
                content = line[4:].strip()
                wrapped = _wrap_text(content, 70)
                summary_wrapped.append(f"{prefix}{wrapped[0]}")
                for w in wrapped[1:]:
                    summary_wrapped.append(f"    {w}")
            else:
                wrapped = _wrap_text(line, 74)
                summary_wrapped.extend(wrapped)
        summary_lines = [""] + [pad(f"  {l}", BOX_WIDTH_DEFAULT - 2) for l in summary_wrapped] + [""]
        print(make_box(f"{Theme.ACCENT}PATIENT-FACING EXPLANATION{Theme.RESET}", summary_lines, style="round"))
        print()

    if output_mode in ("both",):
        print(Theme.HEADER + "  TECHNICAL DECISION TRACE (WM / CS / Rule / Deductions)" + Theme.RESET)
        print(divider())
        print()
        print(exp.format_trace_table(engine.trace))
        print()

    # Trace file export
    if save_trace or output_mode == "file":
        os.makedirs("traces", exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"traces/trace_{domain_id.lower()}_{ts}.txt"
        exp.write_trace_file(
            filename, domain_id, wm, classification,
            engine.trace, engine.mixed_sign_conflicts,
            engine.fired_order, dom["rules"],
        )
        print(f"  {Theme.OK}Full trace saved to:{Theme.RESET} {Theme.ACCENT}{filename}{Theme.RESET}")
        print()

    return {
        "wm": wm, "engine": engine, "classification": classification,
    }


# =============================================================================
# DEMO SCENARIOS - preloaded Phase 1 test cases for the live demonstration
# =============================================================================

DEMO_SCENARIOS = {
    "stroke": ("NEUROLOGICAL", [
        ("headache", "no"), ("headache_location", "none"), ("headache_onset", "none"),
        ("neck_stiffness", "no"), ("photophobia", "no"), ("visual_aura", "no"),
        ("facial_drooping", "yes"), ("arm_weakness", "yes"), ("arm_weakness_side", "unilateral"),
        ("slurred_speech", "yes"), ("confused_speech", "yes"),
        ("loss_of_consciousness", "no"), ("muscle_jerking", "no"),
        ("dizziness", "no"), ("balance_loss", "no"), ("fever", "no"),
        ("symptom_onset", "sudden"), ("symptom_duration_minutes", 30),
        ("migraine_history", "no"), ("hypertension_history", "yes"),
    ]),
    "cold": ("RESPIRATORY", [
        ("fever", "yes"), ("cough", "dry"), ("runny_nose", "yes"),
        ("sore_throat", "no"), ("shortness_of_breath", "no"),
        ("body_aches", "no"), ("fatigue", "yes"),
        ("loss_of_smell", "no"), ("loss_of_taste", "no"), ("chest_tightness", "no"),
        ("symptom_duration", 3), ("symptom_onset", "gradual"),
        ("fever_temp", 37.8), ("influenza_vaccinated", "yes"),
    ]),
    "flu_vaccinated": ("RESPIRATORY", [
        # Influenza symptoms + vaccinated -> triggers the mixed-sign conflict
        ("fever", "yes"), ("cough", "dry"), ("runny_nose", "no"),
        ("sore_throat", "no"), ("shortness_of_breath", "no"),
        ("body_aches", "yes"), ("fatigue", "yes"),
        ("loss_of_smell", "no"), ("loss_of_taste", "no"), ("chest_tightness", "no"),
        ("symptom_duration", 2), ("symptom_onset", "sudden"),
        ("fever_temp", 39.0), ("influenza_vaccinated", "yes"),
    ]),
    "pneumonia": ("RESPIRATORY", [
        ("fever", "yes"), ("cough", "productive"), ("runny_nose", "no"),
        ("sore_throat", "no"), ("shortness_of_breath", "yes"),
        ("body_aches", "no"), ("fatigue", "yes"),
        ("loss_of_smell", "no"), ("loss_of_taste", "no"), ("chest_tightness", "yes"),
        ("symptom_duration", 6), ("symptom_onset", "gradual"),
        ("fever_temp", 39.4), ("SpO2", 91), ("fever_duration", 6),
        ("influenza_vaccinated", "no"),
    ]),
    "appendicitis": ("GASTROINTESTINAL", [
        ("abdominal_pain", "yes"), ("pain_location", "lower_right"),
        ("pain_onset", "sudden"), ("pain_pattern", "constant"),
        ("nausea", "yes"), ("vomiting", "no"), ("diarrhea", "no"),
        ("constipation", "no"), ("loss_of_appetite", "yes"),
        ("fever", "yes"), ("heartburn", "no"), ("regurgitation", "no"),
        ("bloating", "no"), ("symptom_duration", 1),
        ("symptom_trigger", "none"), ("symptom_history", "first_time"),
        ("fever_temp", 38.6), ("prior_appendectomy", "no"),
    ]),
    "food_poisoning": ("GASTROINTESTINAL", [
        ("abdominal_pain", "yes"), ("pain_location", "central"),
        ("pain_onset", "gradual"), ("pain_pattern", "intermittent"),
        ("nausea", "yes"), ("vomiting", "yes"), ("diarrhea", "yes"),
        ("constipation", "no"), ("loss_of_appetite", "yes"),
        ("fever", "yes"), ("heartburn", "no"), ("regurgitation", "no"),
        ("bloating", "yes"), ("symptom_duration", 2),
        ("symptom_trigger", "after_eating_outside"),
        ("symptom_history", "first_time"),
    ]),
    "migraine": ("NEUROLOGICAL", [
        ("headache", "yes"), ("headache_location", "unilateral"),
        ("headache_onset", "gradual"),
        ("neck_stiffness", "no"), ("photophobia", "yes"), ("visual_aura", "yes"),
        ("facial_drooping", "no"), ("arm_weakness", "no"),
        ("arm_weakness_side", "none"), ("slurred_speech", "no"),
        ("confused_speech", "no"), ("loss_of_consciousness", "no"),
        ("muscle_jerking", "no"), ("dizziness", "no"), ("balance_loss", "no"),
        ("fever", "no"), ("symptom_onset", "gradual"),
        ("symptom_duration_minutes", 240),
        ("migraine_history", "yes"), ("hypertension_history", "no"),
    ]),
}


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Medical Diagnosis Expert System (AIE212 Phase 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Interactive mode
  python main.py --demo stroke          # Run the Stroke live-demo scenario
  python main.py --demo appendicitis    # GI emergency scenario
  python main.py --demo flu_vaccinated  # Demonstrate mixed-sign conflict

Available demo scenarios:  stroke, cold, flu_vaccinated, pneumonia,
                            appendicitis, food_poisoning, migraine
""",
    )
    parser.add_argument("--demo", type=str, default=None,
                        help="Run a pre-loaded demo scenario")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save trace .txt file")
    parser.add_argument("--trace", action="store_true",
                        help="Force trace mode output (equivalent to choice 2)")
    args = parser.parse_args()

    print_banner()

    if args.demo:
        if args.demo not in DEMO_SCENARIOS:
            print(f"{Theme.WARN}Unknown demo scenario: {args.demo}{Theme.RESET}")
            print(f"{Theme.DIM}Available: {', '.join(DEMO_SCENARIOS)}{Theme.RESET}")
            sys.exit(1)
        domain_id, facts = DEMO_SCENARIOS[args.demo]
        print(Theme.HEADER + f"  DEMO MODE  │  Scenario: {args.demo}" + Theme.RESET)
        print(f"  {Theme.DIM}Loading preloaded facts into {DOMAINS[domain_id]['display_name']} domain...{Theme.RESET}")
        print()
        run_diagnosis_session(
            domain_id,
            preloaded_facts=facts,
            output_mode="both",
            save_trace=not args.no_save,
        )
        return

    # Interactive mode
    domain_id = select_domain()
    if domain_id is None:
        print(f"  {Theme.DIM}Session cancelled.{Theme.RESET}")
        return

    print()
    print(Theme.HEADER + f"  STEP 2  │  INPUT COLLECTION - {DOMAINS[domain_id]['display_name']}" + Theme.RESET)
    print(divider())
    print(f"  {Theme.DIM}Answer each question. Press 's' or Enter on optional items to skip.{Theme.RESET}")
    print()

    # Temporary WM to collect inputs; will become the real WM
    # (we already reuse the real WM inside run_diagnosis_session)
    # So here we collect the mode first, then pass along
    output_mode = "both" if args.trace else select_output_mode()

    run_diagnosis_session(
        domain_id,
        preloaded_facts=None,
        output_mode=output_mode,
        save_trace=not args.no_save,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"  {Theme.DIM}Session interrupted. Goodbye.{Theme.RESET}")
        sys.exit(0)
