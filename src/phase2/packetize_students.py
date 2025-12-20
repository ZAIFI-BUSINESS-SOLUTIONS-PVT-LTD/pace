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
    response_path = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS, "ResponseSheet.csv")
    
    # Load Merged Data
    with open(merged_path, 'r', encoding='utf-8') as f:
        questions_data = json.load(f)
    
    # Create a map for quick lookup: QID -> Details
    q_map = {q.get("question_id"): q for q in questions_data}
    
    # Load Responses
    df_responses = load_student_responses(response_path)
    
    packets = []
    
    for student_id, row in df_responses.iterrows():
        student_packet = {
            "student_id": str(student_id),
            "questions": []
        }
        
        for q_id in row.index:
            if not str(q_id).startswith("Q"):
                continue # Skip non-question columns
                
            selected_option = row[q_id]
            
            # Handle NaN/None/Empty
            if pd.isna(selected_option) or str(selected_option).strip() == "":
                continue # Skip unattempted
            
            # Use 'merged.json' details
            q_details = q_map.get(str(q_id))
            if not q_details:
                logger.warning(f"Question {q_id} found in response but not in merged.json")
                continue
                
            question_item = {
                "question_id": q_id,
                "question_text": q_details.get("question_text", ""),
                "options": q_details.get("options", []),
                "correct_option": q_details.get("correct_option", "UNKNOWN"),
                "student_selected_option": str(selected_option),
                "attempted": True,
                "solution_text": q_details.get("solution_text", ""),
                "key_concept": q_details.get("key_concept", ""),
                # "difficulty_tag": "" # Not in Phase 1 output, skipping as per rules (only available info)
            }
            
            student_packet["questions"].append(question_item)
            
        packets.append(student_packet)
        
    return packets

if __name__ == "__main__":
    packets = process()
    print(f"Generated {len(packets)} packets")
    print(json.dumps(packets[0], indent=2))
