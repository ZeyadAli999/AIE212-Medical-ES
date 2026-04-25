"""
knowledge_base.py
=================
Medical Diagnosis Expert System - Knowledge Base

Contains all three domain rule sets, fact schemas, condition registries,
and plain-language rationales for the patient-facing explanation layer.

Maps directly to Phase 3 Section 1 (Three-Layer Organization) and
Phase 3 Section 2 (Knowledge Representation).

Course:     AIE212 - Knowledge-Based Systems
University: Alamein International University
Instructor: Dr. Essam Abdellatef
Semester:   Spring 2025/2026
"""

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Rule:
    """
    Canonical rule format as defined in Phase 3 Section 2.1.
    """
    rule_id: str
    domain: str
    priority: int
    lhs_repr: str
    condition: Callable[[dict], bool]
    evidence_cf: Callable[[dict], float]
    conclusion_type: str   # "CONDITION_CF" | "INTERMEDIATE_FACT" | "URGENCY"
    conclusion_target: str
    cf_weight: float
    rationale: str
    fact_refs: list = field(default_factory=list)
    cf_source: str = "team_judgment"


# --- Helper predicates for rule LHS callables --------------------------------

def has(wm: dict, fact: str, value: Any = True) -> bool:
    return fact in wm and wm[fact]["value"] == value


def num(wm: dict, fact: str) -> float:
    return wm[fact]["value"] if fact in wm else None


def cf_of(wm: dict, fact: str) -> float:
    return wm[fact]["cf"] if fact in wm else 0.0


def condition_cf(wm: dict, condition_name: str) -> float:
    return wm.get(f"_condition_cf_{condition_name}", {"cf": 0.0})["cf"]


# =============================================================================
# DOMAIN 1 - RESPIRATORY & FEVER
# =============================================================================

RESPIRATORY_CONDITIONS = [
    "Common Cold", "Influenza", "COVID-19",
    "Strep Throat", "Pneumonia", "Bronchitis",
]

RESPIRATORY_RULES = [
    Rule(
        rule_id="R1", domain="RESPIRATORY", priority=1,
        lhs_repr="fever = yes AND symptom_duration <= 5",
        condition=lambda wm: has(wm, "fever", "yes") and num(wm, "symptom_duration") is not None and num(wm, "symptom_duration") <= 5,
        evidence_cf=lambda wm: min(cf_of(wm, "fever"), cf_of(wm, "symptom_duration")),
        conclusion_type="INTERMEDIATE_FACT", conclusion_target="gradual_onset_fever",
        cf_weight=+0.60,
        fact_refs=["fever", "symptom_duration"],
        rationale="You have a fever that developed over a short duration, a typical early indicator of a gradual-onset upper respiratory illness.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R2", domain="RESPIRATORY", priority=2,
        lhs_repr="runny_nose = yes AND cough = dry",
        condition=lambda wm: has(wm, "runny_nose", "yes") and has(wm, "cough", "dry"),
        evidence_cf=lambda wm: min(cf_of(wm, "runny_nose"), cf_of(wm, "cough")),
        conclusion_type="INTERMEDIATE_FACT", conclusion_target="upper_respiratory_infection",
        cf_weight=+0.70,
        fact_refs=["runny_nose", "cough"],
        rationale="A combination of runny nose and dry cough is a classic sign of an upper respiratory infection.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R3", domain="RESPIRATORY", priority=3,
        lhs_repr="gradual_onset_fever AND upper_respiratory_infection",
        condition=lambda wm: "gradual_onset_fever" in wm and "upper_respiratory_infection" in wm,
        evidence_cf=lambda wm: min(cf_of(wm, "gradual_onset_fever"), cf_of(wm, "upper_respiratory_infection")),
        conclusion_type="CONDITION_CF", conclusion_target="Common Cold",
        cf_weight=+0.80,
        fact_refs=["gradual_onset_fever", "upper_respiratory_infection"],
        rationale="Gradual-onset fever combined with upper respiratory symptoms matches the classic pattern of Common Cold.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R4", domain="RESPIRATORY", priority=4,
        lhs_repr="symptom_onset = sudden AND fever_temp >= 38.5 AND body_aches = yes",
        condition=lambda wm: (
            has(wm, "symptom_onset", "sudden")
            and num(wm, "fever_temp") is not None
            and num(wm, "fever_temp") >= 38.5
            and has(wm, "body_aches", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "symptom_onset"), cf_of(wm, "fever_temp"), cf_of(wm, "body_aches")),
        conclusion_type="CONDITION_CF", conclusion_target="Influenza",
        cf_weight=+0.85,
        fact_refs=["symptom_onset", "fever_temp", "body_aches"],
        rationale="Sudden symptom onset with high fever (>=38.5C) and body aches is the classic Influenza presentation.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R5", domain="RESPIRATORY", priority=5,
        lhs_repr="loss_of_smell = yes OR loss_of_taste = yes",
        condition=lambda wm: has(wm, "loss_of_smell", "yes") or has(wm, "loss_of_taste", "yes"),
        evidence_cf=lambda wm: max(cf_of(wm, "loss_of_smell"), cf_of(wm, "loss_of_taste")),
        conclusion_type="CONDITION_CF", conclusion_target="COVID-19",
        cf_weight=+0.90,
        fact_refs=["loss_of_smell", "loss_of_taste"],
        rationale="Loss of smell or taste is a highly specific indicator of COVID-19 infection.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R6", domain="RESPIRATORY", priority=6,
        lhs_repr="SpO2 < 94 AND fever_duration >= 5",
        condition=lambda wm: (
            num(wm, "SpO2") is not None and num(wm, "SpO2") < 94
            and num(wm, "fever_duration") is not None and num(wm, "fever_duration") >= 5
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "SpO2"), cf_of(wm, "fever_duration")),
        conclusion_type="CONDITION_CF", conclusion_target="Pneumonia",
        cf_weight=+0.95,
        fact_refs=["SpO2", "fever_duration"],
        rationale="Oxygen saturation below 94% combined with prolonged fever is a significant indicator of Pneumonia requiring immediate medical attention.",
        cf_source="clinical_threshold",
    ),
    Rule(
        rule_id="R7", domain="RESPIRATORY", priority=7,
        lhs_repr="SpO2 < 94",
        condition=lambda wm: num(wm, "SpO2") is not None and num(wm, "SpO2") < 94,
        evidence_cf=lambda wm: cf_of(wm, "SpO2"),
        conclusion_type="URGENCY", conclusion_target="HIGH",
        cf_weight=+1.00,
        fact_refs=["SpO2"],
        rationale="Oxygen saturation below 94% indicates respiratory compromise requiring urgent attention regardless of the suspected condition.",
        cf_source="clinical_threshold",
    ),
    Rule(
        rule_id="R8", domain="RESPIRATORY", priority=8,
        lhs_repr="sore_throat = yes AND cough = no",
        condition=lambda wm: has(wm, "sore_throat", "yes") and has(wm, "cough", "no"),
        evidence_cf=lambda wm: min(cf_of(wm, "sore_throat"), cf_of(wm, "cough")),
        conclusion_type="CONDITION_CF", conclusion_target="Strep Throat",
        cf_weight=+0.75,
        fact_refs=["sore_throat", "cough"],
        rationale="A severe sore throat in the absence of cough is a strong indicator of Strep Throat.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R9", domain="RESPIRATORY", priority=9,
        lhs_repr="cough = productive AND chest_tightness = yes AND symptom_duration >= 7",
        condition=lambda wm: (
            has(wm, "cough", "productive") and has(wm, "chest_tightness", "yes")
            and num(wm, "symptom_duration") is not None and num(wm, "symptom_duration") >= 7
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "cough"), cf_of(wm, "chest_tightness"), cf_of(wm, "symptom_duration")),
        conclusion_type="CONDITION_CF", conclusion_target="Bronchitis",
        cf_weight=+0.70,
        fact_refs=["cough", "chest_tightness", "symptom_duration"],
        rationale="A productive cough with chest tightness persisting beyond 7 days is typical of acute Bronchitis.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R10", domain="RESPIRATORY", priority=10,
        lhs_repr="influenza_vaccinated = yes",
        condition=lambda wm: has(wm, "influenza_vaccinated", "yes"),
        evidence_cf=lambda wm: cf_of(wm, "influenza_vaccinated"),
        conclusion_type="CONDITION_CF", conclusion_target="Influenza",
        cf_weight=-0.30,
        fact_refs=["influenza_vaccinated"],
        rationale="Reported influenza vaccination this season reduces (but does not eliminate) the likelihood of Influenza.",
        cf_source="clinical_criteria",
    ),
]

RESPIRATORY_FACT_SCHEMA = {
    "fever":                ("boolean", ["yes", "no"], True),
    "cough":                ("enum", ["dry", "productive", "no"], True),
    "sore_throat":          ("boolean", ["yes", "no"], True),
    "runny_nose":           ("boolean", ["yes", "no"], True),
    "shortness_of_breath":  ("boolean", ["yes", "no"], True),
    "body_aches":           ("boolean", ["yes", "no"], True),
    "fatigue":              ("boolean", ["yes", "no"], True),
    "loss_of_smell":        ("boolean", ["yes", "no"], True),
    "loss_of_taste":        ("boolean", ["yes", "no"], True),
    "chest_tightness":      ("boolean", ["yes", "no"], True),
    "symptom_duration":     ("numeric", (0, 60), True),
    "symptom_onset":        ("enum", ["sudden", "gradual"], True),
    "fever_temp":           ("numeric", (35.0, 42.0), False),
    "fever_duration":       ("numeric", (0, 30), False),
    "SpO2":                 ("numeric", (70, 100), False),
    "influenza_vaccinated": ("boolean", ["yes", "no"], False),
}


# =============================================================================
# DOMAIN 2 - GASTROINTESTINAL
# =============================================================================

GASTROINTESTINAL_CONDITIONS = [
    "Gastroenteritis", "Food Poisoning", "Appendicitis",
    "Gastric Ulcer", "IBS", "Acid Reflux",
]

GASTROINTESTINAL_RULES = [
    Rule(
        rule_id="R1", domain="GASTROINTESTINAL", priority=1,
        lhs_repr="pain_onset = sudden AND pain_location = lower_right AND pain_pattern = constant",
        condition=lambda wm: (
            has(wm, "pain_onset", "sudden") and has(wm, "pain_location", "lower_right")
            and has(wm, "pain_pattern", "constant")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "pain_onset"), cf_of(wm, "pain_location"), cf_of(wm, "pain_pattern")),
        conclusion_type="CONDITION_CF", conclusion_target="Appendicitis",
        cf_weight=+0.90,
        fact_refs=["pain_onset", "pain_location", "pain_pattern"],
        rationale="Sudden-onset constant pain localized to the lower-right abdomen is the hallmark of Appendicitis.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R2", domain="GASTROINTESTINAL", priority=2,
        lhs_repr="Appendicitis_CF >= 0.40",
        condition=lambda wm: condition_cf(wm, "Appendicitis") >= 0.40,
        evidence_cf=lambda wm: condition_cf(wm, "Appendicitis"),
        conclusion_type="URGENCY", conclusion_target="HIGH",
        cf_weight=+1.00,
        fact_refs=["_condition_cf_Appendicitis"],
        rationale="Evidence for Appendicitis is strong enough that it cannot be ruled out without imaging.",
        cf_source="clinical_threshold",
    ),
    Rule(
        rule_id="R3", domain="GASTROINTESTINAL", priority=3,
        lhs_repr="symptom_trigger = after_eating_outside AND vomiting = yes AND diarrhea = yes",
        condition=lambda wm: (
            has(wm, "symptom_trigger", "after_eating_outside")
            and has(wm, "vomiting", "yes") and has(wm, "diarrhea", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "symptom_trigger"), cf_of(wm, "vomiting"), cf_of(wm, "diarrhea")),
        conclusion_type="CONDITION_CF", conclusion_target="Food Poisoning",
        cf_weight=+0.85,
        fact_refs=["symptom_trigger", "vomiting", "diarrhea"],
        rationale="Vomiting and diarrhea shortly after eating outside is the classic pattern of Food Poisoning.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R4", domain="GASTROINTESTINAL", priority=4,
        lhs_repr="vomiting = yes AND diarrhea = yes AND symptom_trigger = none",
        condition=lambda wm: (
            has(wm, "vomiting", "yes") and has(wm, "diarrhea", "yes")
            and has(wm, "symptom_trigger", "none")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "vomiting"), cf_of(wm, "diarrhea"), cf_of(wm, "symptom_trigger")),
        conclusion_type="CONDITION_CF", conclusion_target="Gastroenteritis",
        cf_weight=+0.75,
        fact_refs=["vomiting", "diarrhea", "symptom_trigger"],
        rationale="Vomiting and diarrhea without a specific dietary trigger is most consistent with viral Gastroenteritis.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R5", domain="GASTROINTESTINAL", priority=5,
        lhs_repr="pain_location = upper AND pain_pattern = worse_when_hungry AND heartburn = yes",
        condition=lambda wm: (
            has(wm, "pain_location", "upper") and has(wm, "pain_pattern", "worse_when_hungry")
            and has(wm, "heartburn", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "pain_location"), cf_of(wm, "pain_pattern"), cf_of(wm, "heartburn")),
        conclusion_type="CONDITION_CF", conclusion_target="Gastric Ulcer",
        cf_weight=+0.80,
        fact_refs=["pain_location", "pain_pattern", "heartburn"],
        rationale="Upper-abdominal burning pain that worsens when hungry, combined with heartburn, is the classic Gastric Ulcer pattern.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R6", domain="GASTROINTESTINAL", priority=6,
        lhs_repr="nsaid_use = yes",
        condition=lambda wm: has(wm, "nsaid_use", "yes"),
        evidence_cf=lambda wm: cf_of(wm, "nsaid_use"),
        conclusion_type="CONDITION_CF", conclusion_target="Gastric Ulcer",
        cf_weight=+0.40,
        fact_refs=["nsaid_use"],
        rationale="Regular use of NSAIDs or aspirin is an established risk factor for Gastric Ulcer.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R7", domain="GASTROINTESTINAL", priority=7,
        lhs_repr="symptom_history = recurring AND diarrhea = yes AND constipation = yes AND fever = no",
        condition=lambda wm: (
            has(wm, "symptom_history", "recurring")
            and has(wm, "diarrhea", "yes") and has(wm, "constipation", "yes")
            and has(wm, "fever", "no")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "symptom_history"), cf_of(wm, "diarrhea"), cf_of(wm, "constipation"), cf_of(wm, "fever")),
        conclusion_type="CONDITION_CF", conclusion_target="IBS",
        cf_weight=+0.75,
        fact_refs=["symptom_history", "diarrhea", "constipation", "fever"],
        rationale="A recurring pattern of alternating diarrhea and constipation without fever is characteristic of IBS.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R8", domain="GASTROINTESTINAL", priority=8,
        lhs_repr="heartburn = yes AND regurgitation = yes AND pain_location = upper",
        condition=lambda wm: (
            has(wm, "heartburn", "yes") and has(wm, "regurgitation", "yes")
            and has(wm, "pain_location", "upper")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "heartburn"), cf_of(wm, "regurgitation"), cf_of(wm, "pain_location")),
        conclusion_type="CONDITION_CF", conclusion_target="Acid Reflux",
        cf_weight=+0.80,
        fact_refs=["heartburn", "regurgitation", "pain_location"],
        rationale="Heartburn with regurgitation and upper-abdominal discomfort is the typical presentation of Acid Reflux (GERD).",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R9", domain="GASTROINTESTINAL", priority=9,
        lhs_repr="prior_appendectomy = yes",
        condition=lambda wm: has(wm, "prior_appendectomy", "yes"),
        evidence_cf=lambda wm: cf_of(wm, "prior_appendectomy"),
        conclusion_type="CONDITION_CF", conclusion_target="Appendicitis",
        cf_weight=-1.00,
        fact_refs=["prior_appendectomy"],
        rationale="Prior appendectomy biologically eliminates Appendicitis as a possibility.",
        cf_source="clinical_criteria",
    ),
]

GASTROINTESTINAL_FACT_SCHEMA = {
    "abdominal_pain":      ("boolean", ["yes", "no"], True),
    "pain_location":       ("enum", ["upper", "central", "lower_right", "lower_left", "none"], True),
    "pain_onset":          ("enum", ["sudden", "gradual", "none"], True),
    "pain_pattern":        ("enum", ["constant", "intermittent", "worse_when_hungry", "none"], True),
    "nausea":              ("boolean", ["yes", "no"], True),
    "vomiting":            ("boolean", ["yes", "no"], True),
    "diarrhea":            ("boolean", ["yes", "no"], True),
    "constipation":        ("boolean", ["yes", "no"], True),
    "loss_of_appetite":    ("boolean", ["yes", "no"], True),
    "fever":               ("boolean", ["yes", "no"], True),
    "heartburn":           ("boolean", ["yes", "no"], True),
    "regurgitation":       ("boolean", ["yes", "no"], True),
    "bloating":            ("boolean", ["yes", "no"], True),
    "symptom_duration":    ("numeric", (0, 60), True),
    "symptom_trigger":     ("enum", ["after_eating_outside", "after_meals", "none"], True),
    "symptom_history":     ("enum", ["recurring", "first_time"], True),
    "fever_temp":          ("numeric", (35.0, 42.0), False),
    "nsaid_use":           ("boolean", ["yes", "no"], False),
    "prior_appendectomy":  ("boolean", ["yes", "no"], False),
}


# =============================================================================
# DOMAIN 3 - NEUROLOGICAL
# =============================================================================

NEUROLOGICAL_CONDITIONS = [
    "Tension Headache", "Migraine", "Meningitis",
    "Stroke", "Vertigo", "Epilepsy",
]

NEUROLOGICAL_RULES = [
    Rule(
        rule_id="R1", domain="NEUROLOGICAL", priority=1,
        lhs_repr="facial_drooping = yes",
        condition=lambda wm: has(wm, "facial_drooping", "yes"),
        evidence_cf=lambda wm: cf_of(wm, "facial_drooping"),
        conclusion_type="CONDITION_CF", conclusion_target="Stroke",
        cf_weight=+0.85,
        fact_refs=["facial_drooping"],
        rationale="Facial drooping is the 'F' of the FAST stroke criteria and a high-specificity indicator of Stroke.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R2", domain="NEUROLOGICAL", priority=2,
        lhs_repr="arm_weakness = yes AND arm_weakness_side = unilateral",
        condition=lambda wm: has(wm, "arm_weakness", "yes") and has(wm, "arm_weakness_side", "unilateral"),
        evidence_cf=lambda wm: min(cf_of(wm, "arm_weakness"), cf_of(wm, "arm_weakness_side")),
        conclusion_type="CONDITION_CF", conclusion_target="Stroke",
        cf_weight=+0.85,
        fact_refs=["arm_weakness", "arm_weakness_side"],
        rationale="Unilateral arm weakness is the 'A' of FAST and a high-specificity Stroke indicator.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R3", domain="NEUROLOGICAL", priority=3,
        lhs_repr="slurred_speech = yes OR confused_speech = yes",
        condition=lambda wm: has(wm, "slurred_speech", "yes") or has(wm, "confused_speech", "yes"),
        evidence_cf=lambda wm: max(cf_of(wm, "slurred_speech"), cf_of(wm, "confused_speech")),
        conclusion_type="CONDITION_CF", conclusion_target="Stroke",
        cf_weight=+0.85,
        fact_refs=["slurred_speech", "confused_speech"],
        rationale="Slurred or confused speech is the 'S' of FAST and a high-specificity Stroke indicator.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R4", domain="NEUROLOGICAL", priority=4,
        lhs_repr="Stroke_CF >= 0.50",
        condition=lambda wm: condition_cf(wm, "Stroke") >= 0.50,
        evidence_cf=lambda wm: condition_cf(wm, "Stroke"),
        conclusion_type="URGENCY", conclusion_target="EMERGENCY",
        cf_weight=+1.00,
        fact_refs=["_condition_cf_Stroke"],
        rationale="Evidence for Stroke is sufficient to require emergency services immediately. Every minute without treatment reduces recoverable brain tissue.",
        cf_source="clinical_threshold",
    ),
    Rule(
        rule_id="R5", domain="NEUROLOGICAL", priority=5,
        lhs_repr="neck_stiffness = yes AND fever = yes AND photophobia = yes",
        condition=lambda wm: (
            has(wm, "neck_stiffness", "yes") and has(wm, "fever", "yes")
            and has(wm, "photophobia", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "neck_stiffness"), cf_of(wm, "fever"), cf_of(wm, "photophobia")),
        conclusion_type="CONDITION_CF", conclusion_target="Meningitis",
        cf_weight=+0.90,
        fact_refs=["neck_stiffness", "fever", "photophobia"],
        rationale="Neck stiffness, fever, and photophobia together form the meningeal triad.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R6", domain="NEUROLOGICAL", priority=6,
        lhs_repr="headache_location = unilateral AND headache_onset = gradual AND visual_aura = yes",
        condition=lambda wm: (
            has(wm, "headache_location", "unilateral") and has(wm, "headache_onset", "gradual")
            and has(wm, "visual_aura", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "headache_location"), cf_of(wm, "headache_onset"), cf_of(wm, "visual_aura")),
        conclusion_type="CONDITION_CF", conclusion_target="Migraine",
        cf_weight=+0.85,
        fact_refs=["headache_location", "headache_onset", "visual_aura"],
        rationale="Unilateral gradual-onset headache preceded by visual aura is the classic Migraine presentation.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R7", domain="NEUROLOGICAL", priority=7,
        lhs_repr="headache_location = bilateral AND headache_onset = gradual AND neck_stiffness = no AND fever = no",
        condition=lambda wm: (
            has(wm, "headache_location", "bilateral") and has(wm, "headache_onset", "gradual")
            and has(wm, "neck_stiffness", "no") and has(wm, "fever", "no")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "headache_location"), cf_of(wm, "headache_onset"), cf_of(wm, "neck_stiffness"), cf_of(wm, "fever")),
        conclusion_type="CONDITION_CF", conclusion_target="Tension Headache",
        cf_weight=+0.80,
        fact_refs=["headache_location", "headache_onset", "neck_stiffness", "fever"],
        rationale="Bilateral pressing headache without fever or neck stiffness is typical of benign Tension Headache.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R8", domain="NEUROLOGICAL", priority=8,
        lhs_repr="loss_of_consciousness = yes AND muscle_jerking = yes",
        condition=lambda wm: has(wm, "loss_of_consciousness", "yes") and has(wm, "muscle_jerking", "yes"),
        evidence_cf=lambda wm: min(cf_of(wm, "loss_of_consciousness"), cf_of(wm, "muscle_jerking")),
        conclusion_type="CONDITION_CF", conclusion_target="Epilepsy",
        cf_weight=+0.85,
        fact_refs=["loss_of_consciousness", "muscle_jerking"],
        rationale="Loss of consciousness with involuntary muscle jerking is the classic seizure episode presentation.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R9", domain="NEUROLOGICAL", priority=9,
        lhs_repr="dizziness = yes AND balance_loss = yes AND symptom_onset = sudden AND hypertension_history = yes",
        condition=lambda wm: (
            has(wm, "dizziness", "yes") and has(wm, "balance_loss", "yes")
            and has(wm, "symptom_onset", "sudden") and has(wm, "hypertension_history", "yes")
        ),
        evidence_cf=lambda wm: min(cf_of(wm, "dizziness"), cf_of(wm, "balance_loss"), cf_of(wm, "symptom_onset"), cf_of(wm, "hypertension_history")),
        conclusion_type="CONDITION_CF", conclusion_target="Stroke",
        cf_weight=+0.55,
        fact_refs=["dizziness", "balance_loss", "symptom_onset", "hypertension_history"],
        rationale="Sudden dizziness and balance loss in a hypertensive patient raises the possibility of posterior circulation Stroke even without FAST signs.",
        cf_source="clinical_criteria",
    ),
    Rule(
        rule_id="R10", domain="NEUROLOGICAL", priority=10,
        lhs_repr="migraine_history = yes AND headache_location = unilateral AND facial_drooping = no AND arm_weakness = no AND slurred_speech = no",
        # CRITICAL: FAST guard mandatory - see Phase 3 Section 2.5
        condition=lambda wm: (
            has(wm, "migraine_history", "yes")
            and has(wm, "headache_location", "unilateral")
            and has(wm, "facial_drooping", "no")
            and has(wm, "arm_weakness", "no")
            and has(wm, "slurred_speech", "no")
        ),
        evidence_cf=lambda wm: min(
            cf_of(wm, "migraine_history"), cf_of(wm, "headache_location"),
            cf_of(wm, "facial_drooping"), cf_of(wm, "arm_weakness"), cf_of(wm, "slurred_speech"),
        ),
        conclusion_type="CONDITION_CF", conclusion_target="Stroke",
        cf_weight=-0.25,
        fact_refs=["migraine_history", "headache_location", "facial_drooping", "arm_weakness", "slurred_speech"],
        rationale="A known migraine history with a unilateral headache and NO FAST criteria slightly reduces Stroke likelihood. This suppression only applies when FAST signs are absent.",
        cf_source="clinical_criteria",
    ),
]

NEUROLOGICAL_FACT_SCHEMA = {
    "headache":                   ("boolean", ["yes", "no"], True),
    "headache_location":          ("enum", ["unilateral", "bilateral", "none"], True),
    "headache_onset":             ("enum", ["sudden", "gradual", "none"], True),
    "headache_intensity":         ("numeric", (0, 10), False),
    "neck_stiffness":             ("boolean", ["yes", "no"], True),
    "photophobia":                ("boolean", ["yes", "no"], True),
    "visual_aura":                ("boolean", ["yes", "no"], True),
    "facial_drooping":            ("boolean", ["yes", "no"], True),
    "arm_weakness":               ("boolean", ["yes", "no"], True),
    "arm_weakness_side":          ("enum", ["unilateral", "bilateral", "none"], True),
    "slurred_speech":             ("boolean", ["yes", "no"], True),
    "confused_speech":            ("boolean", ["yes", "no"], True),
    "loss_of_consciousness":      ("boolean", ["yes", "no"], True),
    "muscle_jerking":             ("boolean", ["yes", "no"], True),
    "dizziness":                  ("boolean", ["yes", "no"], True),
    "balance_loss":               ("boolean", ["yes", "no"], True),
    "fever":                      ("boolean", ["yes", "no"], True),
    "symptom_onset":              ("enum", ["sudden", "gradual"], True),
    "symptom_duration_minutes":   ("numeric", (0, 10080), True),
    "migraine_history":           ("boolean", ["yes", "no"], False),
    "hypertension_history":       ("boolean", ["yes", "no"], False),
    "family_history_stroke":      ("boolean", ["yes", "no"], False),
}


# =============================================================================
# DOMAIN REGISTRY
# =============================================================================

DOMAINS = {
    "RESPIRATORY": {
        "display_name": "Respiratory & Fever",
        "rules": RESPIRATORY_RULES,
        "conditions": RESPIRATORY_CONDITIONS,
        "fact_schema": RESPIRATORY_FACT_SCHEMA,
        "emergency_condition": "Pneumonia",
        "emergency_explanation": "Pneumonia - triggered when SpO2 < 94% (R7)",
    },
    "GASTROINTESTINAL": {
        "display_name": "Gastrointestinal",
        "rules": GASTROINTESTINAL_RULES,
        "conditions": GASTROINTESTINAL_CONDITIONS,
        "fact_schema": GASTROINTESTINAL_FACT_SCHEMA,
        "emergency_condition": "Appendicitis",
        "emergency_explanation": "Appendicitis - triggered when CF >= 0.40 (R2)",
    },
    "NEUROLOGICAL": {
        "display_name": "Neurological",
        "rules": NEUROLOGICAL_RULES,
        "conditions": NEUROLOGICAL_CONDITIONS,
        "fact_schema": NEUROLOGICAL_FACT_SCHEMA,
        "emergency_condition": "Stroke",
        "emergency_explanation": "Stroke - triggered when CF >= 0.50 (R4)",
    },
}


OUTPUT_RULES = {
    "primary_diagnosis_threshold": 0.20,
    "differential_window":         0.10,
    "low_confidence_threshold":    0.20,
}


SUGGESTED_ACTIONS = {
    "RESPIRATORY": {
        "LOW":       "Rest, increase fluid intake, and use over-the-counter cold medication if needed. No physician visit required unless symptoms worsen or persist beyond 7 days.",
        "MODERATE":  "Schedule a physician consultation within 24-48 hours. Monitor temperature and oxygen saturation if possible. Isolate if COVID-19 is suspected.",
        "HIGH":      "Seek emergency care immediately. Low oxygen saturation and persistent fever indicate significant respiratory compromise. Do not delay.",
        "EMERGENCY": "Call emergency services immediately.",
    },
    "GASTROINTESTINAL": {
        "LOW":       "Avoid large meals and lying down after eating. Use antacids if needed. If symptoms persist beyond 2 weeks or worsen, schedule a clinic appointment.",
        "MODERATE":  "Consult a physician within 24 hours. Maintain hydration. Avoid solid food until symptoms subside.",
        "HIGH":      "Go to the emergency department immediately. Do not eat or drink anything. Appendicitis cannot be ruled out without imaging - delayed treatment increases risk of perforation.",
        "EMERGENCY": "Call emergency services immediately.",
    },
    "NEUROLOGICAL": {
        "LOW":       "Rest in a dark, quiet room. Monitor symptoms. If this headache is significantly more severe than usual or accompanied by new symptoms, seek medical attention immediately.",
        "MODERATE":  "Consult a physician within 24 hours. Rest and avoid strenuous activity.",
        "HIGH":      "Seek emergency care immediately. Meningitis and stroke require imaging for confirmation and urgent treatment.",
        "EMERGENCY": "Call emergency services immediately. Do not drive to hospital. Report the approximate time of symptom onset - this is critical information for the responding medical team. Every minute without treatment reduces recoverable brain tissue.",
    },
}
