import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from sagemaker.hyperpod.cli.init_utils import (
    is_dynamic_template,
    load_dynamic_schema
)


class TestIsDynamicTemplate:
    """Test cases for is_dynamic_template function"""

    def test_is_dynamic_template_true(self):
        """Test detection of dynamic template"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create .override_spec.json file
            (temp_path / ".override_spec.json").write_text('{"job_name": {"type": "string"}}')
            
            result = is_dynamic_template("hyp-recipe-job", temp_path)
            assert result is True

    def test_is_dynamic_template_false_no_spec_file(self):
        """Test non-dynamic template without spec file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = is_dynamic_template("hyp-pytorch-job", temp_path)
            assert result is False


class TestLoadDynamicSchema:
    """Test cases for load_dynamic_schema function"""

    def test_load_dynamic_schema_success(self):
        """Test successful schema loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create .override_spec.json
            spec = {
                "job_name": {"type": "string", "required": True},
                "epochs": {"type": "integer", "min": 1, "max": 100}
            }
            (temp_path / ".override_spec.json").write_text(json.dumps(spec))
            
            result = load_dynamic_schema(temp_path)
            
            assert result == spec
            assert "job_name" in result
            assert result["job_name"]["type"] == "string"

    def test_load_dynamic_schema_file_not_found(self):
        """Test schema loading with missing file returns empty dict"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            result = load_dynamic_schema(temp_path)
            assert result == {}

    def test_load_dynamic_schema_default_path(self):
        """Test with default path (current directory)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory and create spec file there
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                spec = {"test": {"type": "string"}}
                Path(".override_spec.json").write_text(json.dumps(spec))
                
                result = load_dynamic_schema()
                assert result == spec
            finally:
                os.chdir(original_cwd)


class TestGenerateStandardClickCommandHandlers:
    """Ensure _generate_standard_click_command uses handler-based options for complex fields.

    Regression test: a refactor accidentally replaced _get_handler_for_field +
    _get_click_option_config with create_click_option, which broke complex fields
    (volumes, security groups) that need multiple=True and JSON parsing callbacks.
    """

class TestGenerateStandardClickCommandHandlers:
    """Ensure _generate_standard_click_command uses handler-based option generation.

    Regression test: a refactor accidentally replaced _get_handler_for_field +
    _get_click_option_config with create_click_option, losing special type handling.
    """

    def test_uses_get_handler_for_field(self):
        """_generate_standard_click_command must call _get_handler_for_field for each field."""
        from unittest.mock import patch, MagicMock
        from sagemaker.hyperpod.cli.init_utils import _generate_standard_click_command, DEFAULT_TYPE_HANDLER

        with patch("sagemaker.hyperpod.cli.init_utils._get_handler_for_field",
                   return_value=DEFAULT_TYPE_HANDLER) as mock_handler, \
             patch("sagemaker.hyperpod.cli.init_utils._get_click_option_config",
                   return_value={"type": str, "help": ""}) as mock_config:

            decorator = _generate_standard_click_command("hyp-pytorch-job", "1.1")

            @decorator
            def dummy(option=None, value=None, model_config=None):
                pass

            assert mock_handler.call_count > 0, \
                "_get_handler_for_field was not called — handler-based generation was replaced"
            assert mock_config.call_count > 0, \
                "_get_click_option_config was not called — handler-based generation was replaced"

    def test_does_not_use_create_click_option(self):
        """_generate_standard_click_command must NOT use create_click_option (simple path)."""
        from unittest.mock import patch
        from sagemaker.hyperpod.cli.init_utils import _generate_standard_click_command

        with patch("sagemaker.hyperpod.cli.type_handler_utils.create_click_option") as mock_simple:
            decorator = _generate_standard_click_command("hyp-pytorch-job", "1.1")

            @decorator
            def dummy(option=None, value=None, model_config=None):
                pass

            assert mock_simple.call_count == 0, \
                "create_click_option was called — standard template should use handler-based generation"


class TestGenerateDynamicClickCommand:
    """Test _generate_dynamic_click_command generates options from .override_spec.json."""

    def test_generates_options_from_spec(self):
        """Options should be generated for each key in .override_spec.json."""
        import tempfile, json
        from pathlib import Path
        from unittest.mock import patch
        from sagemaker.hyperpod.cli.init_utils import _generate_dynamic_click_command

        spec = {
            "learning_rate": {"type": "float", "required": True, "default": 0.001},
            "max_epochs":    {"type": "integer", "required": True, "default": 5},
            "output_path":   {"type": "string", "required": False, "default": ""},
        }

        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".override_spec.json").write_text(json.dumps(spec))
            with patch("sagemaker.hyperpod.cli.init_utils.Path") as mock_path_cls:
                mock_path_cls.return_value.resolve.return_value = Path(tmp)
                with patch("sagemaker.hyperpod.cli.init_utils.load_dynamic_schema", return_value=spec):
                    decorator = _generate_dynamic_click_command()

        @decorator
        def dummy(option=None, value=None, model_config=None):
            pass

        param_names = {p.name for p in getattr(dummy, '__click_params__', [])}
        assert 'learning-rate' in param_names or 'learning_rate' in param_names
        assert 'max-epochs' in param_names or 'max_epochs' in param_names
        assert 'output-path' in param_names or 'output_path' in param_names

    def test_integer_field_has_int_type(self):
        """Integer fields in spec should produce int-typed Click options."""
        import json, tempfile
        from pathlib import Path
        from unittest.mock import patch
        from sagemaker.hyperpod.cli.init_utils import _generate_dynamic_click_command

        spec = {"max_epochs": {"type": "integer", "required": True, "default": 5}}

        with patch("sagemaker.hyperpod.cli.init_utils.load_dynamic_schema", return_value=spec):
            decorator = _generate_dynamic_click_command()

        @decorator
        def dummy(option=None, value=None, model_config=None):
            pass

        params = {p.name: p for p in getattr(dummy, '__click_params__', [])}
        param = params.get('max-epochs') or params.get('max_epochs')
        assert param is not None
        assert param.type.name == 'integer'
