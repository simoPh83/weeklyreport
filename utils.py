"""
Utility functions for Property Management System
"""
from datetime import datetime
from typing import Any, Optional


def format_currency(amount: Optional[float]) -> str:
    """
    Format a number as currency
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    if amount is None:
        return ""
    return f"${amount:,.2f}"


def format_date(date_str: Optional[str], format_in: str = "%Y-%m-%d", 
                format_out: str = "%m/%d/%Y") -> str:
    """
    Format a date string
    
    Args:
        date_str: Date string to format
        format_in: Input date format
        format_out: Output date format
        
    Returns:
        Formatted date string
    """
    if not date_str:
        return ""
    
    try:
        date_obj = datetime.strptime(date_str, format_in)
        return date_obj.strftime(format_out)
    except:
        return date_str


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """
    Format a timestamp for display
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp_str:
        return ""
    
    try:
        # SQLite returns timestamps as strings
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str


def validate_required_fields(data: dict, required_fields: list) -> tuple[bool, str]:
    """
    Validate that required fields are present and not empty
    
    Args:
        data: Dictionary of field values
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    for field in required_fields:
        value = data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, f"Field '{field}' is required"
    
    return True, ""


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Integer value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
