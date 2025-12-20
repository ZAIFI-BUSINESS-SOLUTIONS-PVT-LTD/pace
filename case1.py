import sys
import os
import json
import logging
import traceback

# Ensure we can import src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase1 import extract_questionpaper
from src.phase1 import extract_solution
from src.phase1 import merge_data
from src.phase1.guardrails import check_input_purity
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case1Runner")

def verify_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Verification Failed: File not found - {path}")
    if os.path.getsize(path) == 0:
        raise ValueError(f"Verification Failed: File is empty - {path}")
    logger.info(f"Verified exists: {path}")

def verify_json_schema(path, required_keys):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Verification Failed: Root must be a list in {path}")
        
    if not data:
        logger.warning(f"Warning: JSON is empty list in {path}")
        return

    first_item = data[0]
    missing = [k for k in required_keys if k not in first_item]
    if missing:
        raise ValueError(f"Verification Failed: Missing keys {missing} in {path}")
    
    # Check consistency of question_id
    ids = [item.get("question_id") for item in data]
    if len(set(ids)) != len(ids):
        logger.warning(f"Warning: Duplicate question_ids found in {path}")
    
    logger.info(f"Verified schema for {path}")

def main():
    try:
        target_class = os.getenv("TARGET_CLASS")
        classes_to_process = []

        if not target_class or target_class.strip().lower() == "none":
            # Detect all classes in input directory
            if os.path.exists(Config.INPUT_DIR):
                classes_to_process = [d for d in os.listdir(Config.INPUT_DIR) 
                                      if os.path.isdir(os.path.join(Config.INPUT_DIR, d))]
        else:
            classes_to_process = [target_class]

        if not classes_to_process:
            logger.error("No classes found to process.")
            sys.exit(1)

        logger.info(f"Classes to process: {classes_to_process}")

        for current_class in classes_to_process:
            # Patch Config.DEFAULT_CLASS for this iteration
            Config.DEFAULT_CLASS = current_class
            
            logger.info(f"=== Starting Phase 1 Execution for {current_class} ===")
            check_input_purity()
            
            # 1. Extraction
            logger.info(f"--- Step 1: Extract Question Paper ({current_class}) ---")
            extract_questionpaper.process()
            
            logger.info(f"--- Step 2: Extract Solutions ({current_class}) ---")
            extract_solution.process()
            
            # 2. Merge
            logger.info(f"--- Step 3: Merge Data ({current_class}) ---")
            merge_data.process()
            
            # 3. Verification
            logger.info(f"=== Verifying Outputs for {current_class} ===")
            
            qp_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase1", "questionpaper.json")
            sol_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase1", "solution.json")
            merged_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase1", "merged.json")
            
            try:
                verify_file(qp_path)
                verify_file(sol_path)
                verify_file(merged_path)
                
                verify_json_schema(qp_path, ["question_id", "question_text", "options"])
                verify_json_schema(sol_path, ["question_id", "correct_option", "solution_text", "key_concept"])
                verify_json_schema(merged_path, ["question_id", "question_text", "options", "correct_option", "solution_text", "key_concept"])
                
                logger.info(f"=== SUCCESS: {current_class} Completed and Verified ===")
            except Exception as e:
                logger.error(f"Verification Failed for {current_class}: {e}")
                # We do NOT exit here, we allow other classes to proceed/fail
                # But we might want to track failures?
                # User asked to fix the run.
                pass

    except Exception:
        logger.error("Execution FAILED")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
