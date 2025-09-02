#!/usr/bin/env python3
"""
Comprehensive test suite for unified parameter parsers.

Tests all parameter types, supported formats, edge cases, and error handling
to ensure the unified parsing system works correctly across all scenarios.
"""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../src'))

from sagemaker.hyperpod.cli.parsers import (
    parse_list_parameter,
    parse_dict_parameter,
    parse_complex_object_parameter,
    parse_comma_separated_list,
    ParameterParsingError
)


class MockParam:
    """Mock click parameter for testing."""
    def __init__(self, name):
        self.name = name


class TestListParameters:
    """Test suite for list parameter parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.param = MockParam("command")
        self.ctx = None

    def test_json_format_basic(self):
        """Test basic JSON list format."""
        result = parse_list_parameter(self.ctx, self.param, '["python", "train.py"]')
        assert result == ["python", "train.py"]

    def test_json_format_with_spaces(self):
        """Test JSON format with spaces in values."""
        result = parse_list_parameter(self.ctx, self.param, '["python", "my script.py", "--arg", "value with spaces"]')
        assert result == ["python", "my script.py", "--arg", "value with spaces"]

    def test_json_format_empty_list(self):
        """Test empty JSON list."""
        result = parse_list_parameter(self.ctx, self.param, '[]')
        assert result == []

    def test_json_format_single_item(self):
        """Test JSON list with single item."""
        result = parse_list_parameter(self.ctx, self.param, '["single"]')
        assert result == ["single"]

    def test_simple_format_basic(self):
        """Test basic simple list format."""
        result = parse_list_parameter(self.ctx, self.param, '[python, train.py]')
        assert result == ["python", "train.py"]

    def test_simple_format_no_spaces(self):
        """Test simple format without spaces."""
        result = parse_list_parameter(self.ctx, self.param, '[python,train.py,--epochs,10]')
        assert result == ["python", "train.py", "--epochs", "10"]

    def test_simple_format_with_quotes(self):
        """Test simple format with quoted values for spaces."""
        result = parse_list_parameter(self.ctx, self.param, '[python, "my script.py", --arg, "value with spaces"]')
        assert result == ["python", "my script.py", "--arg", "value with spaces"]

    def test_simple_format_empty_list(self):
        """Test empty simple list."""
        result = parse_list_parameter(self.ctx, self.param, '[]')
        assert result == []

    def test_simple_format_mixed_quotes(self):
        """Test simple format with mixed quote types."""
        result = parse_list_parameter(self.ctx, self.param, "[python, 'single quote', \"double quote\"]")
        assert result == ["python", "single quote", "double quote"]

    def test_none_input(self):
        """Test None input returns None."""
        result = parse_list_parameter(self.ctx, self.param, None)
        assert result is None

    def test_invalid_format_no_brackets(self):
        """Test error for invalid format without brackets."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_list_parameter(self.ctx, self.param, 'python, train.py')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --command" in error_msg
        assert "JSON:" in error_msg
        assert "Simple:" in error_msg

    def test_invalid_json_format(self):
        """Test error for invalid JSON."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_list_parameter(self.ctx, self.param, '["invalid", json,]')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --command" in error_msg

    def test_non_list_json(self):
        """Test error when JSON parses but isn't a list."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_list_parameter(self.ctx, self.param, '{"not": "a list"}')

        error_msg = str(exc_info.value)
        assert "Expected a list for --command, got dict" in error_msg


class TestDictParameters:
    """Test suite for dictionary parameter parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.param = MockParam("environment")
        self.ctx = None

    def test_json_format_basic(self):
        """Test basic JSON dictionary format."""
        result = parse_dict_parameter(self.ctx, self.param, '{"VAR1": "foo", "VAR2": "bar"}')
        assert result == {"VAR1": "foo", "VAR2": "bar"}

    def test_json_format_with_spaces(self):
        """Test JSON format with spaces in values."""
        result = parse_dict_parameter(self.ctx, self.param, '{"VAR1": "value with spaces", "VAR2": "another value"}')
        assert result == {"VAR1": "value with spaces", "VAR2": "another value"}

    def test_json_format_empty_dict(self):
        """Test empty JSON dictionary."""
        result = parse_dict_parameter(self.ctx, self.param, '{}')
        assert result == {}

    def test_json_format_nested_quotes(self):
        """Test JSON format with nested quotes."""
        result = parse_dict_parameter(self.ctx, self.param, '{"VAR1": "He said \\"hello\\"", "VAR2": "bar"}')
        assert result == {"VAR1": "He said \"hello\"", "VAR2": "bar"}

    def test_simple_format_basic(self):
        """Test basic simple dictionary format."""
        result = parse_dict_parameter(self.ctx, self.param, '{VAR1: foo, VAR2: bar}')
        assert result == {"VAR1": "foo", "VAR2": "bar"}

    def test_simple_format_no_spaces(self):
        """Test simple format without spaces."""
        result = parse_dict_parameter(self.ctx, self.param, '{VAR1:foo,VAR2:bar}')
        assert result == {"VAR1": "foo", "VAR2": "bar"}

    def test_simple_format_with_quotes(self):
        """Test simple format with quoted values."""
        result = parse_dict_parameter(self.ctx, self.param, '{VAR1: "value with spaces", VAR2: bar}')
        assert result == {"VAR1": "value with spaces", "VAR2": "bar"}

    def test_simple_format_quoted_keys(self):
        """Test simple format with quoted keys."""
        result = parse_dict_parameter(self.ctx, self.param, '{"VAR1": foo, "VAR2": "bar"}')
        assert result == {"VAR1": "foo", "VAR2": "bar"}

    def test_simple_format_mixed_quotes(self):
        """Test simple format with mixed quote types."""
        result = parse_dict_parameter(self.ctx, self.param, "{VAR1: 'single', VAR2: \"double\"}")
        assert result == {"VAR1": "single", "VAR2": "double"}

    def test_simple_format_empty_dict(self):
        """Test empty simple dictionary."""
        result = parse_dict_parameter(self.ctx, self.param, '{}')
        assert result == {}

    def test_none_input(self):
        """Test None input returns None."""
        result = parse_dict_parameter(self.ctx, self.param, None)
        assert result is None

    def test_invalid_format_no_braces(self):
        """Test error for invalid format without braces."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_dict_parameter(self.ctx, self.param, 'VAR1: foo, VAR2: bar')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --environment" in error_msg
        assert "JSON:" in error_msg
        assert "Simple:" in error_msg

    def test_invalid_json_format(self):
        """Test error for invalid JSON."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_dict_parameter(self.ctx, self.param, '{"VAR1": "foo", invalid}')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --environment" in error_msg

    def test_simple_format_missing_colon(self):
        """Test error for simple format missing colon."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_dict_parameter(self.ctx, self.param, '{VAR1 foo, VAR2: bar}')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --environment" in error_msg

    def test_non_dict_json(self):
        """Test error when JSON parses but isn't a dictionary."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_dict_parameter(self.ctx, self.param, '["not", "a", "dict"]')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --environment" in error_msg


class TestComplexObjectParameters:
    """Test suite for complex object parameter parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.param = MockParam("volume")
        self.ctx = None

    def test_json_format_single_object(self):
        """Test JSON format with single object."""
        result = parse_complex_object_parameter(self.ctx, self.param, '{"name": "vol1", "type": "hostPath", "mount_path": "/data"}')
        assert len(result) == 1
        assert result[0] == {"name": "vol1", "type": "hostPath", "mount_path": "/data"}

    def test_json_format_array_allow_multiple(self):
        """Test JSON array format when allow_multiple=True."""
        json_array = '[{"name": "vol1", "type": "hostPath"}, {"name": "vol2", "type": "pvc"}]'
        result = parse_complex_object_parameter(self.ctx, self.param, json_array, allow_multiple=True)
        assert len(result) == 2
        assert result[0] == {"name": "vol1", "type": "hostPath"}
        assert result[1] == {"name": "vol2", "type": "pvc"}

    def test_json_format_array_disallow_multiple(self):
        """Test JSON array format error when allow_multiple=False."""
        json_array = '[{"name": "vol1", "type": "hostPath"}, {"name": "vol2", "type": "pvc"}]'
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, json_array, allow_multiple=False)
        
        error_msg = str(exc_info.value)
        assert "does not support JSON arrays" in error_msg

    def test_key_value_format_basic(self):
        """Test basic key-value format."""
        result = parse_complex_object_parameter(self.ctx, self.param, 'name=vol1,type=hostPath,mount_path=/data')
        assert len(result) == 1
        assert result[0] == {"name": "vol1", "type": "hostPath", "mount_path": "/data"}

    def test_key_value_format_with_equals_in_value(self):
        """Test key-value format with equals sign in value."""
        result = parse_complex_object_parameter(self.ctx, self.param, 'name=vol1,command=echo "x=y",type=hostPath')
        assert len(result) == 1
        assert result[0] == {"name": "vol1", "command": "echo \"x=y\"", "type": "hostPath"}

    def test_multiple_flags_allow_multiple(self):
        """Test multiple flag usage when allow_multiple=True."""
        values = [
            'name=vol1,type=hostPath,mount_path=/data1',
            'name=vol2,type=pvc,mount_path=/data2,claim_name=my-pvc'
        ]
        result = parse_complex_object_parameter(self.ctx, self.param, values, allow_multiple=True)
        assert len(result) == 2
        assert result[0] == {"name": "vol1", "type": "hostPath", "mount_path": "/data1"}
        assert result[1] == {"name": "vol2", "type": "pvc", "mount_path": "/data2", "claim_name": "my-pvc"}

    def test_multiple_flags_disallow_multiple(self):
        """Test multiple flag usage error when allow_multiple=False."""
        values = ['name=vol1,type=hostPath', 'name=vol2,type=pvc']
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, values, allow_multiple=False)
        
        error_msg = str(exc_info.value)
        assert "does not support multiple values" in error_msg

    def test_mixed_json_and_key_value(self):
        """Test mixing JSON and key-value formats in multiple flags."""
        values = [
            '{"name": "vol1", "type": "hostPath"}',
            'name=vol2,type=pvc,claim_name=my-pvc'
        ]
        result = parse_complex_object_parameter(self.ctx, self.param, values, allow_multiple=True)
        assert len(result) == 2
        assert result[0] == {"name": "vol1", "type": "hostPath"}
        assert result[1] == {"name": "vol2", "type": "pvc", "claim_name": "my-pvc"}

    def test_none_input(self):
        """Test None input returns None."""
        result = parse_complex_object_parameter(self.ctx, self.param, None)
        assert result is None

    def test_empty_list_input(self):
        """Test empty list input returns None."""
        result = parse_complex_object_parameter(self.ctx, self.param, [])
        assert result is None

    def test_invalid_key_value_format(self):
        """Test error for invalid key-value format."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, 'name=vol1,invalid_pair,type=hostPath')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --volume" in error_msg
        assert "JSON object:" in error_msg
        assert "Key-value:" in error_msg

    def test_json_array_invalid_item_type(self):
        """Test error for JSON array with invalid item type."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, '[{"name": "vol1"}, "invalid"]', allow_multiple=True)
        
        error_msg = str(exc_info.value)
        assert "JSON array item 2 must be an object" in error_msg

    def test_empty_key_in_key_value(self):
        """Test error for empty key in key-value format."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, '=value,name=vol1')
        
        error_msg = str(exc_info.value)
        assert "Invalid format for --volume" in error_msg


class TestCommaSeparatedList:
    """Test suite for legacy comma-separated list parsing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.param = MockParam("clusters")
        self.ctx = None

    def test_basic_comma_separated(self):
        """Test basic comma-separated format."""
        result = parse_comma_separated_list(self.ctx, self.param, 'cluster1,cluster2,cluster3')
        assert result == ['cluster1', 'cluster2', 'cluster3']

    def test_comma_separated_with_spaces(self):
        """Test comma-separated format with spaces."""
        result = parse_comma_separated_list(self.ctx, self.param, 'cluster1, cluster2, cluster3')
        assert result == ['cluster1', 'cluster2', 'cluster3']

    def test_single_item(self):
        """Test single item."""
        result = parse_comma_separated_list(self.ctx, self.param, 'single-cluster')
        assert result == ['single-cluster']

    def test_empty_items_filtered(self):
        """Test that empty items are filtered out."""
        result = parse_comma_separated_list(self.ctx, self.param, 'cluster1,,cluster2, ,cluster3')
        assert result == ['cluster1', 'cluster2', 'cluster3']

    def test_none_input(self):
        """Test None input returns None."""
        result = parse_comma_separated_list(self.ctx, self.param, None)
        assert result is None


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.list_param = MockParam("args")
        self.dict_param = MockParam("environment")
        self.complex_param = MockParam("volume")
        self.ctx = None

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        # List with unicode
        result = parse_list_parameter(self.ctx, self.list_param, '["café", "naïve", "résumé"]')
        assert result == ["café", "naïve", "résumé"]
        
        # Dict with unicode
        result = parse_dict_parameter(self.ctx, self.dict_param, '{"café": "naïve", "résumé": "value"}')
        assert result == {"café": "naïve", "résumé": "value"}

    def test_special_characters_in_values(self):
        """Test handling of special characters."""
        # JSON with special chars
        result = parse_dict_parameter(self.ctx, self.dict_param, '{"KEY": "value@#$%^&*()"}')
        assert result == {"KEY": "value@#$%^&*()"}
        
        # Simple format with special chars (quoted)
        result = parse_dict_parameter(self.ctx, self.dict_param, '{KEY: "value@#$%^&*()"}')
        assert result == {"KEY": "value@#$%^&*()"}

    def test_numbers_and_booleans(self):
        """Test handling of numbers and booleans in simple format."""
        result = parse_dict_parameter(self.ctx, self.dict_param, '{PORT: 8080, DEBUG: true, TIMEOUT: 30.5}')
        assert result == {"PORT": "8080", "DEBUG": "true", "TIMEOUT": "30.5"}

    def test_nested_quotes(self):
        """Test handling of nested quotes in values."""
        result = parse_dict_parameter(self.ctx, self.dict_param, '{CMD: "echo \\"hello world\\""}')
        assert result == {"CMD": "echo \"hello world\""}

    def test_path_values(self):
        """Test handling of file paths."""
        result = parse_complex_object_parameter(self.ctx, self.complex_param, 
                                              'name=vol1,type=hostPath,mount_path=/opt/ml/model,path=/home/user/data')
        assert result[0]["mount_path"] == "/opt/ml/model"
        assert result[0]["path"] == "/home/user/data"

    def test_empty_string_values(self):
        """Test handling of empty string values."""
        result = parse_dict_parameter(self.ctx, self.dict_param, '{KEY1: "", KEY2: value}')
        assert result == {"KEY1": "", "KEY2": "value"}

    def test_whitespace_handling(self):
        """Test handling of various whitespace scenarios."""
        # Extra whitespace in simple list
        result = parse_list_parameter(self.ctx, self.list_param, '[  python  ,  train.py  ]')
        assert result == ["python", "train.py"]
        
        # Extra whitespace in simple dict
        result = parse_dict_parameter(self.ctx, self.dict_param, '{  VAR1  :  foo  ,  VAR2  :  bar  }')
        assert result == {"VAR1": "foo", "VAR2": "bar"}


class TestErrorMessageQuality:
    """Test suite for error message quality and helpfulness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.param = MockParam("test_param")
        self.ctx = None

    def test_list_error_message_content(self):
        """Test that list error messages contain helpful information."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_list_parameter(self.ctx, self.param, 'invalid format')
        
        error_msg = str(exc_info.value)
        assert "--test_param" in error_msg
        assert "JSON:" in error_msg
        assert "Simple:" in error_msg
        assert "[\"item1\", \"item2\", \"item3\"]" in error_msg
        assert "[item1, item2, item3]" in error_msg

    def test_dict_error_message_content(self):
        """Test that dict error messages contain helpful information."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_dict_parameter(self.ctx, self.param, 'invalid format')
        
        error_msg = str(exc_info.value)
        assert "--test_param" in error_msg
        assert "JSON:" in error_msg
        assert "Simple:" in error_msg
        assert "{\"key\": \"value\", \"key2\": \"value2\"}" in error_msg
        assert "{key: value, key2: \"value with spaces\"}" in error_msg

    def test_complex_object_error_message_content(self):
        """Test that complex object error messages contain helpful information."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, 'invalid format', allow_multiple=True)
        
        error_msg = str(exc_info.value)
        assert "--test_param" in error_msg
        assert "JSON object:" in error_msg
        assert "JSON array:" in error_msg  # Should show array format when allow_multiple=True
        assert "Key-value:" in error_msg

    def test_complex_object_single_mode_error(self):
        """Test error message when allow_multiple=False."""
        with pytest.raises(ParameterParsingError) as exc_info:
            parse_complex_object_parameter(self.ctx, self.param, 'invalid format', allow_multiple=False)
        
        error_msg = str(exc_info.value)
        assert "JSON array:" not in error_msg  # Should not show array format when allow_multiple=False

    def test_parameter_name_in_error_messages(self):
        """Test that parameter names are correctly included in error messages."""
        test_cases = [
            (MockParam("environment"), parse_dict_parameter, "invalid"),
            (MockParam("command"), parse_list_parameter, "invalid"), 
            (MockParam("volume"), parse_complex_object_parameter, "invalid"),
        ]
        
        for param, parser_func, invalid_input in test_cases:
            with pytest.raises(ParameterParsingError) as exc_info:
                if parser_func == parse_complex_object_parameter:
                    parser_func(self.ctx, param, invalid_input)
                else:
                    parser_func(self.ctx, param, invalid_input)
            
            error_msg = str(exc_info.value)
            assert f"--{param.name}" in error_msg


class TestBackwardCompatibility:
    """Test suite for backward compatibility with existing formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ctx = None

    def test_existing_json_formats_still_work(self):
        """Test that all existing JSON formats continue to work."""
        param = MockParam("test")
        
        # Lists
        result = parse_list_parameter(self.ctx, param, '["python", "train.py"]')
        assert result == ["python", "train.py"]
        
        # Dicts  
        result = parse_dict_parameter(self.ctx, param, '{"VAR1":"foo","VAR2":"bar"}')
        assert result == {"VAR1": "foo", "VAR2": "bar"}
        
        # Complex objects
        result = parse_complex_object_parameter(self.ctx, param, '{"name":"vol1","type":"hostPath"}')
        assert result == [{"name": "vol1", "type": "hostPath"}]

    def test_existing_key_value_formats_still_work(self):
        """Test that existing key-value formats continue to work."""
        param = MockParam("volume")
        
        result = parse_complex_object_parameter(self.ctx, param, 'name=model-data,type=hostPath,mount_path=/data,path=/data')
        expected = {"name": "model-data", "type": "hostPath", "mount_path": "/data", "path": "/data"}
        assert result == [expected]

    def test_existing_comma_separated_still_works(self):
        """Test that comma-separated format still works."""
        param = MockParam("clusters")
        
        result = parse_comma_separated_list(self.ctx, param, "cluster1,cluster2,cluster3")
        assert result == ["cluster1", "cluster2", "cluster3"]


if __name__ == "__main__":
    # Run the tests if executed directly
    pytest.main([__file__, "-v"])
