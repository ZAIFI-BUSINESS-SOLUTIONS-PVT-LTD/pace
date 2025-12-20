import os
import json
import logging
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.pdf_loader import load_pdf_pages
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.prompts import PHASE_1_EXTRACT_QUESTION_PROMPT

logger = setup_logger(__name__)

def process():
    setup_gemini()
    
    input_path = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS, "QuestionPaper.pdf")
    output_dir = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "questionpaper.json")
    
    logger.info(f"Processing Question Paper: {input_path}")
    
    all_questions = []
    
    for page_num, text in load_pdf_pages(input_path):
        logger.info(f"Processing Page {page_num}...")
        try:
            data = call_gemini_json(PHASE_1_EXTRACT_QUESTION_PROMPT, text)
            if isinstance(data, list):
                all_questions.extend(data)
            elif isinstance(data, dict):
                 # Handle case where LLM returns a single object or wrapped dict
                 if "questions" in data:
                     all_questions.extend(data["questions"])
                 else:
                     all_questions.append(data)
        except Exception as e:
            logger.error(f"Failed to extract from page {page_num}: {e}")
            # we continue to next page? User said "Fail loudly if anything breaks". 
            # But maybe strict failure means stop? User said "Stop ... if any step fails".
            # This is a step failure.
            raise

    # Post-process to add question_id
    final_questions = []
    for q in all_questions:
        try:
            q_num = q.get("question_number")
            if q_num:
                q["question_id"] = f"Q{q_num}"
                final_questions.append(q)
            else:
                 logger.warning(f"Skipping question without number: {q}")
        except Exception as e:
            logger.error(f"Error processing question item: {q} - {e}")
            raise

    logger.info(f"Extracted {len(final_questions)} questions.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_questions, f, indent=4)
    
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    process()
