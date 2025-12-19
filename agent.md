# agent.md

## Pace Academy × InzightEd — Insights SPA Agent

---

## 1. Purpose of This Agent

This agent defines the **single-page application (SPA)** behavior for displaying **student-level and class-level insights** generated from Phase 1 and Phase 2 pipelines.

It does **not** generate analytics.
It **consumes final CSV outputs** and renders them into a **decision-grade interface**.

The goal is **clarity, not beauty**.

---

## 2. Core Philosophy (Non-Negotiable)

* Less text, more signal
* Fixed zones ≠ small cards
* Focus & Steady = compact, scannable
* Fix It Zone = **deep, expandable, scrollable**
* Same insight logic at **student level and class level**

This UI is for **teachers and institutions**, not students alone.

---

## 3. Primary Insight Zones (Canonical Naming)

The system exposes **four canonical insight blocks**.

### 3.1 Focus Zone

**Meaning:** What is working well

Derived from:

* Strongest concepts
* High accuracy areas

Rules:

* Max **3 bullet points**
* Each bullet ≤ **6–7 words**
* No explanations

Used at:

* Student level
* Class level

---

### 3.2 Steady Zone (S-T-E-A-D-Y)

**Meaning:** Acceptable but fragile areas

Derived from:

* Medium accuracy concepts
* Inconsistent performance

Rules:

* Max **3 bullet points**
* Positioned **beside Focus Zone**
* No alarm language

Used at:

* Student level
* Class level

---

### 3.3 Fix It Zone

**Meaning:** What is breaking performance and why

Derived from:

* Dominant mistake patterns
* LLM summaries
* Long-form explanations

Rules:

* **Never shown as a small card**
* Always **expandable / collapsible**
* Scrollable content allowed
* Can contain:

  * Paragraphs
  * Bullet points
  * Recommendations

Used at:

* Student level (primary)
* Class level (aggregated)

---

### 3.4 Action Plan

**Meaning:** What to do next

Derived from:

* Fix It Zone
* Pattern frequency

Rules:

* 3–5 steps max
* Imperative language
* No theory

Used at:

* Class level only (default)
* Optional at student level

---

## 4. Levels of Insight

### 4.1 Class Level (Institute View)

Shown when:

* A class is selected
* No student is selected

Must display:

* Class Accuracy %
* Focus Zone (class)
* Steady Zone (class)
* Action Plan
* Student Performance Summary table

Must NOT display:

* Fix It Zone as cards
* Individual explanations inline

---

### 4.2 Student Level

Shown when:

* A student is selected

Must display:

* Student Accuracy %
* Focus Zone (student)
* Steady Zone (student)
* Fix It Zone (expanded section)
* Student summary (LLM)

This is the **primary view** and must have **more screen width**.

---

## 5. Layout Rules (Hard)

### Global

* Single Page Application
* Black & white friendly
* No charts required

---

### Top Bar

* Pace Academy logo (left)
* InzightEd branding (right)
* Class selector dropdown (mandatory)

---

### Left Panel — Class Overview (Narrower)

Contains:

* Class Accuracy
* Focus Zone (class)
* Action Plan
* Class Performance Summary table

Does NOT contain:

* Fix It Zone
* Long text blocks

---

### Right Panel — Student Analysis (Wider)

Contains:

* Student selector
* Student Accuracy
* Focus Zone + Steady Zone (side by side)
* Fix It Zone (expandable, bottom-anchored)

This panel owns **depth**.

---

## 6. Data Contracts (Consumed Only)

The UI consumes **final outputs only**:

### From Phase 1

* `student_summary.csv`
* `question_summary.csv`

### From Phase 2

* `student_question_insights.csv`
* `student_insight_summary.csv`

No raw PDFs.
No JSON parsing in frontend.

---

## 7. Behavior Rules

* If no student selected → class view
* If student selected → student view overrides
* If Fix It Zone content is empty → hide section
* If concepts = UNKNOWN → suppress label

No placeholders shown to users.

---

## 8. Explicit Non-Goals

This agent does NOT:

* Predict ranks
* Show scores over time
* Explain syllabus
* Replace teachers
* Beautify language

This UI exists to **reduce cognitive load**.

---

## 9. Success Criteria

This agent is successful if:

* A teacher can identify:

  * What’s strong
  * What’s stable
  * What’s broken
  * What to fix next
    in **under 30 seconds**

If it takes more, the UI has failed.

---

## 10. Handoff Note

This `agent.md` is the **single source of truth** for:

* Wireframe behavior
* SPA logic
* Insight placement

The **Mega Prompt** will:

* Translate this into UI scaffolding

The **Execution Prompt** will:

* Bind real data and render

---