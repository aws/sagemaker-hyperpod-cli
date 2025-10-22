import unittest

import pytest
import json
import click
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from sagemaker.hyperpod.cli.init_utils import _load_schema_for_version, save_template, generate_click_command, _save_cfn_jinja
from sagemaker.hyperpod.cli.constants.init_constants import CFN
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from pydantic import ValidationError

from sagemaker.hyperpod.cli.init_utils import (
    _load_schema_for_version, 
    save_template, 
    generate_click_command, 
    _save_k8s_jinja,
    save_config_yaml,
    load_config_and_validate,
    validate_config_against_model,
    filter_validation_errors_for_user_input,
    display_validation_results,
    build_config_from_schema,
)
from sagemaker.hyperpod.cli.constants.init_constants import CFN, CRD
import tempfile
import os


class TestSaveK8sJinja:
    """Test cases for _save_k8s_jinja function"""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('sagemaker.hyperpod.cli.init_utils.Path')
    @patch('sagemaker.hyperpod.cli.init_utils.os.path.join')
    @patch('builtins.print')
    def test_save_k8s_jinja_success(self, mock_print, mock_join, mock_path, mock_file):
        """Test successful saving of K8s Jinja template"""
        directory = "/test/dir"
        content = "test k8s content"
        mock_join.return_value = "/test/dir/k8s.jinja"
        mock_path.return_value.mkdir = Mock()
        
        result = _save_k8s_jinja(directory, content)
        
        # Verify directory creation
        mock_path.assert_called_once_with(directory)
        mock_path.return_value.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Verify file writing
        mock_file.assert_called_once_with("/test/dir/k8s.jinja", "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(content)
        
        # Verify return value
        assert result == "/test/dir/k8s.jinja"


def create_mock_template(schema_type, registry=None):
    """Helper to create properly structured mock template"""
    return {
        'schema_type': schema_type,
        'registry': registry or {'1.0': Mock()},
        'schema_pkg': 'mock_schema_pkg',
        'template': 'mock_template',
        'type': 'jinja'
    }


class TestSaveTemplate:
    """Test cases for save_template function"""
    
    @patch('sagemaker.hyperpod.cli.init_utils._get_latest_version_from_registry')
    @patch('sagemaker.hyperpod.cli.init_utils._save_k8s_jinja')
    def test_save_template_crd_success(self, mock_save_k8s, mock_get_version):
        """Test save_template with CRD template type"""
        mock_get_version.return_value = '1.0'
        mock_templates = {
            'test-crd': {
                'schema_type': CRD,
                'template_registry': {'1.0': 'crd template content'}
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            result = save_template('test-crd', Path('/test/dir'))
            
            assert result is True
            mock_save_k8s.assert_called_once_with(
                directory='/test/dir',
                content='crd template content'
            )
    
    @patch('sagemaker.hyperpod.cli.init_utils._get_latest_version_from_registry')
    @patch('sagemaker.hyperpod.cli.init_utils._save_cfn_jinja')
    def test_save_template_cfn_success(self, mock_save_cfn, mock_get_version):
        """Test save_template with CFN template type"""
        mock_get_version.return_value = '1.0'
        mock_templates = {
            'test-cfn': {
                'schema_type': CFN,
                'template_registry': {'1.0': 'cfn template content'}
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            result = save_template('test-cfn', Path('/test/dir'))
            
            assert result is True
            mock_save_cfn.assert_called_once_with(
                directory='/test/dir',
                content='cfn template content'
            )
    
    
    @patch('sagemaker.hyperpod.cli.init_utils._save_k8s_jinja')
    @patch('sagemaker.hyperpod.cli.init_utils.click.secho')
    def test_save_template_exception_handling(self, mock_secho, mock_save_k8s):
        """Test save_template handles exceptions gracefully"""
        mock_templates = {
            'test-template': {
                'schema_type': CRD,
                'template': 'content'
            }
        }
        
        # Make _save_k8s_jinja raise an exception
        mock_save_k8s.side_effect = Exception("Test exception")
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            result = save_template('test-template', Path('/test/dir'))
            
            assert result is False
            mock_secho.assert_called_once()
            assert "Template generation failed" in mock_secho.call_args[0][0]


class TestSaveConfigYaml:
    """Test cases for save_config_yaml function"""
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('sagemaker.hyperpod.cli.init_utils.os.makedirs')
    @patch('sagemaker.hyperpod.cli.init_utils.os.path.join')
    @patch('builtins.print')
    def test_save_config_yaml_success(self, mock_print, mock_join, mock_makedirs, mock_file):
        """Test successful saving of config.yaml"""
        prefill = {
            'template': 'hyp-cluster-stack',
            'version': '1.0',
            'namespace': 'test-namespace'
        }
        comment_map = {
            'template': 'Template type',
            'version': 'Schema version',
            'namespace': '[Required] Kubernetes namespace'
        }
        directory = '/test/dir'
        mock_join.return_value = '/test/dir/config.yaml'
        
        save_config_yaml(prefill, comment_map, directory)
        
        # Verify directory creation
        mock_makedirs.assert_called_once_with(directory, exist_ok=True)
        
        # Verify file operations
        mock_file.assert_called_once_with('/test/dir/config.yaml', 'w')
        
        # Verify content written
        written_calls = mock_file().write.call_args_list
        written_content = ''.join(call[0][0] for call in written_calls)
        
        assert '# Template type' in written_content
        assert 'template: hyp-cluster-stack' in written_content
        assert '# [Required] Kubernetes namespace' in written_content
        assert 'namespace: test-namespace' in written_content
        
    def test_save_config_yaml_handles_none_values(self):
        """Test that None values are converted to empty strings"""
        prefill = {
            'template': 'hyp-cluster-stack',
            'optional_field': None
        }
        comment_map = {
            'template': 'Template type',
            'optional_field': 'Optional field'
        }
        
        with patch('builtins.open', mock_open()) as mock_file, \
             patch('sagemaker.hyperpod.cli.init_utils.os.makedirs'), \
             patch('sagemaker.hyperpod.cli.init_utils.os.path.join', return_value='/test/config.yaml'), \
             patch('builtins.print'):
            
            save_config_yaml(prefill, comment_map, '/test')
            
            written_calls = mock_file().write.call_args_list
            written_content = ''.join(call[0][0] for call in written_calls)
            
            assert 'optional_field: ' in written_content  # Should be empty string, not None


class TestLoadConfig:
    """Test cases for load_config function"""
    
    def test_load_config_success(self):
        """Test successful loading of config.yaml"""
        config_content = """
template: hyp-cluster-stack
version: 1.0
namespace: test-namespace
"""
        mock_templates = {
            'hyp-cluster-stack': create_mock_template(CFN)
        }
        
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            
            data, template, version = load_config_and_validate()
            
            assert data['template'] == 'hyp-cluster-stack'
            assert data['version'] == 1.0  # YAML loads this as float
            assert data['namespace'] == 'test-namespace'
            assert template == 'hyp-cluster-stack'
            assert str(version) == '1.0'
    
    def test_load_config_default_version(self):
        """Test loading config with default version when not specified"""
        config_content = """
template: hyp-cluster-stack
namespace: test-namespace
"""
        mock_templates = {
            'hyp-cluster-stack': create_mock_template(CFN)
        }
        
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            
            data, template, version = load_config_and_validate()
            
            assert version == '1.0'  # Default version
    
    @patch('sagemaker.hyperpod.cli.init_utils.click.secho')
    def test_load_config_unknown_template(self, mock_secho):
        """Test load_config with unknown template"""
        config_content = """
template: unknown-template
version: 1.0
"""
        mock_templates = {
            'hyp-cluster-stack': create_mock_template(CFN)
        }
        
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            
            # This should raise SystemExit due to unknown template
            with pytest.raises(SystemExit) as exc_info:
                load_config_and_validate()
            
            # Verify exit code
            assert exc_info.value.code == 1
            
            mock_secho.assert_called_once_with(
                "❌  Unknown template 'unknown-template' in config.yaml", 
                fg="red"
            )


class TestValidateConfigAgainstModel:
    """Test cases for validate_config_against_model function"""
    
    def test_validate_config_cfn_success(self):
        """Test successful validation for CFN template"""
        config_data = {
            'template': 'hyp-cluster-stack',
            'version': '1.0',
            'namespace': 'test-namespace'
        }
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            # Mock successful validation - the registry model should be called
            mock_registry['1.0'].return_value = Mock()
            
            errors = validate_config_against_model(config_data, 'hyp-cluster-stack', '1.0')
            
            assert errors == []
            # Verify the registry model was called with filtered config (no template/version)
            mock_registry['1.0'].assert_called_once_with(namespace='test-namespace')
    
    def test_validate_config_cfn_validation_error(self):
        """Test validation error handling for CFN template"""
        config_data = {
            'template': 'hyp-cluster-stack',
            'version': '1.0',
            'invalid_field': 'invalid_value'
        }
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
            # Mock validation error
            mock_error = ValidationError.from_exception_data('TestModel', [
                {
                    'type': 'missing',
                    'loc': ('required_field',),
                    'msg': 'Field required',
                    'input': {}
                }
            ])
            mock_registry['1.0'].side_effect = mock_error
            
            errors = validate_config_against_model(config_data, 'hyp-cluster-stack', '1.0')
            
            assert len(errors) == 1
            assert 'required_field: Field required' in errors[0]
    
    def test_validate_config_handles_list_values(self):
        """Test that list values are converted to JSON strings"""
        config_data = {
            'template': 'hyp-cluster-stack',
            'version': '1.0',
            'tags': ['tag1', 'tag2']
        }
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cli.init_utils._get_handler_for_field') as mock_get_handler:
            
            # Mock handler
            mock_from_dicts = Mock(return_value=['tag1', 'tag2'])
            mock_handler = {'from_dicts': mock_from_dicts}
            mock_get_handler.return_value = mock_handler
            
            validate_config_against_model(config_data, 'hyp-cluster-stack', '1.0')
            
            # Verify handler was called
            mock_get_handler.assert_called_with('hyp-cluster-stack', 'tags')
            mock_from_dicts.assert_called_with(['tag1', 'tag2'])


class TestFilterValidationErrorsForUserInput:
    """Test cases for filter_validation_errors_for_user_input function"""
    
    def test_filter_validation_errors_success(self):
        """Test filtering validation errors for user input fields"""
        validation_errors = [
            'namespace: Field required',
            'instance_type: Invalid choice',
            'optional_field: Field required',
            'user_field: Invalid format'
        ]
        user_input_fields = {'namespace', 'user_field'}
        
        filtered_errors = filter_validation_errors_for_user_input(
            validation_errors, user_input_fields
        )
        
        assert len(filtered_errors) == 2
        assert 'namespace: Field required' in filtered_errors
        assert 'user_field: Invalid format' in filtered_errors
        assert 'instance_type: Invalid choice' not in filtered_errors
        assert 'optional_field: Field required' not in filtered_errors
    
    def test_filter_validation_errors_no_matches(self):
        """Test filtering when no errors match user input fields"""
        validation_errors = [
            'field1: Error message',
            'field2: Another error'
        ]
        user_input_fields = {'field3', 'field4'}
        
        filtered_errors = filter_validation_errors_for_user_input(
            validation_errors, user_input_fields
        )
        
        assert filtered_errors == []
    
    def test_filter_validation_errors_malformed_error(self):
        """Test filtering handles malformed error strings"""
        validation_errors = [
            'namespace: Field required',
            'malformed error without colon',
            'user_field: Valid error'
        ]
        user_input_fields = {'namespace', 'user_field'}
        
        filtered_errors = filter_validation_errors_for_user_input(
            validation_errors, user_input_fields
        )
        
        # Should only include properly formatted errors
        assert len(filtered_errors) == 2
        assert 'namespace: Field required' in filtered_errors
        assert 'user_field: Valid error' in filtered_errors


class TestDisplayValidationResults:
    """Test cases for display_validation_results function"""
    
    @patch('sagemaker.hyperpod.cli.init_utils.click.secho')
    def test_display_validation_results_success(self, mock_secho):
        """Test displaying successful validation results"""
        validation_errors = []
        
        result = display_validation_results(
            validation_errors, 
            success_message="Config is valid!",
            error_prefix="Errors found:"
        )
        
        assert result is True
        mock_secho.assert_called_once_with("✔️  Config is valid!", fg="green")
    
    @patch('sagemaker.hyperpod.cli.init_utils.click.echo')
    @patch('sagemaker.hyperpod.cli.init_utils.click.secho')
    def test_display_validation_results_with_errors(self, mock_secho, mock_echo):
        """Test displaying validation results with errors"""
        validation_errors = [
            'namespace: Field required',
            'instance_type: Invalid choice'
        ]
        
        result = display_validation_results(
            validation_errors,
            success_message="Config is valid!",
            error_prefix="Validation errors:"
        )
        
        assert result is False
        mock_secho.assert_called_once_with("❌  Validation errors:", fg="red")
        
        # Verify individual errors were displayed
        assert mock_echo.call_count == 2
        mock_echo.assert_any_call("  – namespace: Field required")
        mock_echo.assert_any_call("  – instance_type: Invalid choice")


class TestBuildConfigFromSchema:
    """Test cases for build_config_from_schema function"""
    
    def test_build_config_cfn_template(self):
        """Test building config for CFN template"""
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry,
                'schema_pkg': 'test_pkg'
            }
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cli.init_utils._load_schema_for_version') as mock_load_schema, \
             patch('sagemaker.hyperpod.common.utils.get_default_namespace', return_value='test-namespace'):
            
            # Mock schema
            mock_load_schema.return_value = {
                'properties': {
                    'namespace': {'description': 'Test field description', 'examples': ['default']},
                    'instance_type': {'description': 'Test field description', 'examples': ['ml.g5.xlarge']}
                },
                'required': ['namespace']
            }
            
            config, comment_map = build_config_from_schema('hyp-cluster-stack', '1.0')
            
            assert config['template'] == 'hyp-cluster-stack'
            assert 'namespace' in config
            assert 'instance_type' in config
            assert comment_map['namespace'] == "[Required] Test field description"
    
    def test_build_config_with_model_config(self):
        """Test building config with user-provided model config"""
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry,
                'schema_pkg': 'test_pkg'
            }
        }
        
        # Mock model config
        mock_model = Mock()
        mock_model.model_dump.return_value = {
            'namespace': 'user-namespace',
            'instance_type': 'ml.p4d.24xlarge'
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cli.init_utils._load_schema_for_version') as mock_load_schema, \
             patch('sagemaker.hyperpod.cli.init_utils._get_handler_for_field') as mock_get_handler:
            
            # Mock schema
            mock_load_schema.return_value = {
                'properties': {
                    'namespace': {'description': 'Test description'},
                    'instance_type': {'description': 'Test description'}
                },
                'required': []
            }
            
            # Mock handler
            mock_to_dicts = Mock(return_value=['user-namespace'])
            mock_merge_dicts = Mock(return_value='user-namespace')
            mock_handler = {
                'to_dicts': mock_to_dicts,
                'merge_dicts': mock_merge_dicts
            }
            mock_get_handler.return_value = mock_handler
            
            config, comment_map = build_config_from_schema(
                'hyp-cluster-stack', '1.0', model_config=mock_model
            )
            
            assert config['namespace'] == 'user-namespace'
            assert config['instance_type'] == 'user-namespace'  # Both will be processed by handler
    
    def test_build_config_with_existing_config(self):
        """Test building config with existing configuration"""
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry,
                'schema_pkg': 'test_pkg'
            }
        }
        existing_config = {
            'template': 'hyp-cluster-stack',
            'namespace': 'existing-namespace',
            'version': '1.0'
        }
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cli.init_utils._load_schema_for_version') as mock_load_schema:
            
            # Mock schema
            mock_load_schema.return_value = {
                'properties': {
                    'namespace': {'description': 'Test description'},
                    'instance_type': {'description': 'Test description'}
                },
                'required': []
            }
            
            config, comment_map = build_config_from_schema(
                'hyp-cluster-stack', '1.0', existing_config=existing_config
            )
            
            assert config['namespace'] == 'existing-namespace'
            # Template should not be duplicated from existing_config
            assert config['template'] == 'hyp-cluster-stack'


class TestGenerateClickCommandEnhanced:
    """Enhanced test cases for generate_click_command function focusing on union building"""
    
    def test_generate_click_command_union_building_priority(self):
        """Test that CFN templates override CRD templates in union building"""
        # Use context managers to ensure proper cleanup
        with patch('sagemaker.hyperpod.cli.init_utils._load_schema_for_version') as mock_load_schema, \
             patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack') as mock_cluster_stack, \
             patch('sys.argv', ['hyp', 'configure']), \
             patch('sagemaker.hyperpod.cli.init_utils.load_config') as mock_load_config, \
             patch('sagemaker.hyperpod.cli.init_utils.Path') as mock_path:
            
            # Mock config.yaml exists and load_config
            mock_path.return_value.resolve.return_value.__truediv__.return_value.is_file.return_value = True
            mock_load_config.return_value = ({}, 'crd-template', '1.0')  # Use crd-template to trigger schema loading
            
            # Mock CRD schema
            crd_schema = {
                'properties': {
                    'namespace': {
                        'type': 'string',
                        'description': 'CRD namespace description'
                    },
                    'crd_only_field': {
                        'type': 'string', 
                        'description': 'CRD only field'
                    }
                }
            }
            mock_load_schema.return_value = crd_schema
            
            # Mock CFN model fields - create a proper mock that can be iterated
            mock_field_info = Mock()
            mock_field_info.description = "CFN namespace description"
            
            # Set up the mock properly to avoid iteration issues
            mock_cluster_stack.model_fields = {
                'namespace': mock_field_info,  # This should override CRD
                'cfn_only_field': mock_field_info
            }
            mock_cluster_stack.model_json_schema.return_value = {
                'properties': {
                    'namespace': {'examples': ['cfn-example']},
                    'cfn_only_field': {'examples': ['cfn-field-example']}
                }
            }
            mock_cluster_stack.get_template.return_value = json.dumps({
                'Parameters': {
                    'Namespace': {'Type': 'String', 'Description': 'CFN Namespace param'},
                    'CfnParam': {'Type': 'String', 'Description': 'CFN only param'}
                }
            })
            
            mock_templates = {
                'crd-template': {
                    'schema_type': CRD,
                    'schema_pkg': 'test.pkg',
                    'registry': {'1.0': Mock}
                },
                'cfn-template': {
                    'schema_type': CFN
                }
            }
            
            with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
                decorator = generate_click_command()
                
                # The decorator should be created successfully
                assert callable(decorator)
                
                # Verify that _load_schema_for_version was called for CRD template
                mock_load_schema.assert_called_with('1.0', 'test.pkg')
    
    def test_generate_click_command_handles_list_descriptions(self):
        """Test that generate_click_command handles list descriptions properly"""
        with patch('sagemaker.hyperpod.cli.init_utils._load_schema_for_version') as mock_load_schema, \
             patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack') as mock_cluster_stack:
            
            # Mock schema with list description (the bug we fixed)
            schema_with_list_desc = {
                'properties': {
                    'field_with_list_desc': {
                        'type': 'string',
                        'description': ['First part', 'Second part', 'Third part']
                    },
                    'normal_field': {
                        'type': 'string',
                        'description': 'Normal string description'
                    }
                }
            }
            mock_load_schema.return_value = schema_with_list_desc
            
            mock_templates = {
                'crd-template': {
                    'schema_type': CRD,
                    'schema_pkg': 'test.pkg',
                    'registry': {'1.0': Mock}
                }
            }
            
            # Set up HpClusterStack mock properly
            mock_cluster_stack.model_fields = {}
            mock_cluster_stack.model_json_schema.return_value = {'properties': {}}
            mock_cluster_stack.get_template.return_value = json.dumps({'Parameters': {}})
            
            with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
                # This should not raise an AttributeError
                decorator = generate_click_command()
                assert callable(decorator)
    
    def test_generate_click_command_path(self):
        """Test generate_click_command"""
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN
            }
        }
        
        config_content = """
template: hyp-cluster-stack
version: 1.0
namespace: test-namespace
"""
        
        with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack') as mock_cluster_stack:
            
            # Set up HpClusterStack mock properly
            mock_cluster_stack.model_fields = {}
            mock_cluster_stack.model_json_schema.return_value = {'properties': {}}
            mock_cluster_stack.get_template.return_value = json.dumps({'Parameters': {}})
            
            decorator = generate_click_command()
            
            @decorator
            def test_func(model_config):
                return model_config
            
            # Should be able to call the decorated function
            assert callable(test_func)


class TestLoadConfigAndValidate:
    """Test cases for load_config_and_validate function"""
    
    def test_load_config_and_validate_success(self):
        """Test successful config loading and validation"""
        config_content = """
template: hyp-cluster-stack
version: 1.0
namespace: test-namespace
"""
        mock_templates = {
            'hyp-cluster-stack': create_mock_template(CFN)
        }
        
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack') as mock_cluster_stack:
            
            # Mock successful validation
            mock_cluster_stack.return_value = Mock()
            
            data, template, version = load_config_and_validate()
            
            assert data['template'] == 'hyp-cluster-stack'
            assert data['version'] == 1.0  # YAML loads this as float
            assert data['namespace'] == 'test-namespace'
            assert template == 'hyp-cluster-stack'
            assert str(version) == '1.0'  # YAML loads this as float

    def test_load_config_and_validate_failure(self):
        """Test config loading with validation failure"""
        config_content = """
template: hyp-cluster-stack
version: 1.0
namespace: test-namespace
"""
        mock_registry = {'1.0': Mock()}
        mock_templates = {
            'hyp-cluster-stack': {
                'schema_type': CFN,
                'registry': mock_registry
            }
        }
        
        with patch('pathlib.Path.is_file', return_value=True), \
             patch('pathlib.Path.read_text', return_value=config_content), \
             patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates), \
             patch('sagemaker.hyperpod.cli.init_utils.display_validation_results', return_value=False):
            
            # Mock validation failure by making display_validation_results return False
            # This should raise SystemExit due to validation failure
            with pytest.raises(SystemExit) as exc_info:
                load_config_and_validate()
            
            # Verify exit code
            assert exc_info.value.code == 1
        
    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_success(self, mock_get_data):
        data = {"properties": {"x": {"type": "string"}}}
        mock_get_data.return_value = json.dumps(data).encode()
        result = _load_schema_for_version('1.2', 'pkg')
        assert result == data
        mock_get_data.assert_called_once_with('pkg.v1_2', 'schema.json')

    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_not_found(self, mock_get_data):
        mock_get_data.return_value = None
        with pytest.raises(click.ClickException) as exc:
            _load_schema_for_version('3.0', 'mypkg')
        assert "Could not load schema.json for version 3.0" in str(exc.value)

    @patch('sagemaker.hyperpod.cli.init_utils.pkgutil.get_data')
    def test_invalid_json(self, mock_get_data):
        mock_get_data.return_value = b'invalid'
        with pytest.raises(json.JSONDecodeError):
            _load_schema_for_version('1.0', 'pkg')


@patch('builtins.open', new_callable=mock_open)
@patch('sagemaker.hyperpod.cli.init_utils.Path')
@patch('sagemaker.hyperpod.cli.init_utils._get_latest_version_from_registry')
@patch('sagemaker.hyperpod.cli.init_utils.os.path.join')
@patch('sagemaker.hyperpod.cluster_management.hp_cluster_stack.HpClusterStack.get_template')
def test_save_cfn_jinja_called(mock_get_template,
                               mock_join,
                               mock_get_version,
                               mock_path,
                               mock_file):
    # Setup
    mock_get_version.return_value = '1.0'
    mock_templates = {
        'test-template': {
            'schema_type': CFN,
            'template_registry': {'1.0': 'test template content'}
        }
    }
    mock_join.return_value = '/test/dir/cfn_params.jinja'
    mock_path.return_value.mkdir = Mock()
    mock_get_template.return_value = '{"Parameters": {}}'

    with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
        # Execute
        result = save_template('test-template', Path('/test/dir'))

        # Assert
        assert result is True
        mock_file.assert_called_once_with('/test/dir/cfn_params.jinja', 'w', encoding='utf-8')
        # Content should be written as-is since template now includes all sections
        written_content = mock_file().write.call_args[0][0]
        assert 'test template content' in written_content


def test_generate_click_command_cfn_case():
    # Setup
    mock_templates = {
        'cfn-template': {
            'schema_type': CFN
        }
    }
    
    with patch('sagemaker.hyperpod.cli.init_utils.TEMPLATES', mock_templates):
        # Execute
        decorator = generate_click_command()
        
        # Create a dummy function to decorate
        @decorator
        def dummy_func(template, directory, namespace, version, model_config):
            return model_config
        
        # Assert that the decorator was created successfully
        assert callable(dummy_func)