import os
import sys
from src.config import Config
from src.utils.logger import setup_logger
from src.phase3 import aggregator, synthesizer, writer

logger = setup_logger(__name__)

def get_classes_to_process():
    """
    Determines which classes to process based on TARGET_CLASS env var
    and availability of Phase 2 outputs.
    """
    target_class = os.getenv("TARGET_CLASS")
    
    available_classes = []
    
    # scan text output dir for classes
    if os.path.exists(Config.OUTPUT_DIR):
        for d in os.listdir(Config.OUTPUT_DIR):
            path = os.path.join(Config.OUTPUT_DIR, d)
            if os.path.isdir(path):
                # Check for Phase 2 output
                p2_file = os.path.join(path, "phase2", "student_insight_summary.csv")
                if os.path.exists(p2_file):
                    available_classes.append(d)
    
    if target_class and target_class.lower() != "none":
        if target_class in available_classes:
            return [target_class]
        else:
            logger.warning(f"Target class {target_class} not found or missing Phase 2 output.")
            return []
            
    return available_classes

def run():
    logger.info("=== Starting Phase 3: Class-Level Insight Synthesis ===")
    
    classes = get_classes_to_process()
    
    if not classes:
        logger.error("No classes found ready for Phase 3 (missing Phase 2 outputs?).")
        sys.exit(1)
        
    logger.info(f"Classes to process: {classes}")
    
    results = []
    
    for class_id in classes:
        logger.info(f"--- Processing Class: {class_id} ---")
        try:
            # 1. Read Data
            csv_content = aggregator.load_class_data(class_id)
            
            # 2. Synthesize
            insights = synthesizer.synthesize_class(class_id, csv_content)
            
            # Validate results (implicit in synthesizer parsing, but double check)
            if insights:
                results.append(insights)
                logger.info(f"Successfully synthesized insights for {class_id}")
            
        except Exception as e:
            logger.error(f"Failed to process {class_id}: {e}")
            # strict mode: failure in one class might not stop others, but USER said "Deviation is considered failure".
            # "Fail Phase 3 if ... student_insight_summary.csv is missing" -> aggregator handles this.
            # "Fail Phase 3 if ... Gemini output deviates" -> synthesizer handles this.
            # We should probably continue to other classes but mark this run as partial? 
            # Or stop? The prompt says "Fail Phase 3 if ...". Strict execution.
            # I will stop execution to be strict.
            sys.exit(1)
            
    if results:
        # 3. Write Output
        writer.save_manifest(results)
        logger.info(f"Phase 3 Complete. Output written for {len(results)} classes.")
    else:
        logger.warning("No results generated.")

if __name__ == "__main__":
    run()
