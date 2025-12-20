import os
import json
import logging
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger
from src.utils.pdf_loader import load_pdf_pages
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.prompts import PHASE_1_EXTRACT_SOLUTION_PROMPT

logger = setup_logger(__name__)

def load_answer_key_csv(csv_path):
    logger.info(f"Loading Answer Key from CSV: {csv_path}")
    try:
        # Rules: Ignore Row 1 (header). Col A=QNum, Col B=Option.
        # header=0 means first row is header. We can skip it or just read it.
        # "Ignore the first row completely" -> skip_match logic? 
        # Usually pd.read_csv(header=0) treats row 1 as header. 
        # If user says ignor row 1, maybe they mean it has junk?
        # "Row 1 is a header row ... Ignore the first row completely"
        # Means Row 2 is data.
        
        df = pd.read_csv(csv_path) 
        # Pandas reads header by default. So checking columns might be safer.
        # But instructions say "Map Column A... Column B".
        # We'll use iloc.
        
        solutions = []
        for index, row in df.iterrows():
            try:
                # Column A is index 0, Column B is index 1
                q_num_raw = row.iloc[0]
                opt_raw = row.iloc[1]
                
                # Check for nan
                if pd.isna(q_num_raw) or pd.isna(opt_raw):
                    continue
                    
                # Clean
                q_num = int(q_num_raw)
                correct_opt = str(opt_raw).strip().upper()
                
                item = {
                    "question_number": q_num,
                    "correct_option": correct_opt,
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                }
                solutions.append(item)
            except Exception as e:
                logger.warning(f"Skipping CSV row {index}: {e}")
                
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key CSV: {e}")
        raise

def load_answer_key_excel(file_path):
    logger.info(f"Loading Answer Key from Excel: {file_path}")
    try:
        df = pd.read_excel(file_path)
        solutions = []
        # We assume Col 0 = Q Num, Col 1 = Answer, similar to CSV rule
        # Or look for specific headers if possible. Inspection showed QuestionID, CorrectAnswer.
        # Let's try to detect columns or fall back to iloc.
        
        q_col = df.columns[0]
        a_col = df.columns[1]
        
        for index, row in df.iterrows():
            try:
                q_num_raw = row.iloc[0]
                opt_raw = row.iloc[1]
                
                if pd.isna(q_num_raw) or pd.isna(opt_raw):
                    continue
                    
                q_num = int(q_num_raw)
                correct_opt = str(opt_raw).strip().upper()
                
                item = {
                    "question_number": q_num,
                    "correct_option": correct_opt,
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                }
                solutions.append(item)
            except Exception as e:
                logger.warning(f"Skipping Excel row {index}: {e}")
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key Excel: {e}")
        raise

def load_answer_key_json(json_path):
    logger.info(f"Loading Answer Key from JSON: {json_path}")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        solutions = []
        for item in data:
            # Phase 0 JSON: {"question_id": "Q1", "correct_option": "A"} or {"question_id": 1 ...}
            # We need question_number as int
            q_id = item.get("question_id")
            opt = item.get("correct_option")
            
            if q_id is None or opt is None:
                continue
                
            # Parse number from "Q1" or 1
            q_num = None
            if isinstance(q_id, int):
                q_num = q_id
            else:
                q_id_str = str(q_id).upper()
                if q_id_str.startswith("Q"):
                    try:
                        q_num = int(q_id_str[1:])
                    except:
                        pass
                else:
                    try:
                        q_num = int(q_id_str)
                    except:
                        pass
            
            if q_num is not None:
                solutions.append({
                    "question_number": q_num,
                    "correct_option": str(opt).strip().upper(),
                    "solution_text": "Answer key provided. No explanation available.",
                    "key_concept": "UNKNOWN"
                })
        
        return solutions
    except Exception as e:
        logger.error(f"Error reading Answer Key JSON: {e}")
        raise

def process():
    setup_gemini()
    
    class_dir = os.path.join(Config.INPUT_DIR, Config.DEFAULT_CLASS)
    output_dir = os.path.join(Config.OUTPUT_DIR, Config.DEFAULT_CLASS, "phase1")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "solution.json")
    
    # Check for Answer Key (CSV or XLSX or JSON) or Solutions (CSV or PDF)
    candidates = ["AnswerKey.csv", "Solutions.csv", "AnswerKey.xlsx", "Solutions.xlsx", "answer_key.json"]
    answer_key_path = None
    for c in candidates:
        p = os.path.join(class_dir, c)
        if os.path.exists(p):
            answer_key_path = p
            break
            
    final_solutions = []
    
    if answer_key_path:
        logger.info(f"INFO: Solution detected as ANSWER_KEY_ONLY ({os.path.basename(answer_key_path)})")
        if answer_key_path.endswith('.csv'):
            final_solutions = load_answer_key_csv(answer_key_path)
        elif answer_key_path.endswith('.json'):
            final_solutions = load_answer_key_json(answer_key_path)
        else:
            final_solutions = load_answer_key_excel(answer_key_path)
    else:
        # Fallback to PDF
        pdf_path = os.path.join(class_dir, "Solutions.pdf")
        if not os.path.exists(pdf_path):
             logger.warning(f"No Solutions.pdf or AnswerKey.csv found in {class_dir}")
             return

        logger.info(f"Processing Solutions PDF: {pdf_path}")
        all_solutions = []
        
        # Detection flag logic
        is_answer_key_only_run = False
        
        for page_num, text in load_pdf_pages(pdf_path):
            logger.info(f"Processing Page {page_num}...")
            try:
                data = call_gemini_json(PHASE_1_EXTRACT_SOLUTION_PROMPT, text)
                
                batch = []
                if isinstance(data, list):
                    batch = data
                elif isinstance(data, dict):
                     batch = data.get("solutions", [data]) if "solutions" in data else [data]
                
                # Check detection rule per batch/page
                # "If Gemini output contains Only question_number ... Classify as ANSWER_KEY_ONLY"
                # We check content of 'solution_text'.
                # The updated prompt asks Gemini to set the placeholder string if no explanation.
                # We can also enforce it.
                
                for s in batch:
                    sol_text = s.get("solution_text", "")
                    if not sol_text or sol_text.strip() == "" or "Answer key provided" in sol_text:
                        s["solution_text"] = "Answer key provided. No explanation available."
                        s["key_concept"] = "UNKNOWN"
                        is_answer_key_only_run = True # Flagged
                    
                    all_solutions.append(s)
                    
            except Exception as e:
                logger.error(f"Failed to extract from page {page_num}: {e}")
                # Don't stop, continue to next page
                continue

        if is_answer_key_only_run:
            logger.info("INFO: Solution detected as ANSWER_KEY_ONLY (PDF)")
        else:
            logger.info("INFO: Solution detected as DETAILED_SOLUTION")
            
        final_solutions = all_solutions

    # Post-process to add question_id (Common for both paths)
    processed_final = []
    for s in final_solutions:
        try:
            q_num = s.get("question_number")
            if q_num:
                s["question_id"] = f"Q{q_num}"
                processed_final.append(s)
            else:
                 # Try to parse if strictly 'question_id' key exists? 
                 # CSV loader output uses 'question_number'.
                 logger.warning(f"Skipping solution without number: {s}")
        except Exception as e:
            logger.error(f"Error processing item: {s} - {e}")
            raise

    logger.info(f"Extracted {len(processed_final)} solutions.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_final, f, indent=4)
    
    logger.info(f"Saved to {output_path}")

if __name__ == "__main__":
    process()
