# Medical Diagnosis Expert System

**AIE212 — Phase 4 | Alamein International University**
Dr. Essam Abdellatef · Spring 2025/2026

---

## What it is

A Rule-Based Expert System with Certainty Factors for medical triage.
Forward Chaining + Lowest Index CR. 29 rules across 3 domains:
Respiratory, Gastrointestinal, Neurological.

Two interfaces, same engine:
- **CLI** — terminal with colored trace tables
- **Web** — browser dashboard with anatomy illustrations

---

## How to run

**1. Install once:**
```
pip install colorama flask
```

**2. Navigate to project folder** in Anaconda Prompt or VS Code terminal:
```
cd path\to\this\folder
```

**3. Run CLI version:**
```
python main.py --demo stroke
```
Other demos: `cold`, `flu_vaccinated`, `pneumonia`, `appendicitis`, `food_poisoning`, `migraine`.
Or run `python main.py` for interactive mode.

**4. Run Web version:**
```
python app.py
```
Then open your browser to `http://localhost:5000`.

---

## Quick fixes

- `No module named X` → `pip install X`
- `scripts disabled` (PowerShell) → `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Browser can't connect → make sure `python app.py` is still running
- Port 5000 busy → edit last line of `app.py`, change `port=5000` to `port=5001`
