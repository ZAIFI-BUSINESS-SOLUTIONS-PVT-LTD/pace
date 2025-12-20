import google.generativeai as genai
import os
import json
import logging
import re
from src.config import Config

logger = logging.getLogger(__name__)

def setup_gemini():
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=Config.GEMINI_API_KEY)


def call_gemini_json(prompt: str, content: str) -> dict | list:
    """
    Calls Gemini with a prompt and content, expecting a JSON response.
    """
    model = genai.GenerativeModel(Config.MODEL_NAME)
    
    full_prompt = f"{prompt}\n\nCONTENT:\n{content}"
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # Clean up markdown code blocks
        text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Error calling Gemini or parsing JSON: {e}")
        logger.error(f"Raw response: {text if 'text' in locals() else 'No response'}")
        raise

def call_gemini_text(prompt: str, content: str) -> str:
    """
    Calls Gemini with a prompt and content, returning raw text response.
    """
    model = genai.GenerativeModel(Config.MODEL_NAME)
    
    full_prompt = f"{prompt}\n\nCONTENT:\n{content}"
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error calling Gemini (Text Mode): {e}")
        raise


