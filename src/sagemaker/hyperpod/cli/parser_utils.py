"""
Shared parser utilities for complex CLI parameters
Provides universal parsing for lists, dicts, and other Python literals
"""

import ast
import click


def parse_complex_parameter(ctx, param, value, expected_type=None, allow_multiple=False):
    """
    Universal parser for complex CLI parameters
    
    Handles parsing of Python literal expressions including:
    - Lists: '["item1", "item2"]'
    - Dictionaries: '{"key": "value"}'
    - Strings, numbers, booleans
    - Multiple values for repeated flags
    
    Args:
        ctx: Click context object
        param: Click parameter object
        value: Input value(s) to parse - can be string or list of strings
        expected_type: Expected Python type (dict, list, str, etc.) for validation
        allow_multiple: Whether to handle multiple values (for repeated flags)
    
    Returns:
        Parsed Python object(s) - single object or list depending on allow_multiple
        
    Raises:
        click.BadParameter: If parsing fails or type validation fails
    """
    if value is None:
        return None
    
    # Handle multiple values (like --volume used multiple times)
    if allow_multiple:
        if not isinstance(value, (list, tuple)):
            value = [value]
        
        results = []
        for i, v in enumerate(value):
            try:
                parsed = ast.literal_eval(v)
                
                # Type validation for individual items
                if expected_type and not isinstance(parsed, expected_type):
                    raise click.BadParameter(
                        f"{param.name} item {i+1} must be {expected_type.__name__}, "
                        f"got {type(parsed).__name__}: {v}"
                    )
                
                results.append(parsed)
            except (ValueError, SyntaxError) as e:
                raise click.BadParameter(
                    f"Invalid format for {param.name} item {i+1}: {v}. "
                    f"Expected Python literal (dict, list, string, etc.). Error: {e}"
                )
        
        return results
    
    # Handle single value
    try:
        parsed = ast.literal_eval(value)
        
        # Type validation
        if expected_type and not isinstance(parsed, expected_type):
            raise click.BadParameter(
                f"{param.name} must be {expected_type.__name__}, "
                f"got {type(parsed).__name__}: {value}"
            )
        
        return parsed
    except (ValueError, SyntaxError) as e:
        raise click.BadParameter(
            f"Invalid format for {param.name}: {value}. "
            f"Expected Python literal (dict, list, string, etc.). Error: {e}"
        )
