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
    
    for i, packet in enumerate(packets):
        s_id = packet["student_id"]
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
                
            results.append(response)
            
            # Rate limit guard
            time.sleep(1) 
            
        except Exception as e:
            logger.error(f"Failed to analyze student {s_id}: {e}")
            # Do NOT stop pipeline, just skip student
            continue
            
    return results
