"""
app.py
======
Flask web server for the Medical Diagnosis Expert System.

This is a thin wrapper around the existing 6-file engine. All inference
logic lives in knowledge_base.py / working_memory.py / cf_engine.py /
inference_engine.py / explanation.py — this file only:
  - Serves HTML pages
  - Accepts patient answers via form POSTs
  - Runs the engine and returns results as JSON or rendered HTML

Run with:
    python app.py

Then open http://localhost:5000 in your browser.
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import secrets
import os

from knowledge_base import DOMAINS, SUGGESTED_ACTIONS, OUTPUT_RULES
from working_memory import WorkingMemory
from inference_engine import InferenceEngine
from ui_schema import (
    UI_SCHEMA, SMART_SKIPS, DIAGNOSIS_HIGHLIGHTS,
    SEVERITY_COLORS, URGENCY_STYLES,
)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def get_visible_questions(domain_id, answers):
    """Return the list of questions that should be visible given current answers
    (after smart-skip rules have been applied)."""
    all_questions = UI_SCHEMA[domain_id]["questions"]
    skips = SMART_SKIPS.get(domain_id, {})
    hidden = set()
    for question in all_questions:
        if question["name"] in answers:
            key = (question["name"], answers[question["name"]])
            if key in skips:
                for child in skips[key]:
                    hidden.add(child)
    return [q for q in all_questions if q["name"] not in hidden]


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Home page: domain selector."""
    # Reset session on returning to home
    session.pop("domain", None)
    session.pop("answers", None)
    session.pop("step", None)

    domains = []
    for dom_id, ui in UI_SCHEMA.items():
        backend = DOMAINS[dom_id]
        domains.append({
            "id": dom_id,
            "display_name": ui["display_name"],
            "description": ui["description"],
            "icon_color": ui["icon_color"],
            "accent_color": ui["accent_color"],
            "conditions": backend["conditions"],
            "emergency": backend["emergency_condition"],
        })
    return render_template("index.html", domains=domains)


@app.route("/start/<domain_id>")
def start_domain(domain_id):
    """Initialize session and start the questionnaire."""
    if domain_id not in UI_SCHEMA:
        return redirect(url_for("index"))
    session["domain"] = domain_id
    session["answers"] = {}
    session["step"] = 0
    return redirect(url_for("question"))


@app.route("/question", methods=["GET", "POST"])
def question():
    """Show the current question and handle answer submission."""
    domain_id = session.get("domain")
    if not domain_id:
        return redirect(url_for("index"))

    answers = session.get("answers", {})
    step = session.get("step", 0)

    if request.method == "POST":
        # Handle answer submission or navigation
        action = request.form.get("action", "next")
        question_name = request.form.get("question_name")

        if action == "back":
            visible = get_visible_questions(domain_id, answers)
            if step > 0:
                step -= 1
                # Remove the answer for the question we're going back to
                if step < len(visible):
                    prev_name = visible[step]["name"]
                    if prev_name in answers:
                        del answers[prev_name]
                session["answers"] = answers
                session["step"] = step
            return redirect(url_for("question"))

        if action == "skip":
            # Skipped optional field, do not record
            step += 1
            session["step"] = step
            return redirect(url_for("question"))

        if action == "next" and question_name:
            raw_value = request.form.get("value")
            if raw_value is not None and raw_value != "":
                # Cast numerics
                # (HTML forms always send strings; we convert if type is numeric)
                visible_now = get_visible_questions(domain_id, answers)
                q_def = next((q for q in visible_now if q["name"] == question_name), None)
                if q_def and q_def["type"] in ("numeric", "numeric_optional"):
                    try:
                        f = float(raw_value)
                        raw_value = int(f) if f == int(f) else f
                    except ValueError:
                        pass
                answers[question_name] = raw_value
            step += 1
            session["answers"] = answers
            session["step"] = step

            # Apply smart-skip: advance past any hidden questions
            visible = get_visible_questions(domain_id, answers)
            if step >= len(visible):
                return redirect(url_for("analyze"))
            return redirect(url_for("question"))

    # GET: show the current question
    visible = get_visible_questions(domain_id, answers)
    if step >= len(visible):
        return redirect(url_for("analyze"))

    q = visible[step]
    total = len(visible)

    ui = UI_SCHEMA[domain_id]
    return render_template(
        "question.html",
        domain_id=domain_id,
        domain_name=ui["display_name"],
        accent_color=ui["accent_color"],
        question=q,
        step=step + 1,
        total=total,
        progress_pct=int(((step + 1) / total) * 100) if total else 0,
        can_go_back=(step > 0),
        current_answer=answers.get(q["name"]),
    )


@app.route("/analyze")
def analyze():
    """Show the 'analyzing...' transition page."""
    domain_id = session.get("domain")
    if not domain_id:
        return redirect(url_for("index"))
    return render_template("analyze.html",
                           domain_name=UI_SCHEMA[domain_id]["display_name"],
                           accent_color=UI_SCHEMA[domain_id]["accent_color"])


@app.route("/results")
def results():
    """Run the inference engine and display the results page."""
    domain_id = session.get("domain")
    answers = session.get("answers", {})
    if not domain_id:
        return redirect(url_for("index"))

    dom = DOMAINS[domain_id]
    ui = UI_SCHEMA[domain_id]
    wm = WorkingMemory(domain_id, dom["conditions"])

    # Load patient facts into WM
    for name, value in answers.items():
        wm.add_patient_fact(name, value)

    # Mark missing mandatory fields
    for q in ui["questions"]:
        if q["type"] in ("bool", "enum", "numeric") and q["name"] not in answers:
            # Check if it was smart-skipped (legitimately excluded) vs just missing
            visible = get_visible_questions(domain_id, answers)
            if q["name"] in [v["name"] for v in visible]:
                wm.flag_missing_mandatory(q["name"])

    engine = InferenceEngine(dom["rules"], wm)
    engine.run()
    classification = engine.classify_output()
    engine.finalize_urgency(classification, domain_id)

    # Build results data structure for the template
    highlight_info = None
    if classification["primary"]:
        highlight_info = DIAGNOSIS_HIGHLIGHTS.get(classification["primary"])

    # Ranked conditions (only positive contributors shown prominently)
    ranked_display = []
    for name, cf in classification["all_ranked"]:
        pct = int(round(cf * 100))
        ranked_display.append({
            "name": name,
            "cf": cf,
            "pct": pct,
            "bar_pct": max(0, min(100, pct)),  # for width styling
            "is_negative": cf < 0,
        })

    # Build trace rows for the Doctor Mode panel
    trace_rows = []
    for rec in engine.trace:
        trace_rows.append({
            "cycle": rec.cycle_num,
            "wm": rec.wm_snapshot,
            "cs": [r[1] for r in rec.conflict_set],
            "rule": rec.fired_rule_refs,
            "deduction": rec.deduction_text.split("\n"),
            "is_mixed_sign": any(c["cycle"] == rec.cycle_num
                                  for c in engine.mixed_sign_conflicts),
        })

    # Patient-facing reasoning bullets
    rule_by_id = {r.rule_id: r for r in dom["rules"]}
    reasoning = []
    primary = classification.get("primary")
    if primary:
        for rid in engine.fired_order:
            r = rule_by_id.get(rid)
            if r and r.conclusion_type == "CONDITION_CF" and r.conclusion_target == primary and r.cf_weight > 0:
                reasoning.append({"rule_id": r.rule_id, "text": r.rationale})
        reasoning = reasoning[:3]

    # Mixed-sign conflicts (for a dedicated panel)
    conflict_panels = []
    for c in engine.mixed_sign_conflicts:
        conflict_panels.append({
            "condition": c["condition"],
            "cycle": c["cycle"],
            "rule_id": c["rule_id"],
            "prev_cf": c["prev_cf"],
            "contribution": c["contribution"],
            "combined": c["combined"],
            "formula": (
                f"({c['prev_cf']:+.3f} + ({c['contribution']:+.3f})) / "
                f"(1 - min(|{c['prev_cf']:.3f}|, |{c['contribution']:.3f}|)) = "
                f"{c['combined']:+.3f}"
            ),
        })

    # Suggested action text
    suggested_action = SUGGESTED_ACTIONS.get(domain_id, {}).get(wm.urgency, "")

    # Initial patient facts (for Doctor Mode)
    patient_facts = []
    for f in wm.fact_log:
        if f.source == "PATIENT_INPUT":
            patient_facts.append({
                "id": f.fact_id, "name": f.name, "value": f.value, "cf": f.cf,
            })
    derived_facts = []
    for f in wm.fact_log:
        if f.source == "DERIVED":
            derived_facts.append({
                "id": f.fact_id, "name": f.name, "cf": f.cf, "origin": f.origin,
            })

    return render_template(
        "results.html",
        domain_id=domain_id,
        domain_name=ui["display_name"],
        accent_color=ui["accent_color"],
        classification=classification,
        urgency=wm.urgency,
        urgency_style=URGENCY_STYLES.get(wm.urgency, URGENCY_STYLES["LOW"]),
        ranked=ranked_display,
        reasoning=reasoning,
        highlight=highlight_info,
        severity_colors=SEVERITY_COLORS,
        suggested_action=suggested_action,
        trace_rows=trace_rows,
        conflict_panels=conflict_panels,
        patient_facts=patient_facts,
        derived_facts=derived_facts,
        fired_rules_count=len(engine.fired_rules),
        missing_fields=wm.missing_mandatory,
    )


@app.route("/new")
def new_session():
    session.clear()
    return redirect(url_for("index"))


# -----------------------------------------------------------------------------
# Demo mode - preloaded scenarios for the live presentation
# -----------------------------------------------------------------------------

DEMO_SCENARIOS = {
    "stroke": ("NEUROLOGICAL", {
        "headache": "no", "headache_location": "none", "headache_onset": "none",
        "neck_stiffness": "no", "photophobia": "no", "visual_aura": "no",
        "facial_drooping": "yes", "arm_weakness": "yes", "arm_weakness_side": "unilateral",
        "slurred_speech": "yes", "confused_speech": "yes",
        "loss_of_consciousness": "no", "muscle_jerking": "no",
        "dizziness": "no", "balance_loss": "no", "fever": "no",
        "symptom_onset": "sudden", "symptom_duration_minutes": 30,
        "migraine_history": "no", "hypertension_history": "yes",
    }),
    "cold": ("RESPIRATORY", {
        "fever": "yes", "cough": "dry", "runny_nose": "yes",
        "sore_throat": "no", "shortness_of_breath": "no",
        "body_aches": "no", "fatigue": "yes",
        "loss_of_smell": "no", "loss_of_taste": "no", "chest_tightness": "no",
        "symptom_duration": 3, "symptom_onset": "gradual",
        "fever_temp": 37.8, "influenza_vaccinated": "yes",
    }),
    "flu_vaccinated": ("RESPIRATORY", {
        "fever": "yes", "cough": "dry", "runny_nose": "no",
        "sore_throat": "no", "shortness_of_breath": "no",
        "body_aches": "yes", "fatigue": "yes",
        "loss_of_smell": "no", "loss_of_taste": "no", "chest_tightness": "no",
        "symptom_duration": 2, "symptom_onset": "sudden",
        "fever_temp": 39.0, "influenza_vaccinated": "yes",
    }),
    "pneumonia": ("RESPIRATORY", {
        "fever": "yes", "cough": "productive", "runny_nose": "no",
        "sore_throat": "no", "shortness_of_breath": "yes",
        "body_aches": "no", "fatigue": "yes",
        "loss_of_smell": "no", "loss_of_taste": "no", "chest_tightness": "yes",
        "symptom_duration": 6, "symptom_onset": "gradual",
        "fever_temp": 39.4, "SpO2": 91, "influenza_vaccinated": "no",
    }),
    "appendicitis": ("GASTROINTESTINAL", {
        "abdominal_pain": "yes", "pain_location": "lower_right",
        "pain_onset": "sudden", "pain_pattern": "constant",
        "nausea": "yes", "vomiting": "no", "diarrhea": "no",
        "constipation": "no", "loss_of_appetite": "yes",
        "fever": "yes", "heartburn": "no", "regurgitation": "no",
        "bloating": "no", "symptom_duration": 1,
        "symptom_trigger": "none", "symptom_history": "first_time",
        "fever_temp": 38.6, "prior_appendectomy": "no",
    }),
    "migraine": ("NEUROLOGICAL", {
        "headache": "yes", "headache_location": "unilateral",
        "headache_onset": "gradual",
        "neck_stiffness": "no", "photophobia": "yes", "visual_aura": "yes",
        "facial_drooping": "no", "arm_weakness": "no",
        "arm_weakness_side": "none", "slurred_speech": "no",
        "confused_speech": "no", "loss_of_consciousness": "no",
        "muscle_jerking": "no", "dizziness": "no", "balance_loss": "no",
        "fever": "no", "symptom_onset": "gradual",
        "symptom_duration_minutes": 240,
        "migraine_history": "yes", "hypertension_history": "no",
    }),
}


@app.route("/demo/<scenario>")
def demo(scenario):
    if scenario not in DEMO_SCENARIOS:
        return redirect(url_for("index"))
    domain_id, facts = DEMO_SCENARIOS[scenario]
    session["domain"] = domain_id
    session["answers"] = dict(facts)
    session["step"] = len(UI_SCHEMA[domain_id]["questions"])
    return redirect(url_for("analyze"))


if __name__ == "__main__":
    print()
    print("=" * 66)
    print("  MEDICAL DIAGNOSIS EXPERT SYSTEM — Web Interface")
    print("  AIE212 Knowledge-Based Systems | Alamein International University")
    print("=" * 66)
    print()
    print("  Starting server...")
    print("  Open your browser to:  http://localhost:5000")
    print()
    print("  Press Ctrl+C to stop the server.")
    print("=" * 66)
    print()
    app.run(debug=False, host="0.0.0.0", port=5000)
