# DataFrame conversion helpers
import pandas as pd
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Convert a list of dictionaries to a Pandas DataFrame.
    Handles empty data gracefully.
    """
    if not data:
        logger.info("Input data is empty, returning an empty DataFrame.")
        return pd.DataFrame()
    
    try:
        df = pd.DataFrame(data)
        logger.info(f"Successfully converted data to DataFrame with shape {df.shape}.")
        return df
    except Exception as e:
        logger.error(f"Failed to convert data to DataFrame: {e}")
        raise
