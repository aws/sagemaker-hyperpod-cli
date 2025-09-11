"""
Unified parameter parsing module for SageMaker HyperPod CLI.

This module provides consistent parsing for different parameter types across all CLI commands:
- List parameters: JSON format ['item1', 'item2'] or simple format [item1, item2]  
- Dictionary parameters: JSON format {"key": "value"} or simple format {key: value}
- Complex object parameters: JSON format {"key": "value"} or key=value format
"""

import json
import re
import click
from typing import Any, Dict, List, Union


class ParameterParsingError(click.BadParameter):
    """Custom exception for parameter parsing errors with helpful messages."""
    pass


def parse_list_parameter(ctx, param, value: str) -> List[Any]:
    """
    Parse list parameters supporting multiple formats.
    
    Supported formats:
    - JSON: '["item1", "item2", "item3"]'
    - Simple: '[item1, item2, item3]' (with or without spaces)
    
    Args:
        ctx: Click context
        param: Click parameter object
        value: Input string value
        
    Returns:
        List of parsed items
        
    Raises:
        ParameterParsingError: If parsing fails for both JSON and simple formats
    """
    if value is None or value == "":
        return None
    
    param_name = param.name if param else "parameter"
    
    # Try JSON parsing first
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
        else:
            # JSON parsed but not a list - provide specific error
            raise ParameterParsingError(
                f"Expected a list for --{param_name}, got {type(parsed).__name__}"
            )
    except (json.JSONDecodeError, ValueError):
        # JSON parsing failed, continue to simple parsing
        pass
    
    # Try simple list parsing: [item1, item2] or [item1,item2]
    try:
        return _parse_simple_list(value)
    except Exception:
        pass
    
    # Both formats failed - provide helpful error message
    raise ParameterParsingError(
        f"Invalid format for --{param_name}. Supported formats:\n"
        f"  JSON: '[\"item1\", \"item2\", \"item3\"]'\n" 
        f"  Simple: '[item1, item2, item3]'"
    )


def parse_dict_parameter(ctx, param, value: str) -> Dict[str, Any]:
    """
    Parse dictionary parameters supporting multiple formats.
    
    Supported formats:
    - JSON: '{"key": "value", "key2": "value2"}'
    - Simple: '{key: value, key2: "value with spaces"}'
    
    Args:
        ctx: Click context
        param: Click parameter object  
        value: Input string value
        
    Returns:
        Dictionary of parsed key-value pairs
        
    Raises:
        ParameterParsingError: If parsing fails for both JSON and simple formats
    """
    if value is None:
        return None
        
    param_name = param.name if param else "parameter"
    
    # Try JSON parsing first
    try:
        parsed = json.loads(value)
        if isinstance(parsed, dict):
            return parsed
        else:
            # JSON parsed but not a dict - let it fall through to simple parsing
            pass
    except (json.JSONDecodeError, ValueError):
        # JSON parsing failed, continue to simple parsing
        pass
    
    # Try simple dict parsing: {key: value, key2: value2}
    try:
        return _parse_simple_dict(value)
    except Exception:
        pass
    
    # Both formats failed - provide helpful error message
    raise ParameterParsingError(
        f"Invalid format for --{param_name}. Supported formats:\n"
        f"  JSON: '{{\"key\": \"value\", \"key2\": \"value2\"}}'\n"
        f"  Simple: '{{key: value, key2: \"value with spaces\"}}'"
    )


def parse_complex_object_parameter(ctx, param, value: Union[str, List[str]], allow_multiple: bool = True) -> List[Dict[str, Any]]:
    """
    Parse complex object parameters supporting multiple formats and multiple flag usage.
    
    Supported formats:
    - JSON single object: '{"key": "value", "key2": "value2"}'  
    - JSON array (if allow_multiple=True): '[{"key": "value"}, {"key2": "value2"}]'
    - Key-value single: 'key=value,key2=value2'
    - Multiple flags (if allow_multiple=True): --param obj1 --param obj2
    
    Args:
        ctx: Click context
        param: Click parameter object
        value: Input string value or list of string values (for multiple flags)
        allow_multiple: Whether to support multiple objects via multiple flags or JSON arrays
        
    Returns:
        List of dictionaries representing complex objects (single item list if allow_multiple=False)
        
    Raises:
        ParameterParsingError: If parsing fails for both JSON and key-value formats
    """
    if not value:
        return None
        
    param_name = param.name if param else "parameter"
    
    # Handle multiple flag usage: --volume config1 --volume config2
    if not isinstance(value, (list, tuple)):
        value = [value]
    
    # Check allow_multiple constraint
    if not allow_multiple and len(value) > 1:
        raise ParameterParsingError(
            f"--{param_name} does not support multiple values. "
            f"Received {len(value)} values: {value}"
        )
    
    results = []
    for i, item in enumerate(value):
        try:
            # Try JSON parsing first
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    results.append(parsed)
                    continue
                elif isinstance(parsed, list) and allow_multiple:
                    # JSON array format: '[{"key": "value"}, {"key2": "value2"}]'
                    for j, array_item in enumerate(parsed):
                        if not isinstance(array_item, dict):
                            raise ParameterParsingError(
                                f"--{param_name} JSON array item {j+1} must be an object, got {type(array_item).__name__}"
                            )
                        results.append(array_item)
                    continue
                elif isinstance(parsed, list) and not allow_multiple:
                    raise ParameterParsingError(
                        f"--{param_name} does not support JSON arrays. Use single object format."
                    )
            except (json.JSONDecodeError, ValueError):
                pass
            
            # Try key-value parsing: key=value,key2=value2
            parsed_dict = _parse_key_value_pairs(item)
            results.append(parsed_dict)
            
        except Exception as e:
            if isinstance(e, ParameterParsingError):
                raise e
            raise ParameterParsingError(
                f"Invalid format for --{param_name} item {i+1}: '{item}'. Supported formats:\n"
                f"  JSON object: '{{\"key\": \"value\", \"key2\": \"value2\"}}'\n"
                + (f"  JSON array: '[{{\"key\": \"value\"}}, {{\"key2\": \"value2\"}}]'\n" if allow_multiple else "")
                + f"  Key-value: 'key=value,key2=value2'"
            )
    
    # For single-object mode, return single item list or enforce single result
    if not allow_multiple and len(results) > 1:
        raise ParameterParsingError(
            f"--{param_name} produced multiple objects but only single object is allowed"
        )
    
    return results


def _parse_simple_list(value: str) -> List[str]:
    """
    Parse simple list format: [item1, item2] or [item1,item2]
    
    Args:
        value: String in format [item1, item2]
        
    Returns:
        List of string items
        
    Raises:
        ValueError: If format is invalid
    """
    value = value.strip()
    
    if not (value.startswith('[') and value.endswith(']')):
        raise ValueError("List must be enclosed in brackets")
    
    # Remove brackets and get inner content
    inner = value[1:-1].strip()
    
    if not inner:
        return []
    
    # For simple format, check for common malformed JSON patterns
    if inner.endswith(','):  # trailing comma
        raise ValueError("Invalid list format - trailing comma detected")
    
    # Split by comma and clean up items
    items = []
    for item in inner.split(','):
        item = item.strip()
        if not item:  # Empty item (e.g., trailing comma)
            continue
        # Remove surrounding quotes if present
        if ((item.startswith('"') and item.endswith('"')) or 
            (item.startswith("'") and item.endswith("'"))):
            item = item[1:-1]
        items.append(item)
    
    return items


def _parse_simple_dict(value: str) -> Dict[str, str]:
    """
    Parse simple dictionary format: {key: value, key2: "value with spaces"}
    
    Args:
        value: String in format {key: value, key2: value2}
        
    Returns:
        Dictionary of string key-value pairs
        
    Raises:
        ValueError: If format is invalid
    """
    value = value.strip()
    
    if not (value.startswith('{') and value.endswith('}')):
        raise ValueError("Dictionary must be enclosed in braces")
    
    # Remove braces and get inner content
    inner = value[1:-1].strip()
    
    if not inner:
        return {}
    
    # Parse key-value pairs using regex to handle quoted values
    result = {}
    
    # Split by comma, but respect quotes
    pairs = _split_respecting_quotes(inner, ',')
    
    for pair in pairs:
        pair = pair.strip()
        if ':' not in pair:
            raise ValueError(f"Invalid key-value pair: '{pair}'. Expected format: 'key: value'")
        
        key_part, value_part = pair.split(':', 1)
        key = key_part.strip()
        value_str = value_part.strip()
        
        # Remove surrounding quotes from key if present  
        if ((key.startswith('"') and key.endswith('"')) or
            (key.startswith("'") and key.endswith("'"))):
            key = key[1:-1]
        
        # Remove surrounding quotes from value and unescape inner quotes
        if ((value_str.startswith('"') and value_str.endswith('"')) or
            (value_str.startswith("'") and value_str.endswith("'"))):
            quote_char = value_str[0]
            value_str = value_str[1:-1]
            # Unescape inner quotes
            if quote_char == '"':
                value_str = value_str.replace('\\"', '"')
            else:
                value_str = value_str.replace("\\'", "'")
        
        result[key] = value_str
    
    return result


def _parse_key_value_pairs(value: str) -> Dict[str, str]:
    """
    Parse key-value pairs format: key=value,key2=value2
    
    Args:
        value: String in format key=value,key2=value2
        
    Returns:
        Dictionary of string key-value pairs
        
    Raises:
        ValueError: If format is invalid
    """
    result = {}
    
    # Split by comma and parse each key=value pair
    for pair in value.split(','):
        if '=' not in pair:
            raise ValueError(f"Invalid key-value pair: '{pair}'. Expected format: 'key=value'")
        
        key, val = pair.split('=', 1)  # Split only on first '=' to handle values with '='
        key = key.strip()
        val = val.strip()
        
        if not key:
            raise ValueError(f"Empty key in pair: '{pair}'")
        
        result[key] = val
    
    return result


def _split_respecting_quotes(text: str, delimiter: str) -> List[str]:
    """
    Split text by delimiter while respecting quoted sections.
    
    Args:
        text: Text to split
        delimiter: Delimiter to split on
        
    Returns:
        List of split parts
    """
    parts = []
    current = []
    in_quotes = False
    quote_char = None
    
    i = 0
    while i < len(text):
        char = text[i]
        
        if char in ('"', "'") and (i == 0 or text[i-1] != '\\'):
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        
        if char == delimiter and not in_quotes:
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)
        
        i += 1
    
    if current:
        parts.append(''.join(current))
    
    return parts


def parse_comma_separated_list(ctx, param, value: str) -> List[str]:
    """
    Parse comma-separated list format: item1,item2,item3
    
    This is a legacy format parser for backward compatibility.
    Use parse_list_parameter for new implementations.
    
    Args:
        ctx: Click context
        param: Click parameter object
        value: Input string value
        
    Returns:
        List of string items
    """
    if value is None:
        return None
    
    # Split by comma and clean up items
    items = [item.strip() for item in value.split(',') if item.strip()]
    return items
