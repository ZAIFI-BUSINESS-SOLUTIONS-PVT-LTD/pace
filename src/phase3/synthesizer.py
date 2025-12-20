import re
from src.utils.llm_helper import call_gemini_text, setup_gemini
from src.utils.logger import setup_logger
from src.prompts import PHASE_3_SYSTEM_INSTRUCTION, PHASE_3_USER_PROMPT_TEMPLATE

logger = setup_logger(__name__)

REQUIRED_KEYS = [
    "focus_zone_1", "focus_zone_2", "focus_zone_3",
    "action_plan_1", "action_plan_2", "action_plan_3"
]

def parse_llm_response(text: str) -> dict:
    """
    Parses the LLM text output into a dictionary.
    """
    data = {}
    
    # Regex patterns
    patterns = {
        "focus_zone_1": r"Focus Zone 1:\s*(.*)",
        "focus_zone_2": r"Focus Zone 2:\s*(.*)",
        "focus_zone_3": r"Focus Zone 3:\s*(.*)",
        "action_plan_1": r"Action Plan 1:\s*(.*)",
        "action_plan_2": r"Action Plan 2:\s*(.*)",
        "action_plan_3": r"Action Plan 3:\s*(.*)",
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()
        else:
            logger.error(f"Failed to extract {key} from response.")
            
    # Check completeness
    if len(data) != 6:
        logger.error(f"Incomplete parsing. Got {len(data)} fields. Response:\n{text}")
        raise ValueError("Gemini output deviates from required format or count.")
        
    return data

def synthesize_class(class_id: str, csv_content: str) -> dict:
    """
    Calls Gemini to synthesize class insights.
    """
    setup_gemini()
    
    full_prompt = f"{PHASE_3_SYSTEM_INSTRUCTION}\n\n{PHASE_3_USER_PROMPT_TEMPLATE}"
    
    logger.info(f"Calling Gemini for Class {class_id}...")
    response_text = call_gemini_text(full_prompt, csv_content)
    
    logger.info(f"Received response for {class_id}. Parsing...")
    parsed_data = parse_llm_response(response_text)
    
    parsed_data["class_id"] = class_id
    return parsed_data
