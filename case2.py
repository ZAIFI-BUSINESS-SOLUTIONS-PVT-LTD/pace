import sys
import os
import json
import logging
import traceback

# Ensure src importable
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.phase2 import packetize_students, llm_runner, build_phase2_csvs
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("Case2Runner")

def verify_file(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Verification Failed: File not found - {path}")
    if os.path.getsize(path) < 10: # Min size check
        raise ValueError(f"Verification Failed: File too small - {path}")
    logger.info(f"Verified exists: {path}")

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
            
            logger.info(f"=== Starting Phase 2 Execution for {current_class} ===")
            
            # 1. Packetization
            logger.info(f"--- Step 1: Packetize Students ({current_class}) ---")
            packets = packetize_students.process()
            if not packets:
                logger.warning(f"No student packets generated for {current_class}. Skipping...")
                continue
            logger.info(f"Generated {len(packets)} packets for {current_class}.")
            
            # 2. LLM Analysis
            logger.info(f"--- Step 2: LLM Analysis ({current_class}) ---")
            llm_results = llm_runner.process(packets)
            if not llm_results:
                logger.warning(f"No LLM results returned for {current_class}!")
                continue
                
            logger.info(f"Received analysis for {len(llm_results)} students for {current_class}.")
            
            # 3. Build CSVs
            logger.info(f"--- Step 3: Generate CSVs ({current_class}) ---")
            build_phase2_csvs.process(llm_results, packets)
            
            # 4. Verification
            logger.info(f"=== Verifying Outputs for {current_class} ===")
            
            q_insights_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase2", "student_question_insights.csv")
            s_summary_path = os.path.join(Config.OUTPUT_DIR, current_class, "phase2", "student_insight_summary.csv")
            
            try:
                verify_file(q_insights_path)
                verify_file(s_summary_path)
                logger.info(f"=== SUCCESS: {current_class} Phase 2 Completed and Verified ===")
            except Exception as e:
                 logger.error(f"Verification Failed for {current_class}: {e}")

    except Exception:
        logger.error("Phase 2 Execution FAILED")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
