# Async batch insert/update logic
import pandas as pd
import logging
from .core import AsyncMariaDB
from .exceptions import BulkOperationError

logger = logging.getLogger(__name__)

async def bulk_insert(db: 'AsyncMariaDB', table_name: str, dataframe: pd.DataFrame):
    """
    Perform high-speed async inserts for a DataFrame.
    """
    if dataframe.empty:
        logger.warning("Input DataFrame is empty. No bulk insert operation will be performed.")
        return

    columns = ', '.join(f"`{col}`" for col in dataframe.columns)
    placeholders = ', '.join(['%s'] * len(dataframe.columns))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    # Convert DataFrame rows to tuples, explicitly converting pandas NA types to None
    data = [
        tuple(None if pd.isna(x) else x for x in row)
        for row in dataframe.itertuples(index=False, name=None)
    ]
    
    try:
        logger.info(f"Starting bulk insert of {len(data)} rows into table '{table_name}'.")
        pool = await db._get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.executemany(query, data)
                if not db.db_config['autocommit']:
                    await conn.commit()
        logger.info("Bulk insert operation completed successfully.")
    except Exception as e:
        logger.error(f"Bulk insert failed for table '{table_name}': {e}")
        raise BulkOperationError(f"Failed to bulk insert data into {table_name}.") from e
