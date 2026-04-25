"""
ui_schema.py
============
UI Metadata for the web interface.

Separate from knowledge_base.py which is engine-only. This module
defines:
  - How each question is rendered in the browser
  - Help text for every medical term
  - Numeric hints and quick-select chips
  - Question groupings for the multi-step wizard
  - Smart-skip dependencies

All of this exists so the backend engine stays pure and reusable.
"""

# Type values:
#   'bool'           -> yes/no button pair, required
#   'bool_optional'  -> yes/no/skip, optional
#   'enum'           -> one-of-N card selector, required
#   'enum_optional'  -> one-of-N + skip, optional
#   'numeric'        -> slider + chips + manual, required
#   'numeric_optional'-> slider + chips + manual + skip, optional


RESPIRATORY_QUESTIONS = [
    {
        "group": "Primary Symptoms",
        "name": "fever",
        "type": "bool",
        "prompt": "Do you have a fever?",
        "help": "A fever is a body temperature higher than normal (above 37.5°C / 99.5°F). You may feel hot, sweaty, or have chills.",
    },
    {
        "group": "Primary Symptoms",
        "name": "cough",
        "type": "enum_optional",
        "prompt": "Do you have a cough?",
        "help": "A 'dry' cough produces no mucus. A 'productive' cough brings up phlegm or mucus from your chest.",
        "options": [
            {"value": "dry", "label": "Dry cough", "icon": "🫁"},
            {"value": "productive", "label": "Productive (phlegm)", "icon": "💧"},
            {"value": "no", "label": "No cough", "icon": "✖"},
        ],
    },
    {
        "group": "Primary Symptoms",
        "name": "runny_nose",
        "type": "bool",
        "prompt": "Do you have a runny or blocked nose?",
        "help": "Nasal congestion, a runny nose, or sinus pressure.",
    },
    {
        "group": "Primary Symptoms",
        "name": "sore_throat",
        "type": "bool",
        "prompt": "Do you have a sore throat?",
        "help": "Pain, scratchiness, or irritation in the throat, especially when swallowing.",
    },
    {
        "group": "Primary Symptoms",
        "name": "shortness_of_breath",
        "type": "bool",
        "prompt": "Do you have shortness of breath?",
        "help": "Feeling unable to take a full breath, or having to work harder than usual to breathe.",
    },
    {
        "group": "Secondary Symptoms",
        "name": "body_aches",
        "type": "bool",
        "prompt": "Do you have body aches or muscle pain?",
        "help": "General soreness or pain throughout the body, especially in muscles.",
    },
    {
        "group": "Secondary Symptoms",
        "name": "fatigue",
        "type": "bool",
        "prompt": "Do you feel unusually tired or exhausted?",
        "help": "A level of tiredness that is beyond normal — feeling drained even after rest.",
    },
    {
        "group": "Secondary Symptoms",
        "name": "loss_of_smell",
        "type": "bool",
        "prompt": "Have you lost your sense of smell?",
        "help": "Inability to detect common odors like coffee, food, or perfume. A key indicator of COVID-19.",
    },
    {
        "group": "Secondary Symptoms",
        "name": "loss_of_taste",
        "type": "bool",
        "prompt": "Have you lost your sense of taste?",
        "help": "Food tasting bland or metallic. Often occurs together with loss of smell.",
    },
    {
        "group": "Secondary Symptoms",
        "name": "chest_tightness",
        "type": "bool",
        "prompt": "Do you have chest tightness or chest pain?",
        "help": "A feeling of pressure, heaviness, or squeezing in the chest area.",
    },
    {
        "group": "Onset & Duration",
        "name": "symptom_duration",
        "type": "numeric",
        "prompt": "How many days have symptoms lasted?",
        "help": "Count from the day your first symptom appeared.",
        "unit": "days",
        "min": 0,
        "max": 30,
        "default": 3,
        "context_hint": "Respiratory illnesses typically last 3-14 days. A cold usually improves within 7 days; pneumonia may worsen over 5+ days.",
        "quick_chips": [
            {"label": "1 day", "value": 1},
            {"label": "3 days", "value": 3},
            {"label": "1 week", "value": 7},
            {"label": "2 weeks", "value": 14},
        ],
    },
    {
        "group": "Onset & Duration",
        "name": "symptom_onset",
        "type": "enum",
        "prompt": "How did symptoms start?",
        "help": "'Sudden' = you felt fine, then within hours felt very ill (typical of flu). 'Gradual' = symptoms built up slowly over days (typical of a cold).",
        "options": [
            {"value": "sudden", "label": "Suddenly (within hours)", "icon": "⚡"},
            {"value": "gradual", "label": "Gradually (over days)", "icon": "🌱"},
        ],
    },
    {
        "group": "Optional Vitals",
        "name": "fever_temp",
        "type": "numeric_optional",
        "prompt": "Body temperature (°C) — skip if unknown",
        "help": "Normal: 36.5-37.5°C. Low-grade fever: 37.5-38°C. High fever: above 38.5°C. Skip this if you haven't measured your temperature.",
        "unit": "°C",
        "min": 35.0,
        "max": 42.0,
        "default": 37.8,
        "step": 0.1,
        "context_hint": "Influenza often causes fever above 38.5°C. A cold rarely exceeds 38°C.",
        "quick_chips": [
            {"label": "Normal (37°C)", "value": 37.0},
            {"label": "Low fever (37.8°C)", "value": 37.8},
            {"label": "Moderate (38.5°C)", "value": 38.5},
            {"label": "High (39.5°C)", "value": 39.5},
        ],
    },
    {
        "group": "Optional Vitals",
        "name": "SpO2",
        "type": "numeric_optional",
        "prompt": "Oxygen saturation / SpO₂ (%) — skip if unknown",
        "help": "Measured by a pulse oximeter. Healthy: 95-100%. Below 94% is a medical emergency for respiratory illness.",
        "unit": "%",
        "min": 70,
        "max": 100,
        "default": 97,
        "context_hint": "Below 94% triggers automatic escalation to HIGH urgency (possible pneumonia).",
        "quick_chips": [
            {"label": "Healthy (97%)", "value": 97},
            {"label": "Borderline (94%)", "value": 94},
            {"label": "Concerning (91%)", "value": 91},
            {"label": "Critical (85%)", "value": 85},
        ],
    },
    {
        "group": "Patient History",
        "name": "influenza_vaccinated",
        "type": "bool",
        "prompt": "Have you received the Influenza vaccine this season?",
        "help": "The flu shot reduces (but does not eliminate) the likelihood of Influenza infection.",
    },
]


GASTROINTESTINAL_QUESTIONS = [
    {
        "group": "Primary Symptoms",
        "name": "abdominal_pain",
        "type": "bool",
        "prompt": "Do you have abdominal pain?",
        "help": "Pain anywhere in the belly area, from below the ribs to the groin.",
    },
    {
        "group": "Primary Symptoms",
        "name": "pain_location",
        "type": "enum",
        "prompt": "Where is the pain located?",
        "help": "Pain location is one of the most important clues. Lower-right pain that started near the navel and moved is a classic appendicitis sign.",
        "options": [
            {"value": "upper", "label": "Upper abdomen", "icon": "⬆"},
            {"value": "central", "label": "Central / around navel", "icon": "⊙"},
            {"value": "lower_right", "label": "Lower-right", "icon": "↘"},
            {"value": "lower_left", "label": "Lower-left", "icon": "↙"},
            {"value": "none", "label": "No pain / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "Primary Symptoms",
        "name": "pain_onset",
        "type": "enum",
        "prompt": "How did the pain start?",
        "help": "Sudden, sharp pain is more concerning than gradual pain.",
        "options": [
            {"value": "sudden", "label": "Suddenly", "icon": "⚡"},
            {"value": "gradual", "label": "Gradually", "icon": "🌱"},
            {"value": "none", "label": "No pain / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "Primary Symptoms",
        "name": "pain_pattern",
        "type": "enum",
        "prompt": "What pattern does the pain follow?",
        "help": "'Constant' = pain stays steady. 'Comes and goes' = pain in waves. 'Worse when hungry' = ulcer-type pain relieved by eating.",
        "options": [
            {"value": "constant", "label": "Constant", "icon": "━"},
            {"value": "intermittent", "label": "Comes and goes", "icon": "〜"},
            {"value": "worse_when_hungry", "label": "Worse when hungry", "icon": "🍽"},
            {"value": "none", "label": "No pain / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "Digestive Symptoms",
        "name": "nausea",
        "type": "bool",
        "prompt": "Do you have nausea?",
        "help": "A feeling of sickness with an urge to vomit.",
    },
    {
        "group": "Digestive Symptoms",
        "name": "vomiting",
        "type": "bool",
        "prompt": "Have you been vomiting?",
        "help": "Actively throwing up (not just nausea).",
    },
    {
        "group": "Digestive Symptoms",
        "name": "diarrhea",
        "type": "bool",
        "prompt": "Do you have diarrhea?",
        "help": "Frequent, loose, or watery bowel movements.",
    },
    {
        "group": "Digestive Symptoms",
        "name": "constipation",
        "type": "bool",
        "prompt": "Are you constipated?",
        "help": "Difficulty passing stools or infrequent bowel movements.",
    },
    {
        "group": "Digestive Symptoms",
        "name": "loss_of_appetite",
        "type": "bool",
        "prompt": "Have you lost your appetite?",
        "help": "Not feeling hungry even when it's normally time to eat.",
    },
    {
        "group": "Other Symptoms",
        "name": "fever",
        "type": "bool",
        "prompt": "Do you have a fever?",
        "help": "Body temperature above 37.5°C. Fever with abdominal pain can indicate infection or appendicitis.",
    },
    {
        "group": "Other Symptoms",
        "name": "heartburn",
        "type": "bool",
        "prompt": "Do you have heartburn or burning sensation in the chest/throat?",
        "help": "A painful burning feeling in the middle of the chest or up into the throat, often after meals.",
    },
    {
        "group": "Other Symptoms",
        "name": "regurgitation",
        "type": "bool",
        "prompt": "Do you have acid regurgitation?",
        "help": "A sour or bitter-tasting acid rising into the back of your throat or mouth.",
    },
    {
        "group": "Other Symptoms",
        "name": "bloating",
        "type": "bool",
        "prompt": "Do you have bloating or gas?",
        "help": "A feeling of fullness or pressure in the abdomen, often with visible swelling.",
    },
    {
        "group": "Onset & Context",
        "name": "symptom_duration",
        "type": "numeric",
        "prompt": "How many days have symptoms lasted?",
        "help": "Count from when the first symptom began.",
        "unit": "days",
        "min": 0,
        "max": 30,
        "default": 1,
        "context_hint": "Appendicitis typically presents within 1-2 days. Food poisoning resolves in 1-3 days. Chronic conditions like IBS show recurring patterns over weeks.",
        "quick_chips": [
            {"label": "Today", "value": 0},
            {"label": "1 day", "value": 1},
            {"label": "3 days", "value": 3},
            {"label": "1 week", "value": 7},
        ],
    },
    {
        "group": "Onset & Context",
        "name": "symptom_trigger",
        "type": "enum",
        "prompt": "Did symptoms start after eating?",
        "help": "Eating outside or at a shared meal suggests food poisoning. Symptoms after regular meals may indicate reflux or ulcer.",
        "options": [
            {"value": "after_eating_outside", "label": "After eating outside / shared meal", "icon": "🍽"},
            {"value": "after_meals", "label": "After regular meals", "icon": "🍴"},
            {"value": "none", "label": "No specific trigger", "icon": "✖"},
        ],
    },
    {
        "group": "Onset & Context",
        "name": "symptom_history",
        "type": "enum",
        "prompt": "Is this a recurring pattern?",
        "help": "Recurring symptoms over weeks or months suggest chronic conditions like IBS. First-time severe symptoms are more concerning.",
        "options": [
            {"value": "recurring", "label": "Recurring (happened before)", "icon": "🔁"},
            {"value": "first_time", "label": "First time", "icon": "1️⃣"},
        ],
    },
    {
        "group": "Optional Vitals & History",
        "name": "fever_temp",
        "type": "numeric_optional",
        "prompt": "Body temperature (°C) — skip if unknown",
        "help": "Normal: 36.5-37.5°C. Fever above 38°C with abdominal pain is a supporting sign of appendicitis.",
        "unit": "°C",
        "min": 35.0,
        "max": 42.0,
        "default": 37.5,
        "step": 0.1,
        "quick_chips": [
            {"label": "Normal (37°C)", "value": 37.0},
            {"label": "Low (37.8°C)", "value": 37.8},
            {"label": "Moderate (38.6°C)", "value": 38.6},
            {"label": "High (39.5°C)", "value": 39.5},
        ],
    },
    {
        "group": "Optional Vitals & History",
        "name": "nsaid_use",
        "type": "bool_optional",
        "prompt": "Do you regularly use NSAIDs or aspirin?",
        "help": "NSAIDs include ibuprofen, naproxen, and aspirin. Regular use increases the risk of gastric ulcer.",
    },
    {
        "group": "Optional Vitals & History",
        "name": "prior_appendectomy",
        "type": "bool_optional",
        "prompt": "Have you had your appendix removed?",
        "help": "If yes, appendicitis is biologically impossible and will be excluded from consideration.",
    },
]


NEUROLOGICAL_QUESTIONS = [
    {
        "group": "Headache Assessment",
        "name": "headache",
        "type": "bool",
        "prompt": "Do you have a headache?",
        "help": "Pain in any part of your head or neck.",
    },
    {
        "group": "Headache Assessment",
        "name": "headache_location",
        "type": "enum",
        "prompt": "Where is the headache?",
        "help": "One-sided (unilateral) headaches are typical of migraine. Both-sided (bilateral) pressing pain is typical of tension headache.",
        "options": [
            {"value": "unilateral", "label": "One side of head", "icon": "◐"},
            {"value": "bilateral", "label": "Both sides of head", "icon": "◉"},
            {"value": "none", "label": "No headache / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "Headache Assessment",
        "name": "headache_onset",
        "type": "enum",
        "prompt": "How did the headache start?",
        "help": "A 'thunderclap' headache (sudden, severe) is a medical emergency and may indicate bleeding in the brain.",
        "options": [
            {"value": "sudden", "label": "Suddenly (thunderclap)", "icon": "⚡"},
            {"value": "gradual", "label": "Gradually", "icon": "🌱"},
            {"value": "none", "label": "No headache / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "FAST Stroke Screening",
        "name": "facial_drooping",
        "type": "bool",
        "prompt": "Is one side of your face drooping?",
        "help": "The 'F' in FAST. Ask the patient to smile — does one side droop, or not move?",
    },
    {
        "group": "FAST Stroke Screening",
        "name": "arm_weakness",
        "type": "bool",
        "prompt": "Do you have arm or leg weakness?",
        "help": "The 'A' in FAST. Ask the patient to raise both arms — does one drift downward?",
    },
    {
        "group": "FAST Stroke Screening",
        "name": "arm_weakness_side",
        "type": "enum",
        "prompt": "If yes, which side is weak?",
        "help": "Unilateral (one-sided) weakness is a classic stroke sign. Bilateral weakness has other causes.",
        "options": [
            {"value": "unilateral", "label": "One side only", "icon": "◐"},
            {"value": "bilateral", "label": "Both sides", "icon": "◉"},
            {"value": "none", "label": "No weakness / N/A", "icon": "✖"},
        ],
    },
    {
        "group": "FAST Stroke Screening",
        "name": "slurred_speech",
        "type": "bool",
        "prompt": "Is your speech slurred?",
        "help": "The 'S' in FAST. Words sound slurred, mumbled, or hard to pronounce clearly.",
    },
    {
        "group": "FAST Stroke Screening",
        "name": "confused_speech",
        "type": "bool",
        "prompt": "Is your speech confused or hard to understand?",
        "help": "Speaking words that don't make sense, or difficulty finding the right words.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "neck_stiffness",
        "type": "bool",
        "prompt": "Do you have neck stiffness?",
        "help": "Difficulty bending your chin to your chest, or pain when doing so. A sign of meningitis.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "photophobia",
        "type": "bool",
        "prompt": "Are you sensitive to light or sound?",
        "help": "Bright lights or loud sounds make your symptoms worse. Common in migraine and meningitis.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "visual_aura",
        "type": "bool",
        "prompt": "Any visual disturbances or aura before the headache?",
        "help": "Flashing lights, zigzag lines, or blind spots that appear before a headache. Classic migraine sign.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "loss_of_consciousness",
        "type": "bool",
        "prompt": "Have you lost consciousness?",
        "help": "Passing out, fainting, or losing awareness of your surroundings.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "muscle_jerking",
        "type": "bool",
        "prompt": "Any involuntary muscle jerking?",
        "help": "Uncontrolled shaking or jerking movements. Together with loss of consciousness, suggests a seizure.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "dizziness",
        "type": "bool",
        "prompt": "Do you feel dizzy?",
        "help": "Feeling unsteady, lightheaded, or as if the room is spinning.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "balance_loss",
        "type": "bool",
        "prompt": "Any loss of balance?",
        "help": "Difficulty walking straight, or falling.",
    },
    {
        "group": "Other Neurological Signs",
        "name": "fever",
        "type": "bool",
        "prompt": "Do you have a fever?",
        "help": "Fever with headache and neck stiffness is a red flag for meningitis.",
    },
    {
        "group": "Onset",
        "name": "symptom_onset",
        "type": "enum",
        "prompt": "How did symptoms start?",
        "help": "Sudden onset of neurological symptoms is much more concerning than gradual onset.",
        "options": [
            {"value": "sudden", "label": "Suddenly", "icon": "⚡"},
            {"value": "gradual", "label": "Gradually", "icon": "🌱"},
        ],
    },
    {
        "group": "Onset",
        "name": "symptom_duration_minutes",
        "type": "numeric",
        "prompt": "How long ago did symptoms start?",
        "help": "In a stroke, every minute matters. The 4.5-hour window is critical for treatment.",
        "unit": "minutes",
        "min": 0,
        "max": 10080,
        "default": 60,
        "context_hint": "Stroke treatment is most effective within 4.5 hours (270 minutes) of onset. Beyond that window, options narrow significantly.",
        "quick_chips": [
            {"label": "30 minutes", "value": 30},
            {"label": "1 hour", "value": 60},
            {"label": "3 hours", "value": 180},
            {"label": "6 hours", "value": 360},
            {"label": "1 day", "value": 1440},
        ],
    },
    {
        "group": "Patient History",
        "name": "migraine_history",
        "type": "bool_optional",
        "prompt": "Do you have a history of migraines?",
        "help": "A prior migraine diagnosis changes how the system weighs certain symptoms — but never overrides clear stroke warning signs.",
    },
    {
        "group": "Patient History",
        "name": "hypertension_history",
        "type": "bool_optional",
        "prompt": "Do you have a history of hypertension (high blood pressure)?",
        "help": "Hypertension is a major risk factor for stroke and is used to strengthen stroke suspicion.",
    },
    {
        "group": "Patient History",
        "name": "family_history_stroke",
        "type": "bool_optional",
        "prompt": "Family history of stroke?",
        "help": "Having a close family member who has had a stroke increases your own risk.",
    },
]


UI_SCHEMA = {
    "RESPIRATORY": {
        "display_name": "Respiratory & Fever",
        "icon_color": "#60a5fa",      # blue-400
        "accent_color": "#3b82f6",    # blue-500
        "description": "Cough, fever, breathing issues, sore throat",
        "questions": RESPIRATORY_QUESTIONS,
    },
    "GASTROINTESTINAL": {
        "display_name": "Gastrointestinal",
        "icon_color": "#a78bfa",      # violet-400
        "accent_color": "#8b5cf6",    # violet-500
        "description": "Abdominal pain, nausea, digestion issues",
        "questions": GASTROINTESTINAL_QUESTIONS,
    },
    "NEUROLOGICAL": {
        "display_name": "Neurological",
        "icon_color": "#f472b6",      # pink-400
        "accent_color": "#ec4899",    # pink-500
        "description": "Headache, weakness, speech issues, seizures",
        "questions": NEUROLOGICAL_QUESTIONS,
    },
}


# Smart-skip rules: if (parent, value) is answered, skip these child fields
SMART_SKIPS = {
    "RESPIRATORY": {
        ("fever", "no"): ["fever_temp"],
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


# Diagnosis -> anatomy region highlighting instructions
# Each region ID matches an element in the SVG anatomy illustrations
DIAGNOSIS_HIGHLIGHTS = {
    # RESPIRATORY
    "Common Cold":   {"regions": ["nose", "throat"], "intensity": "mild"},
    "Influenza":     {"regions": ["throat", "chest"], "intensity": "moderate"},
    "COVID-19":      {"regions": ["nose", "throat", "chest"], "intensity": "moderate"},
    "Strep Throat":  {"regions": ["throat"], "intensity": "moderate"},
    "Pneumonia":     {"regions": ["left-lung", "right-lung"], "intensity": "severe"},
    "Bronchitis":    {"regions": ["bronchi"], "intensity": "moderate"},
    # GASTROINTESTINAL
    "Gastroenteritis":{"regions": ["stomach", "small-intestine"], "intensity": "moderate"},
    "Food Poisoning":{"regions": ["stomach", "small-intestine"], "intensity": "moderate"},
    "Appendicitis":  {"regions": ["appendix"], "intensity": "severe"},
    "Gastric Ulcer": {"regions": ["stomach"], "intensity": "moderate"},
    "IBS":           {"regions": ["large-intestine"], "intensity": "mild"},
    "Acid Reflux":   {"regions": ["esophagus", "stomach"], "intensity": "mild"},
    # NEUROLOGICAL
    "Tension Headache":{"regions": ["brain-outer"], "intensity": "mild"},
    "Migraine":      {"regions": ["brain-left"], "intensity": "moderate"},
    "Meningitis":    {"regions": ["meninges"], "intensity": "severe"},
    "Stroke":        {"regions": ["brain-right"], "intensity": "severe"},
    "Vertigo":       {"regions": ["inner-ear"], "intensity": "moderate"},
    "Epilepsy":      {"regions": ["brain-outer"], "intensity": "severe"},
}


# Severity color mapping
SEVERITY_COLORS = {
    "mild":     "#10b981",  # green-500
    "moderate": "#f59e0b",  # amber-500
    "severe":   "#ef4444",  # red-500
    "emergency":"#dc2626",  # red-600
}


# Urgency -> color + label
URGENCY_STYLES = {
    "LOW":       {"color": "#10b981", "label": "Low - Self-care"},
    "MODERATE":  {"color": "#f59e0b", "label": "Moderate - See a physician"},
    "HIGH":      {"color": "#ef4444", "label": "High - Urgent medical care"},
    "EMERGENCY": {"color": "#dc2626", "label": "EMERGENCY - Call ambulance"},
}
