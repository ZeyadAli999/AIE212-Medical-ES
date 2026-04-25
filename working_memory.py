"""
working_memory.py
=================
Medical Diagnosis Expert System - Working Memory

Stores all facts during an inference session. Maps to Phase 3 Section 1.3
(Working Memory Schema).

Three categories of facts are stored:
  1. Initial patient facts     - loaded from patient input, CF = 1.0
  2. Derived intermediate facts - produced when a rule fires, CF computed
  3. Condition CF scores       - one per diagnosable condition, init 0.0

Fact numbering follows Dr. Essam's Lecture 5 convention:
  - Initial patient facts:  f1, f2, ..., fN
  - Derived facts:          f(N+1), f(N+2), ...

This enables the decision trace to render cells like "R6(f13,f14,f15)"
exactly as shown in the lecture slides.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Fact:
    """A single fact in Working Memory."""
    fact_id: str
    name: str
    value: Any
    cf: float
    source: str
    origin: str = "PATIENT"


class WorkingMemory:
    """
    Working Memory for a single inference session.
    Monotonic reasoning: once a fact is added, it is never retracted.
    """

    def __init__(self, active_domain: str, conditions: list):
        self.active_domain = active_domain
        self._facts: dict = {}
        self._fact_counter = 0
        self._fact_log: list = []
        self._urgency = "LOW"
        self._urgency_origin = None
        self._missing_mandatory: list = []

        for cond in conditions:
            self._facts[f"_condition_cf_{cond}"] = {
                "value": 0.0, "cf": 0.0, "source": "SYSTEM_INIT",
                "origin": "INIT", "fact_id": None,
            }

    def add_patient_fact(self, name: str, value: Any, cf: float = 1.0):
        self._fact_counter += 1
        fact_id = f"f{self._fact_counter}"
        self._facts[name] = {
            "value": value, "cf": cf, "source": "PATIENT_INPUT",
            "origin": "PATIENT", "fact_id": fact_id,
        }
        self._fact_log.append(Fact(fact_id, name, value, cf, "PATIENT_INPUT", "PATIENT"))
        return fact_id

    def add_derived_fact(self, name: str, value: Any, cf: float, origin_rule: str):
        self._fact_counter += 1
        fact_id = f"f{self._fact_counter}"
        self._facts[name] = {
            "value": value, "cf": cf, "source": "DERIVED",
            "origin": origin_rule, "fact_id": fact_id,
        }
        self._fact_log.append(Fact(fact_id, name, value, cf, "DERIVED", origin_rule))
        return fact_id

    def update_condition_cf(self, condition: str, new_cf: float, origin_rule: str):
        key = f"_condition_cf_{condition}"
        self._facts[key]["value"] = new_cf
        self._facts[key]["cf"] = new_cf
        self._facts[key]["origin"] = origin_rule

    _URGENCY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "EMERGENCY": 3}

    def escalate_urgency(self, new_level: str, origin_rule: str) -> bool:
        if self._URGENCY_RANK[new_level] > self._URGENCY_RANK[self._urgency]:
            self._urgency = new_level
            self._urgency_origin = origin_rule
            return True
        return False

    def set_baseline_urgency(self, level: str):
        self.escalate_urgency(level, "BASELINE_FROM_PRIMARY_DIAGNOSIS")

    @property
    def urgency(self):
        return self._urgency

    @property
    def urgency_origin(self):
        return self._urgency_origin

    def flag_missing_mandatory(self, field_name: str):
        if field_name not in self._missing_mandatory:
            self._missing_mandatory.append(field_name)

    @property
    def missing_mandatory(self):
        return list(self._missing_mandatory)

    def as_dict(self) -> dict:
        return self._facts

    def get_condition_cf(self, condition: str) -> float:
        return self._facts.get(f"_condition_cf_{condition}", {"cf": 0.0})["cf"]

    def get_all_condition_cfs(self) -> dict:
        return {
            key.replace("_condition_cf_", ""): entry["cf"]
            for key, entry in self._facts.items()
            if key.startswith("_condition_cf_")
        }

    def has_fact(self, name: str) -> bool:
        return name in self._facts and not name.startswith("_condition_cf_")

    def get_fact(self, name: str) -> Fact:
        entry = self._facts.get(name)
        if not entry or name.startswith("_condition_cf_"):
            return None
        return Fact(
            entry["fact_id"], name, entry["value"], entry["cf"],
            entry["source"], entry["origin"],
        )

    def fact_id_of(self, name: str) -> str:
        entry = self._facts.get(name)
        if not entry or name.startswith("_condition_cf_"):
            return "-"
        return entry["fact_id"] or "-"

    @property
    def fact_log(self) -> list:
        return list(self._fact_log)

    def snapshot_names(self) -> list:
        ids = [f.fact_id for f in self._fact_log]
        if len(ids) <= 4:
            return ",".join(ids)
        return f"{ids[0]},{ids[1]},...,{ids[-1]}"
