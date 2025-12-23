import os
import json
import logging
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def process():
    logger.info("Starting Phase 1: Merge Data")
    
    qp_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "questionpaper.json")
    sol_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "solution.json")
    output_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "merged.json")
    
    if not os.path.exists(qp_path):
        raise FileNotFoundError(f"Question Paper JSON not found: {qp_path}")
    if not os.path.exists(sol_path):
        raise FileNotFoundError(f"Solution JSON not found: {sol_path}")
        
    # Read QP (Wrapped in "questions")
    with open(qp_path, 'r', encoding='utf-8') as f:
        qp_data = json.load(f)
        questions = qp_data.get("questions") if isinstance(qp_data, dict) else qp_data
    
    # Read Sol (Wrapped in "solutions")
    with open(sol_path, 'r', encoding='utf-8') as f:
        sol_data = json.load(f)
        solutions = sol_data.get("solutions") if isinstance(sol_data, dict) else sol_data
        
    # Index solutions by question_id    
    sol_map = {s.get("question_id"): s for s in solutions if s.get("question_id")}
    
    merged_data = []
    
    for q in questions:
        q_id = q.get("question_id")
        if not q_id:
            logger.warning(f"Question without ID: {q}")
            continue
            
        merged_item = q.copy()
        
        if q_id in sol_map:
            sol = sol_map[q_id]
            merged_item["correct_option"] = sol.get("correct_option", "UNKNOWN")
            merged_item["solution_text"] = sol.get("solution_text", "")
            merged_item["key_concept"] = sol.get("key_concept", "")
        else:
            logger.warning(f"No solution mapping found for: {q_id}")
            # Step 5: Fail fast if missing correct_option?
            # Prompt says "Any question is missing correct_option" -> FAIL
            logger.error(f"CRITICAL: Question {q_id} missing correct_option mapping!")
            raise ValueError(f"Question {q_id} missing correct_option mapping")
            
        merged_data.append(merged_item)
        
    logger.info(f"Merged {len(merged_data)} items.")
    
    # Save merged.json (List format - Phase 2 compatibility)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4)
        
    logger.info(f"Saved to {output_path}")

    # --- Step 4: ResponseSheet Ingestion & Analysis ---
    response_path = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS, "ResponseSheet.csv")
    if not os.path.exists(response_path):
        logger.error(f"CRITICAL: ResponseSheet.csv missing in {Config.INPUT_DIR}/{Config.DEFAULT_CLASS}")
        raise FileNotFoundError(f"ResponseSheet.csv missing")

    logger.info(f"Processing ResponseSheet: {response_path}")
    
    # Read CSV
    try:
        # Phase 0 produces Question x Student matrix with 'question_id' as index/first col
        # Phase 1 logic below expects Student x Question (Rows=Students)
        # So we Transpose.
        df_resp = pd.read_csv(response_path, index_col=0)
        df_resp = df_resp.T
    except Exception as e:
        logger.error(f"Failed to read ResponseSheet.csv: {e}")
        raise

    # Validation: columns
    # After transpose, columns are Question IDs (1, 2, 3...)
    
    # Check if we have at least one question column
    q_cols = [c for c in df_resp.columns if str(c).strip().upper().startswith("Q") or str(c).strip().isdigit()]
    if not q_cols:
         # Maybe format is different? But Phase 2 reads it.
         pass
         
    # Generate CSVs
    # 1. student_question_analysis.csv
    student_analysis_rows = []
    
    # Map q_id -> details from merged_data
    # We need correct_option and key_concept
    merged_map = {m["question_id"]: m for m in merged_data}
    
    # We iterate rows (Students)
    for idx, row in df_resp.iterrows():
        # Index is the Student ID
        student_id = str(idx)
            
        for col in df_resp.columns:
            # We need to normalize col to question_id 'Qx'
            q_id_check = str(col).strip().upper()
            if not q_id_check.startswith("Q") and q_id_check.isdigit():
                q_id_check = f"Q{q_id_check}"
            
            if q_id_check in merged_map:
                # It is a question column
                selected = str(row[col]).strip().upper() if pd.notna(row[col]) else ""
                
                # Get details from map
                q_details = merged_map[q_id_check]
                correct = q_details.get("correct_option")
                key_concept = q_details.get("key_concept", "")
                
                is_correct = (selected == correct) if selected else False
                attempted = True if selected else False
                
                if not selected:
                    # Unattempted
                    status = "Unattempted"
                    is_correct = False
                else:
                    status = "Correct" if is_correct else "Incorrect"
                
                student_analysis_rows.append({
                    "student_id": student_id,
                    "question_id": q_id_check,
                    "selected_option": selected,
                    "correct_option": correct,
                    "is_correct": is_correct,
                    "status": status,
                    "attempted": attempted,
                    "key_concept": key_concept
                })

    df_analysis = pd.DataFrame(student_analysis_rows)
    
    # Add difficulty_tag
    if not df_analysis.empty:
        # Calculate accuracy per question: Mean of boolean is_correct * 100
        # groupby question_id
        q_stats = df_analysis.groupby("question_id")["is_correct"].mean() * 100
        
        def get_diff_tag(acc):
            if acc >= 70: return "Easy"
            elif acc >= 40: return "Medium"
            else: return "Hard"
            
        q_diff_map = q_stats.apply(get_diff_tag).to_dict()
        df_analysis["difficulty_tag"] = df_analysis["question_id"].map(q_diff_map)
    else:
        # Empty case, just add column
        df_analysis["difficulty_tag"] = []

    analysis_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "student_question_analysis.csv")
    df_analysis.to_csv(analysis_path, index=False)
    logger.info(f"Generated {analysis_path}")
    
    # 2. student_summary.csv
    if not df_analysis.empty:
        # Group by student_id
        summary_rows = []
        grouped = df_analysis.groupby("student_id")
        for sid, group in grouped:
            total = len(group)
            attempted = len(group[group["status"] != "Unattempted"])
            correct_count = len(group[group["is_correct"] == True])
            incorrect_count = attempted - correct_count
            score_pct = (correct_count / total * 100) if total > 0 else 0.0
            
            summary_rows.append({
                "student_id": sid,
                "total_questions": total,
                "attempted": attempted,
                "correct": correct_count,
                "incorrect": incorrect_count,
                "score_percentage": round(score_pct, 2)
            })
            
        df_summary = pd.DataFrame(summary_rows)
        summary_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "student_summary.csv")
        df_summary.to_csv(summary_path, index=False)
        logger.info(f"Generated {summary_path}")
    else:
        logger.warning("No analysis data generated, skipping student_summary.csv")

    # 3. question_summary.csv
    if not df_analysis.empty:
        q_summary_rows = []
        q_grouped = df_analysis.groupby("question_id")
        for qid, group in q_grouped:
            total = len(group) # number of students
            correct_count = len(group[group["is_correct"] == True])
            accuracy = (correct_count / total * 100) if total > 0 else 0.0
            
            q_summary_rows.append({
                "question_id": qid,
                "total_students": total,
                "correct_count": correct_count,
                "accuracy_percentage": round(accuracy, 2)
            })
            
        df_q_summary = pd.DataFrame(q_summary_rows)
        q_summary_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "question_summary.csv")
        df_q_summary.to_csv(q_summary_path, index=False)
        logger.info(f"Generated {q_summary_path}")

if __name__ == "__main__":
    process()
