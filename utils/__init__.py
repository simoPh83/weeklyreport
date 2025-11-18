"""Utils package initialization"""
from .db_path_manager import (
    get_app_data_dir,
    save_database_path,
    load_database_path,
    clear_database_path
)

from .helpers import (
    format_currency,
    format_date,
    format_timestamp,
    validate_required_fields,
    safe_int,
    safe_float,
    truncate_string
)

__all__ = [
    # Database path management
    'get_app_data_dir',
    'save_database_path',
    'load_database_path',
    'clear_database_path',
    # Helper functions
    'format_currency',
    'format_date',
    'format_timestamp',
    'validate_required_fields',
    'safe_int',
    'safe_float',
    'truncate_string'
]
