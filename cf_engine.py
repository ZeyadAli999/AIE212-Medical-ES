"""
cf_engine.py
============
Medical Diagnosis Expert System - Certainty Factor Engine

Implements CF arithmetic exactly as taught in Dr. Essam's Lecture 4.
"""


def evidence_and(*cfs: float) -> float:
    return min(cfs)


def evidence_or(*cfs: float) -> float:
    return max(cfs)


def evidence_not(cf: float) -> float:
    return -cf


def rule_contribution(evidence_cf: float, rule_weight: float) -> float:
    return evidence_cf * rule_weight


def combine(cf1: float, cf2: float) -> float:
    """
    Combine two CF contributions via the three-case formula (Lecture 4 p.9).
    """
    if cf1 == 0.0:
        return cf2
    if cf2 == 0.0:
        return cf1
    if cf1 > 0 and cf2 > 0:
        return cf1 + cf2 * (1 - cf1)
    if cf1 < 0 and cf2 < 0:
        return cf1 + cf2 * (1 + cf1)
    denom = 1 - min(abs(cf1), abs(cf2))
    if denom == 0:
        return 0.0
    return (cf1 + cf2) / denom


def combine_many(*cfs: float) -> float:
    if not cfs:
        return 0.0
    result = cfs[0]
    for cf in cfs[1:]:
        result = combine(result, cf)
    return result


def format_evidence_trace(operator: str, values: list, result: float) -> str:
    vals = ", ".join(f"{v:.2f}" for v in values)
    return f"{operator}({vals}) = {result:.2f}"


def format_contribution_trace(evidence_cf: float, rule_weight: float, contribution: float) -> str:
    return f"{evidence_cf:.2f} * {rule_weight:+.2f} = {contribution:+.3f}"


def format_combine_trace(cf1: float, cf2: float, combined: float) -> str:
    """
    Render a combining calculation using Dr. Essam's lecture-board notation.
    Both-positive case: CF1 + CF2 - (CF1 * CF2) (Lecture 4 p.10, p.12)
    """
    if cf1 > 0 and cf2 > 0:
        prod = cf1 * cf2
        return f"{cf1:+.3f} + {cf2:+.3f} - ({cf1:.3f} * {cf2:.3f}) = {cf1 + cf2:.3f} - {prod:.3f} = {combined:+.3f}"
    if cf1 < 0 and cf2 < 0:
        prod = cf1 * cf2
        return f"{cf1:+.3f} + ({cf2:+.3f}) + ({cf1:.3f} * {cf2:.3f}) = {cf1 + cf2:.3f} + {prod:.3f} = {combined:+.3f}"
    denom = 1 - min(abs(cf1), abs(cf2))
    return (f"({cf1:+.3f} + ({cf2:+.3f})) / (1 - min(|{cf1:.3f}|, |{cf2:.3f}|)) "
            f"= {cf1 + cf2:+.3f} / {denom:.3f} = {combined:+.3f}")
