"""
Unit tests for error_constants module.
Tests all enums and constant mappings.
"""

import pytest
from sagemaker.hyperpod.common.exceptions.error_constants import (
    ResourceType,
    OperationType,
    RESOURCE_LIST_COMMANDS,
    RESOURCE_DISPLAY_NAMES
)


class TestResourceType:
    """Test ResourceType enum."""
    
    def test_resource_type_values(self):
        """Test that ResourceType enum has expected values."""
        assert ResourceType.HYP_PYTORCH_JOB.value == "hyp_pytorch_job"
        assert ResourceType.HYP_CUSTOM_ENDPOINT.value == "hyp_custom_endpoint"
        assert ResourceType.HYP_JUMPSTART_ENDPOINT.value == "hyp_jumpstart_endpoint"
    
    def test_resource_type_members(self):
        """Test ResourceType has expected members."""
        expected_members = {
            'HYP_PYTORCH_JOB',
            'HYP_CUSTOM_ENDPOINT', 
            'HYP_JUMPSTART_ENDPOINT'
        }
        actual_members = {member.name for member in ResourceType}
        assert actual_members == expected_members
    
    def test_resource_type_uniqueness(self):
        """Test that all ResourceType values are unique."""
        values = [member.value for member in ResourceType]
        assert len(values) == len(set(values)), "ResourceType values should be unique"


class TestOperationType:
    """Test OperationType enum."""
    
    def test_operation_type_values(self):
        """Test that OperationType enum has expected values."""
        assert OperationType.DELETE.value == "delete"
        assert OperationType.GET.value == "get"
        assert OperationType.DESCRIBE.value == "describe"
        assert OperationType.LIST.value == "list"
    
    def test_operation_type_members(self):
        """Test OperationType has expected members."""
        expected_members = {'DELETE', 'GET', 'DESCRIBE', 'LIST'}
        actual_members = {member.name for member in OperationType}
        assert actual_members == expected_members
    
    def test_operation_type_uniqueness(self):
        """Test that all OperationType values are unique."""
        values = [member.value for member in OperationType]
        assert len(values) == len(set(values)), "OperationType values should be unique"


class TestResourceListCommands:
    """Test RESOURCE_LIST_COMMANDS mapping."""
    
    def test_all_resource_types_mapped(self):
        """Test that all ResourceType enums have list commands."""
        for resource_type in ResourceType:
            assert resource_type in RESOURCE_LIST_COMMANDS, \
                f"ResourceType.{resource_type.name} missing from RESOURCE_LIST_COMMANDS"
    
    def test_command_format(self):
        """Test list commands have expected format."""
        expected_commands = {
            ResourceType.HYP_PYTORCH_JOB: "hyp list hyp-pytorch-job",
            ResourceType.HYP_CUSTOM_ENDPOINT: "hyp list hyp-custom-endpoint",
            ResourceType.HYP_JUMPSTART_ENDPOINT: "hyp list hyp-jumpstart-endpoint"
        }
        
        for resource_type, expected_command in expected_commands.items():
            actual_command = RESOURCE_LIST_COMMANDS[resource_type]
            assert actual_command == expected_command, \
                f"Wrong command for {resource_type.name}: got '{actual_command}', expected '{expected_command}'"
    
    def test_commands_are_strings(self):
        """Test that all commands are strings."""
        for resource_type, command in RESOURCE_LIST_COMMANDS.items():
            assert isinstance(command, str), \
                f"Command for {resource_type.name} should be string, got {type(command)}"
            assert len(command) > 0, f"Command for {resource_type.name} should not be empty"


class TestResourceDisplayNames:
    """Test RESOURCE_DISPLAY_NAMES mapping."""
    
    def test_all_resource_types_mapped(self):
        """Test that all ResourceType enums have display names."""
        for resource_type in ResourceType:
            assert resource_type in RESOURCE_DISPLAY_NAMES, \
                f"ResourceType.{resource_type.name} missing from RESOURCE_DISPLAY_NAMES"
    
    def test_display_name_format(self):
        """Test display names have expected format."""
        expected_names = {
            ResourceType.HYP_PYTORCH_JOB: "Job",
            ResourceType.HYP_CUSTOM_ENDPOINT: "Custom endpoint",
            ResourceType.HYP_JUMPSTART_ENDPOINT: "JumpStart endpoint"
        }
        
        for resource_type, expected_name in expected_names.items():
            actual_name = RESOURCE_DISPLAY_NAMES[resource_type]
            assert actual_name == expected_name, \
                f"Wrong display name for {resource_type.name}: got '{actual_name}', expected '{expected_name}'"
    
    def test_display_names_are_strings(self):
        """Test that all display names are strings."""
        for resource_type, display_name in RESOURCE_DISPLAY_NAMES.items():
            assert isinstance(display_name, str), \
                f"Display name for {resource_type.name} should be string, got {type(display_name)}"
            assert len(display_name) > 0, f"Display name for {resource_type.name} should not be empty"
    
    def test_display_names_user_friendly(self):
        """Test that display names are user-friendly (capitalized, readable)."""
        for resource_type, display_name in RESOURCE_DISPLAY_NAMES.items():
            # Should start with capital letter
            assert display_name[0].isupper(), \
                f"Display name '{display_name}' for {resource_type.name} should start with capital letter"
            
            # Should not contain underscores (user-friendly)
            assert '_' not in display_name, \
                f"Display name '{display_name}' for {resource_type.name} should not contain underscores"


class TestConstantConsistency:
    """Test consistency between different constant mappings."""
    
    def test_all_mappings_cover_same_resource_types(self):
        """Test that all constant dictionaries cover the same ResourceType values."""
        resource_types_in_commands = set(RESOURCE_LIST_COMMANDS.keys())
        resource_types_in_display = set(RESOURCE_DISPLAY_NAMES.keys())
        all_resource_types = set(ResourceType)
        
        assert resource_types_in_commands == all_resource_types, \
            "RESOURCE_LIST_COMMANDS should cover all ResourceType values"
        assert resource_types_in_display == all_resource_types, \
            "RESOURCE_DISPLAY_NAMES should cover all ResourceType values"
        assert resource_types_in_commands == resource_types_in_display, \
            "Both mappings should cover the same ResourceType values"
    
    def test_no_extra_mappings(self):
        """Test that constant dictionaries don't have extra keys."""
        all_resource_types = set(ResourceType)
        
        extra_in_commands = set(RESOURCE_LIST_COMMANDS.keys()) - all_resource_types
        extra_in_display = set(RESOURCE_DISPLAY_NAMES.keys()) - all_resource_types
        
        assert not extra_in_commands, f"RESOURCE_LIST_COMMANDS has extra keys: {extra_in_commands}"
        assert not extra_in_display, f"RESOURCE_DISPLAY_NAMES has extra keys: {extra_in_display}"
