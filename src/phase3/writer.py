import os
import pandas as pd
from src.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OUTPUT_FILE = "class_level_focus_and_action.csv"
COLUMNS = [
    "class_id",
    "focus_zone_1", "focus_zone_2", "focus_zone_3",
    "action_plan_1", "action_plan_2", "action_plan_3"
]

def save_manifest(results: list[dict]):
    """
    Saves the list of class insights to a CSV file.
    """
    output_dir = Config.OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, OUTPUT_FILE)
    
    df = pd.DataFrame(results, columns=COLUMNS)
    
    try:
        df.to_csv(file_path, index=False)
        logger.info(f"Successfully wrote Phase 3 manifest to {file_path}")
    except Exception as e:
        logger.error(f"Failed to write output CSV: {e}")
        raise
