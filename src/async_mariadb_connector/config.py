# Config + environment management
import os
from dotenv import load_dotenv
from typing import Dict, Any

def load_config(**kwargs) -> Dict[str, Any]:
    """
    Loads configuration from .env file and merges it with provided kwargs.
    Kwargs take precedence over environment variables.
    """
    load_dotenv()
    env_config = os.environ

    # Start with defaults and environment variables
    config = {
        'host': env_config.get('DB_HOST', 'localhost'),
        'port': int(env_config.get('DB_PORT', 3306)),
        'user': env_config.get('DB_USER'),
        'password': env_config.get('DB_PASSWORD'),
        'db': env_config.get('DB_NAME'),
        'minsize': int(env_config.get('DB_POOL_MIN_SIZE', 1)),
        'maxsize': int(env_config.get('DB_POOL_MAX_SIZE', 10)),
        'autocommit': env_config.get('AUTOCOMMIT', 'true').lower() in ('true', '1', 't'),
        'connect_timeout': int(env_config.get('DB_CONNECT_TIMEOUT', 10))
    }

    # Remap and apply kwargs, giving them precedence
    if 'pool_min_size' in kwargs:
        kwargs['minsize'] = kwargs.pop('pool_min_size')
    if 'pool_max_size' in kwargs:
        kwargs['maxsize'] = kwargs.pop('pool_max_size')

    config.update(kwargs)

    # Filter out None values for optional parameters
    return {k: v for k, v in config.items() if v is not None}
