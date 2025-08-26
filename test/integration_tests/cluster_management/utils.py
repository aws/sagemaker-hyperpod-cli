"""
Utility functions for integration tests.
"""
import yaml
from pathlib import Path


def assert_command_succeeded(result):
    """Assert that a CLI command succeeded."""
    assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}. Output: {result.output}"


def assert_command_failed_with_helpful_error(result, expected_keywords):
    """Assert that a command failed and contains helpful error messages."""
    assert result.exit_code != 0, f"Command should have failed but succeeded. Output: {result.output}"
    for keyword in expected_keywords:
        assert keyword.lower() in result.output.lower(), f"Expected keyword '{keyword}' not found in output: {result.output}"


def assert_config_values(directory, expected_values):
    """Assert that config.yaml contains expected values."""
    config_path = Path(directory) / "config.yaml"
    assert config_path.exists(), f"config.yaml should exist in {directory}"
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    for key, expected_value in expected_values.items():
        actual_value = config.get(key)
        assert actual_value == expected_value, f"Expected {key}={expected_value}, got {actual_value}"


def assert_warning_displayed(result, expected_keywords):
    """Assert that warning messages are displayed in command output."""
    for keyword in expected_keywords:
        assert keyword.lower() in result.output.lower(), f"Expected warning keyword '{keyword}' not found in output: {result.output}"


def assert_yes_no_prompt_displayed(result):
    """Assert that a yes/no prompt was displayed."""
    prompt_indicators = ["(y/n)", "(Y/n)", "[y/N]", "?"]
    found_prompt = any(indicator in result.output for indicator in prompt_indicators)
    assert found_prompt, f"Expected yes/no prompt not found in output: {result.output}"


def assert_success_message_displayed(result, expected_keywords):
    """Assert that success messages are displayed in command output."""
    for keyword in expected_keywords:
        assert keyword.lower() in result.output.lower(), f"Expected success keyword '{keyword}' not found in output: {result.output}"