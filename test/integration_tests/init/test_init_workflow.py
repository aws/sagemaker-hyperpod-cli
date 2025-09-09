"""
Integration tests for init workflow commands.

Tests cross-command workflows, template rendering, and file system interactions.
Does NOT test CLI argument parsing or basic error handling (covered by unit tests).
"""
import yaml
import os
from pathlib import Path
from contextlib import contextmanager
import pytest
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.init import init, configure, validate, reset
from test.integration_tests.init.utils import (
    assert_command_succeeded,
    assert_command_failed_with_helpful_error,
    assert_config_values,
    assert_warning_displayed,
    assert_yes_no_prompt_displayed,
    assert_success_message_displayed,
)


@contextmanager
def change_directory(path):
    """Context manager for safely changing directories in tests."""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)


@pytest.fixture
def runner():
    """CLI test runner for invoking commands."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return str(tmp_path)


class TestConfigurationValidation:
    """Test configuration validation and error handling."""
    
    def test_invalid_instance_type_validation(self, temp_dir, runner):
        """Test that invalid instance types are caught during configure."""
        # Initialize jumpstart template
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            # Configure with invalid instance type - should fail immediately
            result2 = runner.invoke(
                configure_cmd, [
                    "--model-id", "test-model",
                    "--instance-type", "invalid.instance.type",
                    "--endpoint-name", "test-endpoint"
                ], catch_exceptions=False
            )
        
        # Configure should fail with helpful error about instance type
        assert_command_failed_with_helpful_error(result2, ["instance", "ml"])
    
    def test_invalid_model_id_validation(self, temp_dir, runner):
        """Test that model ID configuration works (validation is lenient)."""
        # Initialize jumpstart template
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            # Configure with any model ID (validation is lenient)
            result2 = runner.invoke(
                configure_cmd, [
                    "--model-id", "nonexistent-invalid-model-id-12345",
                    "--instance-type", "ml.g5.xlarge",
                    "--endpoint-name", "test-endpoint"
                ], catch_exceptions=False
            )
            assert_command_succeeded(result2)
            
            # Validate should pass (model ID validation is lenient)
            result3 = runner.invoke(validate, [], catch_exceptions=False)
        
        # Validation should pass with current lenient behavior
        assert_command_succeeded(result3)
        assert_success_message_displayed(result3, ["✔️", "valid"])
    
    def test_custom_s3_parameters_required(self, temp_dir, runner):
        """Test that required parameters are validated for custom endpoints."""
        # Initialize custom template
        result1 = runner.invoke(
            init, ["hyp-custom-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        result3 = None
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            # Configure with S3 source but missing required fields
            result2 = runner.invoke(
                configure_cmd, [
                    "--endpoint-name", "test-endpoint",
                    "--model-name", "test-model",
                    "--instance-type", "ml.g5.xlarge",
                    "--image-uri", "test-image:latest",
                    "--model-source-type", "s3"
                    # Missing container_port and model_volume_mount_name
                ], catch_exceptions=False
            )
            assert_command_succeeded(result2)  # Configure should accept it
            
            # Validate should catch missing required parameters
            result3 = runner.invoke(validate, [], catch_exceptions=False)
        
        # Validation should fail with helpful error about missing required params
        if result3 is not None:
            assert_command_failed_with_helpful_error(result3, ["container_port", "model_volume_mount_name"])
    
    def test_custom_fsx_parameters_required(self, temp_dir, runner):
        """Test that required parameters are validated for custom endpoints with FSx."""
        # Initialize custom template
        result1 = runner.invoke(
            init, ["hyp-custom-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        result3 = None
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            # Configure with FSx source but missing required fields
            result2 = runner.invoke(
                configure_cmd, [
                    "--endpoint-name", "test-endpoint",
                    "--model-name", "test-model",
                    "--instance-type", "ml.g5.xlarge",
                    "--image-uri", "test-image:latest",
                    "--model-source-type", "fsx"
                    # Missing container_port and model_volume_mount_name
                ], catch_exceptions=False
            )
            assert_command_succeeded(result2)  # Configure should accept it
            
            # Validate should catch missing required parameters
            result3 = runner.invoke(validate, [], catch_exceptions=False)
        
        # Validation should fail with helpful error about missing required params
        if result3 is not None:
            assert_command_failed_with_helpful_error(result3, ["container_port", "model_volume_mount_name"])
    
    def test_custom_s3_complete_configuration_validates(self, temp_dir, runner):
        """Test that complete custom endpoint configuration passes validation."""
        # Initialize custom template
        result1 = runner.invoke(
            init, ["hyp-custom-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            # Configure with complete parameters including required fields
            result2 = runner.invoke(
                configure_cmd, [
                    "--endpoint-name", "test-endpoint",
                    "--model-name", "test-model",
                    "--instance-type", "ml.g5.xlarge",
                    "--image-uri", "test-image:latest",
                    "--model-source-type", "s3",
                    "--s3-bucket-name", "test-bucket",
                    "--model-location", "models/test-model.tar.gz",
                    "--s3-region", "us-east-2",
                    "--container-port", "8080",
                    "--model-volume-mount-name", "model-volume"
                ], catch_exceptions=False
            )
            assert_command_succeeded(result2)
            
            # Validate should succeed with complete config
            result3 = runner.invoke(validate, [], catch_exceptions=False)
        
        # Validation should pass
        assert_command_succeeded(result3)
        assert_success_message_displayed(result3, ["✔️", "valid"])


class TestInitEdgeCases:
    """Test edge cases for init command - double init scenarios."""
    
    def test_double_init_same_template_prompts_reset(self, temp_dir, runner):
        """Test that re-running init with same template prompts for reset."""
        # First init
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        # Second init with same template - should prompt for reset
        result2 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], 
            input="n\n",  # Answer 'no' to override prompt
            catch_exceptions=False
        )
        
        # Use helper functions for better validation
        assert_warning_displayed(result2, ["already initialized", "override"])
        assert_yes_no_prompt_displayed(result2)
        assert "aborting init" in result2.output.lower()
    
    def test_double_init_same_template_accepts_override(self, temp_dir, runner):
        """Test that accepting override re-initializes successfully."""
        # First init
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        # Second init with same template - accept override
        result2 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], 
            input="y\n",  # Answer 'yes' to override prompt
            catch_exceptions=False
        )
        
        # Use helper functions for validation
        assert_warning_displayed(result2, ["already initialized", "override", "overriding config.yaml"])
        assert_yes_no_prompt_displayed(result2)
        assert_command_succeeded(result2)
    
    def test_double_init_different_template_warns_user(self, temp_dir, runner):
        """Test that re-running init with different template shows strong warning."""
        # First init with jumpstart
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        # Second init with custom - should warn strongly
        result2 = runner.invoke(
            init, ["hyp-custom-endpoint", temp_dir], 
            input="n\n",  # Answer 'no' to re-initialize prompt
            catch_exceptions=False
        )
        
        # Use helper functions for comprehensive validation
        assert_warning_displayed(result2, [
            "already initialized as", 
            "highly unrecommended", 
            "recommended path is create a new folder"
        ])
        assert_yes_no_prompt_displayed(result2)
        assert "aborting init" in result2.output.lower()
    
    def test_double_init_different_template_accepts_reinit(self, temp_dir, runner):
        """Test that accepting re-init with different template works."""
        # First init with jumpstart
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        # Second init with custom - accept re-initialization
        result2 = runner.invoke(
            init, ["hyp-custom-endpoint", temp_dir], 
            input="y\n",  # Answer 'yes' to re-initialize prompt
            catch_exceptions=False
        )
        
        # Use helper functions for validation
        assert_warning_displayed(result2, [
            "already initialized as", 
            "highly unrecommended", 
            "re-initializing"
        ])
        assert_yes_no_prompt_displayed(result2)
        assert_command_succeeded(result2)
        
        # Verify config was changed to new template
        assert_config_values(temp_dir, {"template": "hyp-custom-endpoint"})


class TestResetFunctionality:
    """Test reset command functionality and integration with other commands."""
    
    def test_reset_clears_config_to_defaults(self, temp_dir, runner):
        """Test that reset command clears config back to default values."""
        # Initialize and configure
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            result2 = runner.invoke(
                configure_cmd, [
                    "--model-id", "test-model",
                    "--instance-type", "ml.g5.xlarge",
                    "--endpoint-name", "test-endpoint"
                ], catch_exceptions=False
            )
            assert_command_succeeded(result2)
            
            # Verify config has values
            assert_config_values(temp_dir, {
                "model_id": "test-model",
                "instance_type": "ml.g5.xlarge",
                "endpoint_name": "test-endpoint"
            })
            
            # Reset config
            result3 = runner.invoke(reset, [], catch_exceptions=False)
            assert_command_succeeded(result3)
        
        # Verify config was reset (template should remain)
        config_path = Path(temp_dir) / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config.get('template') == "hyp-jumpstart-endpoint", "Template should be preserved"
        # Other fields should be reset to defaults (None or empty)
        assert config.get('model_id') is None or config.get('model_id') == ""
        assert config.get('endpoint_name') is None or config.get('endpoint_name') == ""
    
    def test_reset_and_reconfigure_workflow(self, temp_dir, runner):
        """Test reset -> reconfigure workflow."""
        # Initialize and configure
        result1 = runner.invoke(
            init, ["hyp-jumpstart-endpoint", temp_dir], catch_exceptions=False
        )
        assert_command_succeeded(result1)
        
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            result2 = runner.invoke(
                configure_cmd, [
                    "--model-id", "original-model",
                    "--instance-type", "ml.g5.xlarge"
                ], catch_exceptions=False
            )
        assert_command_succeeded(result2)
        assert_config_values(temp_dir, {
            "model_id": "original-model",
            "instance_type": "ml.g5.xlarge"
        })
        
        # Reset configuration
        with change_directory(temp_dir):
            result3 = runner.invoke(
                reset, [], input="y\n", catch_exceptions=False
            )
        assert_command_succeeded(result3)
        
        # Verify config is reset (should have empty/default values)
        config_path = Path(temp_dir) / "config.yaml"
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Config should exist but values should be reset
        assert config.get('model_id') in [None, ""]
        assert config.get('instance_type') in [None, ""]
        
        # Reconfigure with new values
        with change_directory(temp_dir):
            # Add sys.argv patching for configure command
            import sys
            from unittest.mock import patch
            with patch.object(sys, 'argv', ['hyp', 'configure']):
                import importlib
                from sagemaker.hyperpod.cli.commands import init as init_module
                importlib.reload(init_module)
                configure_cmd = init_module.configure
            
            result4 = runner.invoke(
                configure_cmd, [
                    "--model-id", "new-model",
                    "--instance-type", "ml.g5.2xlarge",
                    "--endpoint-name", "new-endpoint"
                ], catch_exceptions=False
            )
        assert_command_succeeded(result4)
        assert_config_values(temp_dir, {
            "model_id": "new-model",
            "instance_type": "ml.g5.2xlarge",
            "endpoint_name": "new-endpoint"
        })
        
        # Validate new configuration
        with change_directory(temp_dir):
            result5 = runner.invoke(validate, [], catch_exceptions=False)
        assert_command_succeeded(result5)