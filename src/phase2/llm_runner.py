import logging
import json
import time
from src.utils.llm_helper import setup_gemini, call_gemini_json
from src.utils.logger import setup_logger
from src.prompts import PHASE_2_ANALYSIS_PROMPT

logger = setup_logger(__name__)

def process(packets):
    setup_gemini()
    
    results = []
    
    total = len(packets)
    logger.info(f"Starting LLM Analysis for {total} students...")
    
    skipped_count = 0
    flagged_count = 0
    processed_count = 0
    
    for i, packet in enumerate(packets):
        s_id = packet.get("student_id", "Unknown")
        
        # --- Step 2: Enforce Packet Integrity ---
        # Validate that the student packet contains all required fields
        valid_packet = True
        questions_map = {} # For Step 3 overwriting
        
        required_fields = ["question_id", "correct_option", "student_selected_option", 
                           "is_correct", "key_concept", "difficulty_tag"]
        
        if not packet.get("questions"):
             logger.warning(f"Skipping student {s_id}: No questions in packet.")
             skipped_count += 1
             continue
             
        for q in packet["questions"]:
            missing = [k for k in required_fields if k not in q or q[k] is None]
            if missing:
                logger.warning(f"Skipping student {s_id}: Missing fields {missing} in question {q.get('question_id')}")
                valid_packet = False
                break
            # Build map for overwrite later
            questions_map[q["question_id"]] = q
            
        if not valid_packet:
            skipped_count += 1
            continue
            
        logger.info(f"[{i+1}/{total}] Analyzing Student {s_id}...")
        
        # Prepare content
        content = json.dumps(packet, indent=2)
        
        try:
            # Add student_id to context so LLM knows it
            prompt_with_id = f"{PHASE_2_ANALYSIS_PROMPT}\n\nStudent ID: {s_id}"
            
            response = call_gemini_json(prompt_with_id, content)
            
            # Validation / patching if needed
            if "student_id" not in response:
                response["student_id"] = s_id
            
            is_flagged = False
            
            # --- Step 3: Protect Truth after LLM Response ---
            response_questions = []
            if isinstance(response, dict) and "questions" in response:
                response_questions = response["questions"]
            elif isinstance(response, list): # Root list
                response_questions = response
            
            if response_questions:
                for rq in response_questions:
                    qid = rq.get("question_id")
                    
                    # --- Step 1: Validate LLM output schema ---
                    # Validate: mistake_type
                    valid_mistakes = ["Conceptual", "Calculation", "Guess", "Careless"]
                    m_type = rq.get("mistake_type")
                    if m_type not in valid_mistakes:
                        logger.warning(f"Student {s_id}: Invalid mistake_type '{m_type}' for {qid}. Defaulting to 'Conceptual'.")
                        rq["mistake_type"] = "Conceptual"
                        is_flagged = True
                        
                    # Validate: confidence_signal
                    valid_signals = ["Low", "Medium", "High"]
                    c_sig = rq.get("confidence_signal")
                    if c_sig not in valid_signals:
                        logger.warning(f"Student {s_id}: Invalid confidence_signal '{c_sig}' for {qid}. Defaulting to 'Low'.")
                        rq["confidence_signal"] = "Low"
                        is_flagged = True
                        
                    # Validate: correctness_reason
                    reason = rq.get("correctness_reason")
                    if not reason or not isinstance(reason, str) or not reason.strip():
                        logger.warning(f"Student {s_id}: Empty or invalid correctness_reason for {qid}. setting placeholder.")
                        rq["correctness_reason"] = "No explanation provided."
                        is_flagged = True

                    if qid and qid in questions_map:
                        truth = questions_map[qid]
                        # Overwrite Truths (Step 3 from previous prompt)
                        rq["correct_option"] = truth["correct_option"]
                        rq["student_selected_option"] = truth["student_selected_option"] 
                        rq["difficulty_tag"] = truth["difficulty_tag"]
                        rq["key_concept"] = truth["key_concept"]
                        if "is_correct" in rq:
                             rq["is_correct"] = truth["is_correct"]
                        
            # Update response with protected questions
            if isinstance(response, dict) and "questions" in response:
                 response["questions"] = response_questions
            elif isinstance(response, list):
                 response = response_questions
            
            if is_flagged:
                flagged_count += 1
                
            results.append(response)
            processed_count += 1
            
            # Rate limit guard
            time.sleep(1) 
            
        except Exception as e:
            logger.error(f"Failed to analyze student {s_id}: {e}")
            skipped_count += 1
            # Do NOT stop pipeline, just skip student
            continue

    logger.info(f"Phase 2 Execution Report: Total Processed={processed_count}, Flagged (Schema Issues)={flagged_count}, Skipped (Packet/Err)={skipped_count}")
    return results
