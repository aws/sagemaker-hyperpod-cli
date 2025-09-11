"""Type handler for CLI parameter generation"""

import json
import click
from typing import get_origin
import ast


# Utility functions
def convert_cli_value(value, field_type):
    """Convert CLI string value to proper Python type"""
    if not isinstance(value, str) or field_type == str:
        return value

    # Handle complex types (already parsed by callbacks, but just in case)
    if is_complex_type(field_type):
        try:
            parsed = json.loads(value)
            return parsed
        except json.JSONDecodeError as e:
            return value

    # Handle simple types
    if field_type == bool:
        return value.lower() in ('true', '1', 'yes', 'on')
    elif field_type == int:
        try:
            return int(value)
        except ValueError:
            return value
    elif field_type == float:
        try:
            return float(value)
        except ValueError:
            return value
    return value


def to_click_type(field_type):
    """Convert Python type to Click type"""
    if is_complex_type(field_type):
        return str  # JSON string input for complex types
    elif field_type is bool:
        return bool
    elif field_type is int:
        return int
    elif field_type is float:
        return float
    else:
        return str


def is_complex_type(field_type):
    """Check if field type needs JSON parsing"""
    origin = get_origin(field_type)
    return (
        origin is list or field_type is list or
        origin is dict or field_type is dict or
        origin is tuple or field_type is tuple
    )


def parse_strings(ctx_or_value, param=None, value=None):
    """
    Parse string input with JSON fallback and flexible list handling.
    
    This function serves dual purposes:
    1. As a Click callback for CLI parameter validation
    2. As a direct utility function for string parsing
    
    Args:
        ctx_or_value: When used as Click callback, this is the Click context.
                     When used directly, this is the value to parse.
        param: Click parameter object (only present when used as Click callback)
        value: The actual value to parse (only present when used as Click callback)
    
    Returns:
        - None if input is None
        - Original value if not a string
        - Parsed JSON object/array if valid JSON
        - Parsed list if input matches pattern [item1, item2, ...]
        - Original string if no parsing succeeds
    
    Parsing Logic:
        1. First attempts standard JSON parsing
        2. If JSON fails and input looks like a list [item1, item2], 
           attempts to parse as unquoted list items
        3. Strips quotes and whitespace from list items
        4. Falls back to returning original string
    
    Raises:
        click.BadParameter: When used as Click callback and parsing fails
    
    Examples:
        parse_strings('{"key": "value"}')  # Returns dict
        parse_strings('[item1, item2]')    # Returns ['item1', 'item2']  
        parse_strings('["a", "b"]')        # Returns ['a', 'b']
        parse_strings('plain text')        # Returns 'plain text'
    """
    # Handle dual usage pattern (inlined)
    if param is not None and value is not None:
        actual_value, is_click_callback = value, True
    else:
        actual_value, is_click_callback = ctx_or_value, False

    if actual_value is None:
        return None

    if not isinstance(actual_value, str):
        return actual_value

    try:
        return json.loads(actual_value)
    except json.JSONDecodeError:
        # Try ast.literal_eval for Python-style strings with single quotes
        try:
            return ast.literal_eval(actual_value)
        except (ValueError, SyntaxError):
            # Try to fix unquoted list items: [python, train.py] -> ["python", "train.py"]
            if actual_value.strip().startswith('[') and actual_value.strip().endswith(']'):
                try:
                    # Remove brackets and split by comma
                    inner = actual_value.strip()[1:-1]
                    items = [item.strip().strip('"').strip("'") for item in inner.split(',')]
                    return items
                except:
                    pass

            if is_click_callback:
                raise click.BadParameter(f"{param.name!r} must be valid JSON or a list like [item1, item2]")
            return actual_value


def write_to_yaml(key, value, file_handle):
    """Write value to YAML format."""
    if isinstance(value, list):
        if value:
            file_handle.write(f"{key}:\n")
            for item in value:
                file_handle.write(f"  - {item}\n")
            file_handle.write("\n")
        else:
            file_handle.write(f"{key}: []\n\n")
    else:
        value = "" if value is None else value
        file_handle.write(f"{key}: {value}\n\n")


def from_dicts(dicts):
    """Convert dicts to objects. Base implementation returns as-is."""
    return dicts


def to_dicts(objects):
    """Convert objects to dicts. Base implementation handles both cases."""
    if not objects:
        return []
    return [obj.to_dict() if hasattr(obj, 'to_dict') else obj for obj in objects]


def merge_dicts(existing, new):
    """Merge configurations. Base implementation handles single values and lists."""
    return new if new is not None else existing


# Default type handler dictionary for backward compatibility
DEFAULT_TYPE_HANDLER = {
    'parse_strings': parse_strings,
    'write_to_yaml': write_to_yaml,
    'from_dicts': from_dicts,
    'to_dicts': to_dicts,
    'merge_dicts': merge_dicts,
    'needs_multiple_option': False
}
