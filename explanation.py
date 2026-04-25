"""
explanation.py
==============
Medical Diagnosis Expert System - Explanation Module

Produces two distinct outputs for every session (Phase 3 Section 6):
  1. Patient-facing plain-language summary using each rule's rationale field
  2. Technical WM/CS/Rule/Deductions trace in Dr. Essam's Lecture 5 format

Also produces:
  - Mixed-sign conflict callouts (Phase 3 Section 6.3)
  - Ambiguous-output notices (Phase 3 Section 6.4)
  - Missing-mandatory-field warnings (user-requested enhancement)
  - Plain .txt file export of the full trace (for submission/grading)
"""

import datetime
from typing import Optional

from knowledge_base import DOMAINS, SUGGESTED_ACTIONS


# =============================================================================
# COLOR SUPPORT - uses colorama if available, degrades gracefully to plain text
# =============================================================================

try:
    from colorama import Fore, Back, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    class _Stub:
        def __getattr__(self, _): return ""
    Fore = _Stub()
    Back = _Stub()
    Style = _Stub()


# Theme palette - navy/cyan aesthetic, inspired by modern medical dashboards
class Theme:
    """Color theme matching the navy + cyan medical dashboard aesthetic."""
    TITLE     = Fore.CYAN + Style.BRIGHT
    HEADER    = Fore.BLUE + Style.BRIGHT
    ACCENT    = Fore.CYAN
    DIM       = Style.DIM
    RESET     = Style.RESET_ALL
    OK        = Fore.GREEN + Style.BRIGHT
    WARN      = Fore.YELLOW + Style.BRIGHT
    DANGER    = Fore.RED + Style.BRIGHT
    EMERGENCY = Fore.WHITE + Back.RED + Style.BRIGHT
    HIGH      = Fore.BLACK + Back.YELLOW + Style.BRIGHT
    MODERATE  = Fore.BLACK + Back.CYAN
    LOW       = Fore.BLACK + Back.GREEN
    BAR_FILL  = Fore.CYAN
    BAR_NEG   = Fore.RED
    LABEL     = Fore.WHITE + Style.BRIGHT


# =============================================================================
# BOX-DRAWING PRIMITIVES
# =============================================================================

BOX_WIDTH_DEFAULT = 78

def strip_ansi(s: str) -> str:
    """Remove ANSI colour codes so width calculations work correctly."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def visible_len(s: str) -> int:
    return len(strip_ansi(s))


def pad(s: str, width: int, align: str = "left") -> str:
    """Pad a (possibly coloured) string to a given visible width."""
    extra = width - visible_len(s)
    if extra <= 0:
        return s
    if align == "center":
        left = extra // 2
        right = extra - left
        return " " * left + s + " " * right
    if align == "right":
        return " " * extra + s
    return s + " " * extra


def make_box(title: str, lines: list, width: int = BOX_WIDTH_DEFAULT, style: str = "double") -> str:
    """
    Build a box-drawing frame around a list of text lines.

    style='double' -> ╔═╗ / ║ / ╚═╝
    style='single' -> ┌─┐ / │ / └─┘
    style='round'  -> ╭─╮ / │ / ╰─╯
    """
    chars = {
        "double": ("╔", "╗", "╚", "╝", "║", "═"),
        "single": ("┌", "┐", "└", "┘", "│", "─"),
        "round":  ("╭", "╮", "╰", "╯", "│", "─"),
    }[style]
    tl, tr, bl, br, vert, horiz = chars

    inner_width = width - 2
    out = []

    # Title row
    if title:
        title_str = f" {title} "
        title_pad = inner_width - visible_len(title_str)
        left_pad = 2
        right_pad = title_pad - left_pad
        top = f"{tl}{horiz * left_pad}{title_str}{horiz * right_pad}{tr}"
    else:
        top = f"{tl}{horiz * inner_width}{tr}"
    out.append(top)

    # Body rows
    for line in lines:
        if line == "---":
            # Separator
            out.append(f"{vert}{horiz * inner_width}{vert}")
        else:
            padded = pad(line, inner_width)
            out.append(f"{vert}{padded}{vert}")

    # Bottom
    out.append(f"{bl}{horiz * inner_width}{br}")
    return "\n".join(out)


def divider(width: int = BOX_WIDTH_DEFAULT, char: str = "─") -> str:
    return Theme.DIM + (char * width) + Theme.RESET


# =============================================================================
# URGENCY BADGE
# =============================================================================

def urgency_badge(level: str) -> str:
    """Return a coloured urgency badge string (fixed-width for alignment)."""
    label = f" {level} "
    if level == "EMERGENCY":
        return Theme.EMERGENCY + label + Theme.RESET
    if level == "HIGH":
        return Theme.HIGH + label + Theme.RESET
    if level == "MODERATE":
        return Theme.MODERATE + label + Theme.RESET
    return Theme.LOW + label + Theme.RESET


# =============================================================================
# CF SPARK BAR - text-based visualization of CF score
# =============================================================================

def cf_bar(cf: float, width: int = 20) -> str:
    """
    Render a horizontal bar for a CF value in [-1, +1].
    Positive CFs fill right in cyan; negative CFs fill left in red.
    """
    cf = max(-1.0, min(1.0, cf))
    half = width // 2
    bar = [" "] * width
    zero = half
    bar[zero] = "│"

    if cf >= 0:
        n = int(round(cf * (width - zero - 1)))
        colour = Theme.BAR_FILL
        for i in range(zero + 1, zero + 1 + n):
            if i < width:
                bar[i] = "█"
        s = "".join(bar[:zero]) + "│" + colour + "".join(bar[zero + 1:]) + Theme.RESET
    else:
        n = int(round(abs(cf) * zero))
        colour = Theme.BAR_NEG
        for i in range(zero - 1, zero - 1 - n, -1):
            if i >= 0:
                bar[i] = "█"
        s = colour + "".join(bar[:zero]) + Theme.RESET + "│" + "".join(bar[zero + 1:])
    return s


# =============================================================================
# PATIENT-FACING PLAIN-LANGUAGE SUMMARY
# =============================================================================

def build_patient_summary(classification: dict, fired_rules: list, rules: list,
                          urgency: str, domain_id: str) -> str:
    """
    Assemble the patient-facing summary from Phase 3 Section 6.1.
    Uses each fired rule's rationale field to build 2-3 plain-language
    sentences, selecting the top-contributing rules.
    """
    lines = []

    primary = classification.get("primary")
    primary_cf = classification.get("primary_cf")

    # Opening line
    if classification["scenario"] == "low_confidence":
        lines.append(
            "Based on your reported symptoms, the system cannot confidently "
            "identify a single primary condition. Further evaluation by a "
            "physician is recommended."
        )
    elif classification["scenario"] == "differential_pair":
        diffs = classification["differentials"]
        names = " and ".join(n for n, _ in diffs[:2])
        lines.append(
            f"Your symptoms point to two possible conditions with similar "
            f"likelihood: {names}. A physician should determine which is "
            f"correct based on additional clinical examination."
        )
    elif classification["scenario"] == "unranked_differential":
        diffs = classification["differentials"]
        names = ", ".join(n for n, _ in diffs)
        lines.append(
            f"Your symptoms could match multiple conditions "
            f"({names}) with similar likelihood. Physician evaluation is "
            f"required to narrow down the diagnosis."
        )
    else:  # standard_primary
        conf_pct = int(round(primary_cf * 100))
        lines.append(
            f"Based on your reported symptoms, the most likely condition is "
            f"{primary} with a confidence score of {conf_pct}%."
        )

    # Reasoning from fired rules (pick 2-3 highest-contribution CONDITION_CF rules)
    if primary:
        supporting = []
        rule_by_id = {r.rule_id: r for r in rules}
        for rid in fired_rules:
            r = rule_by_id.get(rid)
            if r and r.conclusion_type == "CONDITION_CF" and r.conclusion_target == primary and r.cf_weight > 0:
                supporting.append(r)
        supporting = supporting[:3]
        if supporting:
            lines.append("")
            lines.append("The system reached this conclusion because:")
            for r in supporting:
                lines.append(f"  • {r.rationale}")

    # Urgency and suggested action
    action = SUGGESTED_ACTIONS.get(domain_id, {}).get(urgency, "")
    lines.append("")
    lines.append(f"Your urgency level is: {urgency}")
    if action:
        lines.append(f"Recommended action: {action}")

    return "\n".join(lines)


# =============================================================================
# CONFLICTING-EVIDENCE NOTICE (Phase 3 Section 6.3)
# =============================================================================

def build_conflict_notices(mixed_sign_conflicts: list) -> Optional[str]:
    if not mixed_sign_conflicts:
        return None
    lines = []
    for c in mixed_sign_conflicts:
        lines.append(f"CONFLICTING EVIDENCE DETECTED for {c['condition']}:")
        lines.append(f"  Prior accumulated CF   = {c['prev_cf']:+.3f}")
        lines.append(f"  New contribution       = {c['contribution']:+.3f}  (from {c['rule_id']})")
        lines.append(f"  Combined via mixed-sign formula = {c['combined']:+.3f}")
        delta = c['combined'] - c['prev_cf']
        direction = "reduced" if delta < 0 else "increased"
        lines.append(
            f"  Confidence {direction} from {c['prev_cf']:+.3f} to {c['combined']:+.3f}. "
            f"The conflict is recorded below in the decision trace."
        )
        lines.append("")
    return "\n".join(lines).rstrip()


# =============================================================================
# AMBIGUOUS-OUTPUT NOTICE (Phase 3 Section 6.4)
# =============================================================================

def build_ambiguity_notice(classification: dict) -> Optional[str]:
    scenario = classification["scenario"]
    if scenario == "standard_primary":
        return None

    header = "AMBIGUOUS OUTPUT — no primary diagnosis committed."
    body_lines = [header, ""]

    if scenario == "low_confidence":
        body_lines.append(
            "Top CF score is below 0.20. The following conditions were "
            "considered but no single condition achieved sufficient confidence:"
        )
    elif scenario == "differential_pair":
        body_lines.append(
            "Two conditions are within 0.10 CF of each other and cannot be "
            "prioritised on current evidence:"
        )
    else:  # unranked_differential
        body_lines.append(
            "Three or more conditions are within 0.10 CF of the top score. "
            "The evidence is insufficient to prioritise among them:"
        )

    body_lines.append("")
    for name, cf in classification["all_ranked"]:
        if cf > 0 or cf < 0:
            body_lines.append(f"  • {name}: CF = {cf:+.3f}")

    body_lines.append("")
    body_lines.append(
        "This may indicate an incomplete symptom profile, an atypical "
        "presentation, or a condition outside the system's knowledge base. "
        "Direct physician evaluation is required."
    )
    return "\n".join(body_lines)


# =============================================================================
# TECHNICAL DECISION TRACE - WM / CS / Rule / Deductions table
# =============================================================================

def _wrap_text(text: str, width: int) -> list:
    """Wrap text to lines of `width` characters, splitting on whitespace."""
    out = []
    for paragraph in text.split("\n"):
        if not paragraph:
            out.append("")
            continue
        words = paragraph.split(" ")
        line = ""
        for w in words:
            test = w if not line else line + " " + w
            if len(test) <= width:
                line = test
            else:
                if line:
                    out.append(line)
                # Word longer than width - hard-split
                while len(w) > width:
                    out.append(w[:width])
                    w = w[width:]
                line = w
        if line:
            out.append(line)
    return out


def format_trace_table(trace: list, color: bool = True) -> str:
    """
    Render the full cycle-by-cycle trace as a WM/CS/Rule/Deductions table
    using box-drawing characters, mirroring Dr. Essam's lecture format.

    Column widths (total 78 wide):
      Cycle     : 5
      WM        : 14
      CS        : 18
      Rule      : 10
      Deduction : 27
    """
    # Column widths tuned so sum + 6 vertical separators = 78 (BOX_WIDTH_DEFAULT)
    col_cycle, col_wm, col_cs, col_rule, col_ded = 4, 13, 17, 13, 25

    def row(cells: list, is_header: bool = False) -> list:
        """Build rows; each cell is wrapped individually, rows expand to max cell height."""
        widths = [col_cycle, col_wm, col_cs, col_rule, col_ded]
        wrapped = [_wrap_text(cells[i], widths[i]) for i in range(5)]
        max_lines = max(len(w) for w in wrapped)
        # Pad each wrapped block to max_lines
        for w in wrapped:
            while len(w) < max_lines:
                w.append("")
        lines = []
        for i in range(max_lines):
            cell_strs = []
            for col_i in range(5):
                c = wrapped[col_i][i]
                if is_header:
                    c = Theme.HEADER + c + Theme.RESET if color else c
                cell_strs.append(pad(c, widths[col_i]))
            lines.append("│" + "│".join(cell_strs) + "│")
        return lines

    def border(left, mid, right, fill="─"):
        return left + fill * col_cycle + mid + fill * col_wm + mid + fill * col_cs + mid + fill * col_rule + mid + fill * col_ded + right

    out = []
    out.append(border("┌", "┬", "┐"))
    out.extend(row(["Cyc.", "WM", "CS", "Rule", "Deductions + CF Arithmetic"], is_header=True))
    out.append(border("├", "┼", "┤", "═"))

    for rec in trace:
        # CS cell: one rule ref per line
        cs_text = "\n".join(r[1] for r in rec.conflict_set) if rec.conflict_set else "(empty)"

        # Deductions cell: multi-line already
        ded_text = rec.deduction_text

        out.extend(row([
            str(rec.cycle_num),
            rec.wm_snapshot,
            cs_text,
            rec.fired_rule_refs,
            ded_text,
        ]))
        out.append(border("├", "┼", "┤"))

    # Final halt row
    out[-1] = border("├", "┼", "┤", "═")
    out.extend(row([
        "END",
        "—",
        "(empty)",
        "STOP",
        "Conflict Set empty. Session complete.",
    ]))
    out.append(border("└", "┴", "┘"))
    return "\n".join(out)


# =============================================================================
# FINAL OUTPUT PANEL - primary diagnosis card, differentials, urgency
# =============================================================================

def render_diagnosis_panel(classification: dict, urgency: str, wm, domain_id: str) -> str:
    """
    Render the main result panel: the 'hero' output the patient/grader sees first.
    """
    scenario = classification["scenario"]

    if scenario == "standard_primary":
        title = f"{Theme.TITLE}PRIMARY DIAGNOSIS{Theme.RESET}"
        primary = classification["primary"]
        cf = classification["primary_cf"]
        conf_pct = int(round(cf * 100))

        lines = [
            "",
            pad(f"  {Theme.LABEL}Condition{Theme.RESET}   :  {Theme.ACCENT}{primary}{Theme.RESET}", BOX_WIDTH_DEFAULT - 2),
            pad(f"  {Theme.LABEL}Confidence{Theme.RESET}  :  {cf_bar(cf, 30)}  {cf:+.3f} ({conf_pct}%)", BOX_WIDTH_DEFAULT - 2),
            pad(f"  {Theme.LABEL}Urgency{Theme.RESET}     :  {urgency_badge(urgency)}", BOX_WIDTH_DEFAULT - 2),
            "",
        ]
        return make_box(title, lines, style="double")

    elif scenario in ("differential_pair", "unranked_differential"):
        title = f"{Theme.WARN}AMBIGUOUS DIAGNOSIS - DIFFERENTIAL{Theme.RESET}"
        diffs = classification["differentials"]
        lines = [
            "",
            pad(f"  {Theme.LABEL}Candidates within 0.10 CF:{Theme.RESET}", BOX_WIDTH_DEFAULT - 2),
        ]
        for name, cf in diffs:
            conf_pct = int(round(cf * 100))
            lines.append(pad(
                f"    • {Theme.ACCENT}{name:20s}{Theme.RESET}  {cf_bar(cf, 20)}  {cf:+.3f} ({conf_pct}%)",
                BOX_WIDTH_DEFAULT - 2,
            ))
        lines.append("")
        lines.append(pad(f"  {Theme.LABEL}Urgency{Theme.RESET}     :  {urgency_badge(urgency)}", BOX_WIDTH_DEFAULT - 2))
        lines.append("")
        return make_box(title, lines, style="double")

    else:  # low_confidence
        title = f"{Theme.WARN}LOW CONFIDENCE - NO PRIMARY COMMITTED{Theme.RESET}"
        top = classification["all_ranked"][0] if classification["all_ranked"] else ("—", 0.0)
        lines = [
            "",
            pad(f"  {Theme.LABEL}Top candidate{Theme.RESET}  :  {top[0]} (CF = {top[1]:+.3f})", BOX_WIDTH_DEFAULT - 2),
            pad(f"  {Theme.LABEL}Threshold{Theme.RESET}      :  0.20 - not met", BOX_WIDTH_DEFAULT - 2),
            pad(f"  {Theme.LABEL}Urgency{Theme.RESET}        :  {urgency_badge(urgency)}", BOX_WIDTH_DEFAULT - 2),
            "",
            pad(f"  {Theme.WARN}Physician consultation required.{Theme.RESET}", BOX_WIDTH_DEFAULT - 2),
            "",
        ]
        return make_box(title, lines, style="double")


def render_differentials_panel(classification: dict) -> str:
    """Show the full ranked CF list for all conditions (mini panel)."""
    ranked = classification["all_ranked"]
    lines = [""]
    for name, cf in ranked:
        conf_pct = int(round(cf * 100))
        label = f"  {name:20s}"
        bar = cf_bar(cf, 20)
        lines.append(pad(f"{label}  {bar}  {cf:+.3f} ({conf_pct:+d}%)", BOX_WIDTH_DEFAULT - 2))
    lines.append("")
    return make_box(f"{Theme.ACCENT}ALL CONDITIONS - RANKED{Theme.RESET}", lines, style="single")


# =============================================================================
# MISSING-MANDATORY-FIELDS WARNING
# =============================================================================

def render_missing_fields_warning(wm) -> Optional[str]:
    missing = wm.missing_mandatory
    if not missing:
        return None
    lines = [""]
    lines.append(pad(
        f"  {Theme.WARN}{len(missing)} mandatory field(s) were not answered.{Theme.RESET}",
        BOX_WIDTH_DEFAULT - 2,
    ))
    lines.append(pad(f"  {Theme.DIM}This may reduce diagnostic confidence.{Theme.RESET}", BOX_WIDTH_DEFAULT - 2))
    lines.append(pad(f"  {Theme.DIM}Skipped fields:{Theme.RESET}", BOX_WIDTH_DEFAULT - 2))
    # Show in groups of 3
    for i in range(0, len(missing), 3):
        group = "  ".join(missing[i:i + 3])
        lines.append(pad(f"    {Theme.DIM}{group}{Theme.RESET}", BOX_WIDTH_DEFAULT - 2))
    lines.append("")
    return make_box(f"{Theme.WARN}MISSING INPUT NOTICE{Theme.RESET}", lines, style="round")


# =============================================================================
# TRACE FILE EXPORT (plain text, no colors)
# =============================================================================

def write_trace_file(path: str, domain_id: str, wm, classification: dict,
                     trace: list, mixed_sign_conflicts: list, fired_rules: list,
                     rules: list) -> str:
    """
    Write a plain-text decision trace file suitable for inclusion in the
    Phase 4 submission. Contains everything that the terminal showed, with
    ANSI codes stripped.
    """
    dom = DOMAINS[domain_id]
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("=" * 78)
    lines.append("MEDICAL DIAGNOSIS EXPERT SYSTEM - DECISION TRACE")
    lines.append("AIE212 Knowledge-Based Systems | Alamein International University")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Domain:     {dom['display_name']}")
    lines.append(f"Timestamp:  {timestamp}")
    lines.append(f"Primary:    {classification.get('primary') or '—'}")
    if classification.get("primary_cf") is not None:
        lines.append(f"CF score:   {classification['primary_cf']:+.4f}")
    lines.append(f"Urgency:    {wm.urgency}")
    lines.append(f"Scenario:   {classification['scenario']}")
    lines.append("")

    lines.append("-" * 78)
    lines.append("INITIAL WORKING MEMORY (patient facts, all CF = 1.0)")
    lines.append("-" * 78)
    for f in wm.fact_log:
        if f.source == "PATIENT_INPUT":
            lines.append(f"  {f.fact_id:>4s}  {f.name:30s} = {str(f.value):15s} (CF = {f.cf:+.2f})")
    lines.append("")

    lines.append("-" * 78)
    lines.append("INFERENCE TRACE: WM | CS | RULE | DEDUCTIONS")
    lines.append("-" * 78)
    lines.append("")
    lines.append(strip_ansi(format_trace_table(trace, color=False)))
    lines.append("")

    lines.append("-" * 78)
    lines.append("DERIVED FACTS (intermediate conclusions with computed CFs)")
    lines.append("-" * 78)
    for f in wm.fact_log:
        if f.source == "DERIVED":
            lines.append(f"  {f.fact_id:>4s}  {f.name:30s} (CF = {f.cf:+.3f} from {f.origin})")
    lines.append("")

    lines.append("-" * 78)
    lines.append("FINAL CONDITION CFs (ranked)")
    lines.append("-" * 78)
    for name, cf in classification["all_ranked"]:
        lines.append(f"  {name:25s}  CF = {cf:+.4f}")
    lines.append("")

    if mixed_sign_conflicts:
        lines.append("-" * 78)
        lines.append("MIXED-SIGN CONFLICTS (Type 2)")
        lines.append("-" * 78)
        lines.append(strip_ansi(build_conflict_notices(mixed_sign_conflicts)))
        lines.append("")

    lines.append("-" * 78)
    lines.append("URGENCY DETERMINATION")
    lines.append("-" * 78)
    lines.append(f"  Baseline from primary diagnosis : (Stage 1)")
    lines.append(f"  Emergency override              : {wm.urgency_origin or 'none'}")
    lines.append(f"  Final urgency                   : {wm.urgency}")
    lines.append("")

    lines.append("-" * 78)
    lines.append("PATIENT-FACING EXPLANATION")
    lines.append("-" * 78)
    lines.append(build_patient_summary(classification, fired_rules, rules, wm.urgency, domain_id))
    lines.append("")
    lines.append("=" * 78)
    lines.append("END OF TRACE")
    lines.append("=" * 78)

    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path
