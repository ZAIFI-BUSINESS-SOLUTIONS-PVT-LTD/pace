# Pace Analytics: Execution & Architecture Guidelines

**Status**: SYSTEM FUNCTIONALLY COMPLETE (Phases 0, 1, 2, 3 Implemented)
**Last Updated**: 2025-12-20

---

## 1. Project Philosophy & strictly Enforced Boundaries

This project generates educational insights from raw student data. It operates on a strict **Phase-Based Architecture**.

### Core Invariants
1.  **Phase Immutability**: Later phases **never** modify the outputs of earlier phases. Phase 1 is ground truth. Phase 2 is reasoning. Phase 3 is synthesis.
2.  **Truth vs. Reasoning**:
    *   **Phase 0 & 1** establishes **TRUTH** (What was asked? What is the answer? What did the student click?). This is mechanical and deterministic.
    *   **Phase 2 & 3** generates **REASONING** (Why did they mistake this? What should the teacher do?). This is probabilistic (LLM-based).
3.  **One-Way Data Flow**: Data flows `Phase 0 -> Phase 1 -> Phase 2 -> Phase 3`. No loops.

---

## 2. Prompt Management Strategy

Prompts in this system are **configuration**, not code.

*   **Centralization**: All LLM prompts must reside in `src/prompts.py`.
*   **Usage**: Execution code must import prompts (e.g., `from src.prompts import PHASE_2_ANALYSIS_PROMPT`).
*   **Prohibition**: **NEVER** inline prompt text inside logic files (`.py`).
*   **Stability**: Changing a prompt requires a configuration update, not a logic refactor.

---

## 3. Phase Details

### Phase 0: Case 0 (Ingestion & Normalization)
**Objective**: Standardize messy client inputs into a strict schema.
**Input**: Raw Excel/PDFs in `client_uploads/`.
**Output**: `normalized_inputs/<class_id>/ResponseSheet.csv`.

**The ResponseSheet Contract (Non-Negotiable)**:
*   The `ResponseSheet.csv` generated here is the **Final Authoritative Record** of student actions.
*   **Schema**:
    *   **Index**: `question_id` (Q1, Q2, ...).
    *   **Columns**: `student_id` (Student IDs).
    *   **Values**: `A`, `B`, `C`, `D`, or `empty` (unattempted).
*   **Downstream Rules**: No future phase generally alters this data. Interpretations of "guessing" occur in Phase 2, but the raw click is fixed here.

### Phase 1: Case 1 (Ground Truth Extraction)
**Objective**: Extract Question Paper and Solutions into structured JSON.
**Input**: `QuestionPaper.pdf`, `Solutions.pdf` / `AnswerKey.csv`.
**Output**: `output/<class_id>/phase1/merged.json`.
**Logic**:
*   PDF parsing via Gemini (Vision/Text).
*   Mechanical merge of Questions + Solutions.
*   **Strict Verification**: 100% of questions must have a solution key.

### Phase 2: Case 2 (Student-Level Reasoning)
**Objective**: Analyze *individual* student performance.
**Input**: `merged.json` (Case 1) + `ResponseSheet.csv` (Case 0).
**Output**: 
*   `output/<class_id>/phase2/student_question_insights.csv` (Micro-level).
*   `output/<class_id>/phase2/student_insight_summary.csv` (Macro-level).
**Logic**:
*   **Packetization**: Create a "Packet" per student (Questions + Student Choice + Solution).
*   **LLM Call**: **One call per student**.
*   **Constraints**: The LLM analyzes *why* a mistake happened but cannot change *if* it happened.

### Phase 3: Case 3 (Class-Level Synthesis)
**Objective**: Synthesize aggregate teacher guidance from student insights.
**Input**: `output/<class_id>/phase2/student_insight_summary.csv`.
**Output**: `output/class_level_focus_and_action.csv`.

**Logic**:
*   **One Call Per Class**: Gemini analyzes the entire class's Phase 2 summary in one pass.
*   **Privacy**: System does NOT mention specific students.
*   **Focus Zones**: Aggregates recurring misunderstandings (e.g., "70% failed Atomic Structure").
*   **Action Plans**: Prescriptive teacher guidance (e.g., "Revise unit conversions using visual aids").

**Final Output Schema (CSV)**:
*   `class_id`
*   `focus_zone_1`
*   `focus_zone_2`
*   `focus_zone_3`
*   `action_plan_1`
*   `action_plan_2`
*   `action_plan_3`

---

## 4. Execution Workflow

To run the full pipeline:

1.  **Setup**: Place files in `client_uploads/`.
2.  **Phase 0**: `python case0.py` (Normalizes inputs).
3.  **Phase 1**: `python case1.py` (Extracts ground truth).
4.  **Phase 2**: `python case2.py` (Generates student insights).
5.  **Phase 3**: `python case3.py` (Synthesizes class plans).

*Note: Use `TARGET_CLASS` env var to run specific classes.*

---

## 5. System Status

| Phase | Status | Notes |
| :--- | :--- | :--- |
| **Phase 0** | **COMPLETE** | Ingestion operational. |
| **Phase 1** | **COMPLETE** | Extraction & Merging operational. Prompt centralized. |
| **Phase 2** | **COMPLETE** | Student Analysis operational. Prompt centralized. |
| **Phase 3** | **COMPLETE** | Class Synthesis operational. Output verified. Prompt centralized. |


---

## 6. Configuration Reference

The system behavior is controlled via environment variables in `.env`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | **Required** | Google Gemini API Key. |
| `TARGET_CLASS` | `class_medical` | Steps run ONLY for this class if set. Set to blank/None to run all. |
| `MODEL_NAME` | `gemini-3.0-flash` | The specific Gemini model version to use. |
| `RESPONSE_TYPE` | `BOTH` | `ONLINE` (read Response_Online.xlsx), `OFFLINE` (Offline.xlsx), or `BOTH`. |

---


---

## 7. Directory Map & Data Flow

Understanding the folder roles is critical for strict execution.

### Project Folder Structure

```text
pace_analytics/
├── .env                        # Configuration variables
├── case0.py                    # Phase 0 Entry Point
├── case1.py                    # Phase 1 Entry Point
├── case2.py                    # Phase 2 Entry Point
├── case3.py                    # Phase 3 Entry Point
├── src/
│   ├── phase0/                 # Ingestion Logic
│   ├── phase1/                 # Extraction Logic
│   ├── phase2/                 # Student Analysis Logic
│   ├── phase3/                 # Class Synthesis Logic
│   └── prompts.py              # CENTRALIZED PROMPT REGISTRY
├── client_uploads/             # [DROP ZONE] User places raw files here
│   ├── responses/
│   │   └── Response_Online.xlsx
│   └── class_10 FB/
│       └── QuestionPaper.pdf
├── input/                      # [GENERATED SOURCE] Phase 0 writes valid files here
│   └── class_10 FB/
│       ├── ResponseSheet.csv
│       ├── answer_key.json
│       └── QuestionPaper.pdf
└── output/                     # [ARTIFACTS] System generation targets
    ├── class_level_focus_and_action.csv  # Phase 3 Final Output
    └── class_10 FB/
        ├── phase1/             # derived json truth
        │   ├── merged.json
        │   ├── questionpaper.json
        │   └── solution.json
        └── phase2/             # student insights
            ├── student_insight_summary.csv
            └── student_question_insights.csv
```

### Key Directory Responsibilities

*   **`client_uploads/`**: Use this for **Manual Data Entry**.
    *   Create a folder matching the Class ID (e.g., `class_10`).
    *   Place `QuestionPaper.pdf` inside it.
    *   Ensure the class name matches a sheet in `responses/Response_Online.xlsx`.

*   **`normalized_inputs/`** (Hidden): Use this for **Debugging Phase 0**.
    *   Intermediate staging area where messy inputs are cleaned before promotion to `input/`.

*   **`input/`**: Use this for **Phase 1 Execution**.
    *   Phase 1 reads ONLY from here.
    *   Contains the strict canonical files (`ResponseSheet.csv`, `QuestionPaper.pdf`).

*   **`output/`**: Use this for **Consuming Results**.
    *   Contains all generated JSONs and CSVs suitable for UI or reporting.
    *   Phase 3 writes the final class-level summary at the root of this folder.


---

## 8. Troubleshooting & Common Failures

*   **"QuestionPaper.pdf not found"**: Phase 0 requires this exact filename in `client_uploads/<class_folder>/`.
*   **"Verification Failed: File too small"**: Indicates extraction step failed or input was empty.
*   **API Errors**: Check `GEMINI_API_KEY`. If quota exceeded, system logs error but may skip student.
*   **Strict Naming**: Class folders in `client_uploads` must usually match the sheet names in the Response Excel for Phase 0 to link them.

