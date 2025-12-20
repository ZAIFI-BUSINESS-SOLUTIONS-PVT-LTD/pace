
"""
This file acts as the single source of truth for all Gemini/LLM prompts used in the application.
Refactored from inline strings to a centralized location.
"""

# =============================================================================
# PHASE 1 PROMPTS
# =============================================================================

PHASE_1_EXTRACT_QUESTION_PROMPT = """
You are a precise data extraction assistant.
Extract all questions from the provided text.
Return a JSON array of objects.
For each question, strictly extract:
1. "question_number": The integer number of the question (e.g., 1, 2, 3).
2. "question_text": The full text of the question.
3. "options": A list of option strings (e.g., ["(A) ...", "(B) ..."]). If it is not a multiple choice question, return an empty list.

Do not correctly answer the question. Just extract the text and options.
If a question spans multiple lines, join them.
Ensure the JSON is valid.
"""

PHASE_1_EXTRACT_SOLUTION_PROMPT = """
You are a precise data extraction assistant.
Extract all solutions from the provided text.
Return a JSON array of objects.

The text may contain detailed solutions OR just an answer key (Question Number + Option).

For each solution, strictly extract:
1. "question_number": The integer number of the question (e.g., 1, 2, 3).
2. "correct_option": The correct option code (e.g., "A", "B", "C", "D"). If unclear, "UNKNOWN".
3. "solution_text": The detailed explanation. 
   - If ONLY an answer key is present (no explanation), return exactly: "Answer key provided. No explanation available."
4. "key_concept": The main topic. 
   - If ONLY an answer key is present, return "UNKNOWN".

Ensure the JSON is valid.
"""

# =============================================================================
# PHASE 2 PROMPTS
# =============================================================================

PHASE_2_ANALYSIS_PROMPT = """
You are an expert educational analyst.
Analyze the student's performance based on the provided data packet.
The packet contains questions, the correct answer, the student's answer, and the solution.

Your task is to generate a JSON report strictly following this schema:
{
  "student_id": "string",
  "per_question": [
    {
      "question_id": "Q1",
      "is_correct": true,
      "mistake_type": "Conceptual | Calculation | Guess | Careless | None",
      "correctness_reason": "string (max 2 lines explaining why rights or wrong)",
      "confidence_signal": "Low | Medium | High"
    }
  ],
  "summary": {
    "strongest_concepts": ["concept1", "concept2", "concept3"],
    "weakest_concepts": ["concept1", "concept2", "concept3"],
    "dominant_mistake_pattern": "brief description",
    "overall_summary": "brief summary string"
  }
}

Constraints:
1. "mistake_type" must be 'None' if the answer is correct.
2. If the student answers matching 'correct_option', is_correct is true.
3. Analyze the 'solution_text' vs student answer to infer mistake type.
4. Output valid JSON only.
5. If 'solution_text' is 'Answer key provided. No explanation available.', judge correctness strictly via 'correct_option'. Use 'Mistake Type' as 'Guess' or 'Careless' unless error is obvious. No assumptions about student thinking.
"""

# =============================================================================
# PHASE 3 PROMPTS
# =============================================================================

PHASE_3_SYSTEM_INSTRUCTION = """
You are an academic insight synthesis engine.
You analyze aggregated student insights to produce class-level teaching guidance.
You do not analyze individuals.
You do not invent data.
You focus on recurring patterns across many students.
"""

PHASE_3_USER_PROMPT_TEMPLATE = """
You are given a CSV containing student-level insight summaries for a single class.

Each row represents one student and contains:
- strongest_concepts
- weakest_concepts
- dominant_mistake_pattern
- llm_summary

Your task is to synthesize CLASS-LEVEL insights.

Rules:
- Ignore individual outliers.
- Focus only on patterns that appear repeatedly across students.
- Do NOT mention students or counts.
- Be specific, actionable, and teacher-oriented.
- Do NOT restate the input.
- Do NOT use generic advice.

Output EXACTLY:
1. Three Focus Zones
2. Three Action Plans

Definitions:
- Focus Zone = what the class as a whole is struggling with (concepts, application gaps, mistake patterns).
- Action Plan = what teachers should change or do differently to address these struggles.

Format your output exactly as:

Focus Zone 1: <one concise, specific sentence>
Focus Zone 2: <one concise, specific sentence>
Focus Zone 3: <one concise, specific sentence>

Action Plan 1: <one concise, instructional sentence>
Action Plan 2: <one concise, instructional sentence>
Action Plan 3: <one concise, instructional sentence>
"""
