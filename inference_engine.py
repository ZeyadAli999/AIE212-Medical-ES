"""
inference_engine.py
===================
Medical Diagnosis Expert System - Inference Engine

Implements the Match-Select-Fire cycle using:
  - Forward Chaining (Phase 2 Section 4.1)
  - Lowest Index conflict resolution (Phase 2 Section 5.1)
  - Monotonic reasoning
"""

from dataclasses import dataclass, field
from typing import Optional

from knowledge_base import Rule, OUTPUT_RULES
from working_memory import WorkingMemory
import cf_engine


@dataclass
class CycleRecord:
    """One cycle of the inference loop, captured for the trace table."""
    cycle_num: int
    wm_snapshot: str
    conflict_set: list
    fired_rule_id: str
    fired_rule_refs: str
    selection_reason: str
    deduction_text: str
    conclusion_type: str
    conclusion_target: str
    evidence_cf: float
    rule_weight: float
    contribution: float
    combined_before: Optional[float] = None
    combined_after: Optional[float] = None
    was_combined: bool = False
    new_fact_id: Optional[str] = None


class InferenceEngine:
    def __init__(self, rules: list, wm: WorkingMemory):
        self.rules = rules
        self.wm = wm
        self.trace: list = []
        self.fired_rules: set = set()
        self.fired_order: list = []
        self.mixed_sign_conflicts: list = []

    def _match(self) -> list:
        cs = []
        wm_dict = self.wm.as_dict()
        for rule in self.rules:
            if rule.rule_id in self.fired_rules:
                continue
            try:
                if rule.condition(wm_dict):
                    cs.append(rule)
            except (KeyError, TypeError):
                pass
        return cs

    def _select(self, conflict_set: list) -> Rule:
        return min(conflict_set, key=lambda r: r.priority)

    def _fire(self, rule: Rule, cycle_num: int, cs_before: list):
        wm_dict = self.wm.as_dict()
        evidence = rule.evidence_cf(wm_dict)
        contribution = cf_engine.rule_contribution(evidence, rule.cf_weight)

        deduction_lines = []
        new_fact_id = None
        combined_before = combined_after = None
        was_combined = False

        arith_prefix = self._build_arith_prefix(rule, wm_dict, evidence)
        deduction_lines.append(f"CF_rule = {arith_prefix} * {rule.cf_weight:+.2f} = {contribution:+.3f}")

        if rule.conclusion_type == "INTERMEDIATE_FACT":
            new_fact_id = self.wm.add_derived_fact(
                name=rule.conclusion_target, value=True,
                cf=contribution, origin_rule=rule.rule_id,
            )
            deduction_lines.insert(
                0, f"{new_fact_id} -> {rule.conclusion_target} (derived, CF = {contribution:+.3f})",
            )

        elif rule.conclusion_type == "CONDITION_CF":
            condition = rule.conclusion_target
            prev_cf = self.wm.get_condition_cf(condition)
            combined_before = prev_cf

            if prev_cf == 0.0:
                new_cf = contribution
                deduction_lines.append(
                    f"CF({condition}) was 0.0 -> initialized to {new_cf:+.3f}"
                )
            else:
                new_cf = cf_engine.combine(prev_cf, contribution)
                was_combined = True
                is_mixed = (prev_cf > 0) != (contribution > 0) and prev_cf != 0 and contribution != 0

                deduction_lines.append(
                    f"Combining with prior CF({condition}) = {prev_cf:+.3f}:"
                )
                deduction_lines.append(
                    "  " + cf_engine.format_combine_trace(prev_cf, contribution, new_cf)
                )
                if is_mixed:
                    deduction_lines.append(
                        f"  *** MIXED-SIGN CONFLICT *** "
                        f"CF({condition}) went from {prev_cf:+.3f} to {new_cf:+.3f}"
                    )
                    self.mixed_sign_conflicts.append({
                        "condition": condition, "cycle": cycle_num,
                        "rule_id": rule.rule_id, "prev_cf": prev_cf,
                        "contribution": contribution, "combined": new_cf,
                    })

            combined_after = new_cf
            self.wm.update_condition_cf(condition, new_cf, rule.rule_id)

        elif rule.conclusion_type == "URGENCY":
            escalated = self.wm.escalate_urgency(rule.conclusion_target, rule.rule_id)
            if escalated:
                deduction_lines.append(
                    f"URGENCY -> {rule.conclusion_target} (escalation-only; prior was lower)"
                )
            else:
                deduction_lines.append(
                    f"URGENCY unchanged: current level already >= {rule.conclusion_target}"
                )

        fired_refs_str = self._format_rule_with_refs(rule)
        cs_display = [(r.rule_id, self._format_rule_with_refs(r)) for r in cs_before]

        record = CycleRecord(
            cycle_num=cycle_num,
            wm_snapshot=self.wm.snapshot_names(),
            conflict_set=cs_display,
            fired_rule_id=rule.rule_id,
            fired_rule_refs=fired_refs_str,
            selection_reason="lowest index",
            deduction_text="\n".join(deduction_lines),
            conclusion_type=rule.conclusion_type,
            conclusion_target=rule.conclusion_target,
            evidence_cf=evidence,
            rule_weight=rule.cf_weight,
            contribution=contribution,
            combined_before=combined_before,
            combined_after=combined_after,
            was_combined=was_combined,
            new_fact_id=new_fact_id,
        )
        self.trace.append(record)
        self.fired_rules.add(rule.rule_id)
        self.fired_order.append(rule.rule_id)

    def _build_arith_prefix(self, rule: Rule, wm_dict: dict, evidence: float) -> str:
        fact_cfs = []
        for fname in rule.fact_refs:
            if fname.startswith("_condition_cf_"):
                cond = fname.replace("_condition_cf_", "")
                fact_cfs.append(self.wm.get_condition_cf(cond))
            elif fname in wm_dict:
                fact_cfs.append(wm_dict[fname]["cf"])

        if not fact_cfs:
            return f"{evidence:.3f}"
        if len(fact_cfs) == 1:
            return f"{fact_cfs[0]:.2f}"

        op = "max" if " OR " in rule.lhs_repr else "min"
        values_str = ", ".join(f"{v:.2f}" for v in fact_cfs)
        return f"{op}({values_str}) = {evidence:.3f}"

    def _format_rule_with_refs(self, rule: Rule) -> str:
        parts = []
        for fname in rule.fact_refs:
            if fname.startswith("_condition_cf_"):
                cond = fname.replace("_condition_cf_", "")
                parts.append(f"CF({cond})")
            else:
                parts.append(self.wm.fact_id_of(fname))
        if not parts:
            return rule.rule_id
        return f"{rule.rule_id}({','.join(parts)})"

    def run(self, max_cycles: int = 200):
        cycle_num = 0
        while True:
            if cycle_num >= max_cycles:
                break
            cs = self._match()
            if not cs:
                break
            cycle_num += 1
            fired = self._select(cs)
            self._fire(fired, cycle_num, cs)

    def rank_conditions(self) -> list:
        all_cfs = self.wm.get_all_condition_cfs()
        return sorted(all_cfs.items(), key=lambda kv: kv[1], reverse=True)

    def classify_output(self) -> dict:
        ranked = self.rank_conditions()
        top_name, top_cf = ranked[0] if ranked else (None, 0.0)

        primary_threshold = OUTPUT_RULES["primary_diagnosis_threshold"]
        window = OUTPUT_RULES["differential_window"]
        low_conf = OUTPUT_RULES["low_confidence_threshold"]

        if top_cf < low_conf:
            return {
                "scenario": "low_confidence",
                "primary": None, "primary_cf": None,
                "differentials": ranked, "all_ranked": ranked,
                "notes": (
                    f"Top CF score ({top_cf:+.3f}) is below the primary "
                    f"diagnosis threshold ({primary_threshold}). "
                    "Physician consultation recommended."
                ),
            }

        close_conditions = [(n, c) for n, c in ranked if (top_cf - c) <= window and c > 0]
        num_close = len(close_conditions)

        if num_close == 1:
            return {
                "scenario": "standard_primary",
                "primary": top_name, "primary_cf": top_cf,
                "differentials": [x for x in ranked if x[0] != top_name],
                "all_ranked": ranked,
                "notes": f"Primary diagnosis is {top_name} (CF = {top_cf:+.3f}).",
            }
        elif num_close == 2:
            return {
                "scenario": "differential_pair",
                "primary": None, "primary_cf": None,
                "differentials": close_conditions, "all_ranked": ranked,
                "notes": "Differential pair flagged. Physician evaluation recommended.",
            }
        else:
            return {
                "scenario": "unranked_differential",
                "primary": None, "primary_cf": None,
                "differentials": close_conditions, "all_ranked": ranked,
                "notes": f"Unranked differential: {num_close} conditions within {window} CF.",
            }

    def finalize_urgency(self, classification: dict, domain: str):
        primary = classification.get("primary")
        if not primary:
            self.wm.set_baseline_urgency("MODERATE")
            return

        baseline_map = {
            "Common Cold": "LOW", "Influenza": "MODERATE", "COVID-19": "MODERATE",
            "Strep Throat": "MODERATE", "Pneumonia": "HIGH", "Bronchitis": "MODERATE",
            "Gastroenteritis": "MODERATE", "Food Poisoning": "MODERATE",
            "Appendicitis": "HIGH", "Gastric Ulcer": "MODERATE",
            "IBS": "LOW", "Acid Reflux": "LOW",
            "Tension Headache": "LOW", "Migraine": "MODERATE",
            "Meningitis": "HIGH", "Stroke": "EMERGENCY",
            "Vertigo": "MODERATE", "Epilepsy": "HIGH",
        }
        baseline = baseline_map.get(primary, "MODERATE")
        self.wm.set_baseline_urgency(baseline)
