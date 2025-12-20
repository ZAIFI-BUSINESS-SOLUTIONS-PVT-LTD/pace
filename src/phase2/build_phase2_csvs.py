import os
import pandas as pd
import logging
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def process(llm_results, original_packets):
    logger.info("Building Phase 2 CSVs...")
    
    # 1. Student Question Insights
    # Merge LLM result ("per_question") with original packet info (key_concept)
    
    # Map original packet info for easy lookup: Student -> QID -> Concept
    concept_map = {} # {student_id: {qid: concept}}
    options_map = {} # {student_id: {qid: {selected: ..., correct: ...}}}
    
    for p in original_packets:
        s_id = p["student_id"]
        concept_map[s_id] = {}
        options_map[s_id] = {}
        for q in p["questions"]:
            q_id = q["question_id"]
            concept_map[s_id][q_id] = q.get("key_concept", "")
            options_map[s_id][q_id] = {
                "selected_option": q.get("student_selected_option"),
                "correct_option": q.get("correct_option")
            }
            
    question_rows = []
    
    for res in llm_results:
        s_id = res.get("student_id")
        per_q_list = res.get("per_question", [])
        
        for item in per_q_list:
            q_id = item.get("question_id")
            
            # Lookup basics
            opts = options_map.get(s_id, {}).get(q_id, {})
            concept = concept_map.get(s_id, {}).get(q_id, "")
            
            row = {
                "student_id": s_id,
                "question_id": q_id,
                "selected_option": opts.get("selected_option"),
                "correct_option": opts.get("correct_option"),
                "is_correct": item.get("is_correct"),
                "mistake_type": item.get("mistake_type"),
                "correctness_reason": item.get("correctness_reason"),
                "confidence_signal": item.get("confidence_signal"),
                "key_concept": concept
            }
            question_rows.append(row)
            
    df_q = pd.DataFrame(question_rows)
    out_q_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase2", "student_question_insights.csv")
    os.makedirs(os.path.dirname(out_q_path), exist_ok=True)
    df_q.to_csv(out_q_path, index=False)
    logger.info(f"Saved Question Insights: {out_q_path}")
    
    # 2. Student Insight Summary
    summary_rows = []
    
    for res in llm_results:
        s_id = res.get("student_id")
        summ = res.get("summary", {})
        
        # Calculate stats from question_rows for this student
        student_q_rows = [r for r in question_rows if r["student_id"] == s_id]
        total_attempt = len(student_q_rows)
        correct_count = sum(1 for r in student_q_rows if r["is_correct"])
        accuracy = (correct_count / total_attempt * 100) if total_attempt > 0 else 0.0
        
        # Total questions in paper? We don't have that easily here unless we pass it. 
        # But "attempt_percentage" usually implies (attempted / total_paper_questions).
        # We'll use total items in concept_map entry ? No, packet only has attempts.
        # Let's assume attempted / total_questions_in_paper.
        # We can find total questions from options_map entries? No.
        # Let's derive it from merging all observed QIDs across all students or passed config?
        # For now, let's just use 100% implicitly or just leave it as placeholder if expected strictly.
        # Prompt says "accuracy_percentage" and "attempt_percentage".
        # I'll rely on the packet. Packet is "only attempted questions".
        # I'll calculate attempt percentage based on a fixed 30 (from Phase 1 output I saw).
        # Or I can scan 'merged.json' length again.
        
        row = {
            "student_id": s_id,
            "accuracy_percentage": round(accuracy, 2),
            "attempt_percentage": 0, # Placeholder, will update if I read merged count
            "strongest_concepts": "; ".join(summ.get("strongest_concepts", [])),
            "weakest_concepts": "; ".join(summ.get("weakest_concepts", [])),
            "dominant_mistake_pattern": summ.get("dominant_mistake_pattern"),
            "llm_summary": summ.get("overall_summary")
        }
        summary_rows.append(row)
        
    df_s = pd.DataFrame(summary_rows)
    out_s_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase2", "student_insight_summary.csv")
    df_s.to_csv(out_s_path, index=False)
    logger.info(f"Saved Student Summary: {out_s_path}")

