import os
import json
import logging
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
        
    with open(qp_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    with open(sol_path, 'r', encoding='utf-8') as f:
        solutions = json.load(f)
        
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
            merged_item["correct_option"] = "UNKNOWN"
            merged_item["solution_text"] = ""
            merged_item["key_concept"] = ""
            
        merged_data.append(merged_item)
        
    logger.info(f"Merged {len(merged_data)} items.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=4)
        
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    process()
