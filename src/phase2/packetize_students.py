import json
import os
import logging
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.csv_loader import load_student_responses

logger = setup_logger(__name__)

def process():
    logger.info("Starting Packetization...")
    
    # Paths
    merged_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "merged.json")
    qa_analysis_path = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1", "student_question_analysis.csv")
    
    if not os.path.exists(qa_analysis_path):
        logger.error(f"Phase 1 Analysis CSV not found: {qa_analysis_path}")
        return []

    # Load Merged Data for static content (Text, Options, Solution Text)
    # Phase 2 reader expects list in merged.json, verify
    with open(merged_path, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Create a map for quick lookup: QID -> Details
    # We only take static fields from here. Correctness/Concept comes from CSV Analysis.
    q_map = {q.get("question_id"): q for q in questions_data}
    
    # Load Student Analysis CSV (The "Truth" for performance tags)
    try:
        df_analysis = pd.read_csv(qa_analysis_path)
    except Exception as e:
        logger.error(f"Failed to read student analysis CSV: {e}")
        return []
    
    packets = []
    
    # Group by student_id
    if df_analysis.empty:
        logger.warning("Student analysis CSV is empty.")
        return []

    grouped = df_analysis.groupby("student_id")
    
    for student_id, group in grouped:
        student_packet = {
            "student_id": str(student_id),
            "questions": []
        }
        
        for _, row in group.iterrows():
            q_id = str(row["question_id"])
            
            # Static details from merged.json
            static_details = q_map.get(q_id, {})
            
            # Mismatch check?
            if not static_details:
                logger.warning(f"Question {q_id} in analysis CSV but not in merged.json. Skipping.")
                continue
            
            # Build Question Item using CSV as TRUTH for dynamic fields
            # and merged.json for static fields.
            
            # Map 'selected_option' (CSV) to 'student_selected_option' (Packet Schema)
            # Map 'attempted' (CSV) -> boolean (CSV might read as True/False string or bool)
            is_attempted = bool(row.get("attempted", False))
            
            question_item = {
                "question_id": q_id,
                "question_text": static_details.get("question_text", ""),
                "options": static_details.get("options", []),
                
                # TRUTH FIELDS (Read-Only later)
                "correct_option": str(row.get("correct_option", "UNKNOWN")),
                "student_selected_option": str(row.get("selected_option", "")) if pd.notna(row.get("selected_option")) else "",
                "attempted": is_attempted,
                "is_correct": bool(row.get("is_correct", False)),
                "difficulty_tag": str(row.get("difficulty_tag", "Unknown")),
                "key_concept": str(row.get("key_concept", "")),
                
                "solution_text": static_details.get("solution_text", "")
            }
            
            student_packet["questions"].append(question_item)
            
        if student_packet["questions"]:
            packets.append(student_packet)
        
    return packets

if __name__ == "__main__":
    packets = process()
    print(f"Generated {len(packets)} packets")
    print(json.dumps(packets[0], indent=2))
