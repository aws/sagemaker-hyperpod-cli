"""
Unit tests for init command training job functionality
"""
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import click
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.init import init


class TestInitTrainingJobCommands:
    """Test cases for init command with training job templates"""

    def test_init_recipe_job_template_choice(self):
        """Test that hyp-recipe-job is available as a template choice"""
        runner = CliRunner()
        result = runner.invoke(init, ['--help'])
        
        assert result.exit_code == 0
        assert 'hyp-recipe-job' in result.output

    @patch('sagemaker.hyperpod.cli.commands.init._init_training_job')
    def test_init_recipe_job_with_all_params(self, mock_init_training):
        """Test init hyp-recipe-job with all parameters"""
        mock_init_training.return_value = True

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--model-id', 'test-model',
                '--technique', 'SFT',
                '--instance-type', 'ml.p4d.24xlarge'
            ])

            assert result.exit_code == 0
            mock_init_training.assert_called_once_with(
                temp_dir, 'hyp-recipe-job', 'test-model', 'SFT', 'ml.p4d.24xlarge', is_huggingface=False
            )
            assert "initialized successfully" in result.output

    @patch('sagemaker.hyperpod.cli.commands.init._init_training_job')
    def test_init_recipe_job_without_technique(self, mock_init_training):
        """Test init hyp-recipe-job without technique shows error (technique is required)"""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--model-id', 'test-model',
                '--instance-type', 'ml.p4d.24xlarge'
            ])

            assert result.exit_code == 0
            assert "--technique is required" in result.output
            mock_init_training.assert_not_called()

    @patch('sagemaker.hyperpod.cli.commands.init._init_training_job')
    def test_init_recipe_job_without_instance_type(self, mock_init_training):
        """Test init hyp-recipe-job without instance type (triggers interactive selection)"""
        mock_init_training.return_value = True

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--model-id', 'test-model',
                '--technique', 'SFT',
            ])

            assert result.exit_code == 0
            mock_init_training.assert_called_once_with(
                temp_dir, 'hyp-recipe-job', 'test-model', 'SFT', None, is_huggingface=False
            )

    def test_init_recipe_job_missing_model_name(self):
        """Test init hyp-recipe-job without required model-id parameter"""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--technique', 'SFT',
                '--instance-type', 'ml.p4d.24xlarge'
            ])

            assert result.exit_code == 0
            assert "--model-id or --huggingface-model-id is required" in result.output

    @patch('sagemaker.hyperpod.cli.commands.init._init_training_job')
    def test_init_recipe_job_failure(self, mock_init_training):
        """Test init training job when initialization fails"""
        mock_init_training.return_value = False

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--model-id', 'test-model',
                '--technique', 'SFT',
                '--instance-type', 'ml.p4d.24xlarge'
            ])

            assert result.exit_code == 0
            assert "initialized successfully" not in result.output

    @patch('sagemaker.hyperpod.cli.commands.init._init_training_job')
    def test_init_recipe_job_with_huggingface_model_id(self, mock_init_training):
        """Test init hyp-recipe-job with --huggingface-model-id flag"""
        mock_init_training.return_value = True

        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--huggingface-model-id', 'meta-llama/Llama-3.1-8B-Instruct',
                '--technique', 'SFT',
                '--instance-type', 'ml.p4d.24xlarge'
            ])

            assert result.exit_code == 0
            mock_init_training.assert_called_once_with(
                temp_dir, 'hyp-recipe-job', 'meta-llama/Llama-3.1-8B-Instruct', 'SFT', 'ml.p4d.24xlarge', is_huggingface=True
            )

    def test_init_recipe_job_both_model_id_flags_error(self):
        """Test that providing both --model-id and --huggingface-model-id shows error"""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.invoke(init, [
                'hyp-recipe-job', temp_dir,
                '--model-id', 'test-model',
                '--huggingface-model-id', 'meta-llama/Llama-3.1-8B-Instruct',
                '--technique', 'SFT',
            ])

            assert result.exit_code == 0
            assert "Specify either --model-id or --huggingface-model-id, not both" in result.output


class TestInitUtilsChanges:
    """Test cases for changes in init_utils.py"""

    def test_is_dynamic_template_recipe_job(self):
        """Test is_dynamic_template recognizes hyp-recipe-job"""
        from sagemaker.hyperpod.cli.init_utils import is_dynamic_template
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            override_file = temp_path / ".override_spec.json"
            override_file.write_text('{"test": "data"}')
            
            assert is_dynamic_template("hyp-recipe-job", temp_path) is True

    def test_is_dynamic_template_other_template(self):
        """Test is_dynamic_template returns False for other templates"""
        from sagemaker.hyperpod.cli.init_utils import is_dynamic_template
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            override_file = temp_path / ".override_spec.json"
            override_file.write_text('{"test": "data"}')
            
            assert is_dynamic_template("hyp-pytorch-job", temp_path) is False

    def test_is_dynamic_template_no_override_file(self):
        """Test is_dynamic_template returns False when no override file exists"""
        from sagemaker.hyperpod.cli.init_utils import is_dynamic_template
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            assert is_dynamic_template("hyp-recipe-job", temp_path) is False


class TestInitConstantsChanges:
    """Test cases for changes in init_constants.py"""

    def test_templates_include_recipe_job(self):
        """Test that TEMPLATES includes hyp-recipe-job"""
        from sagemaker.hyperpod.cli.constants.init_constants import TEMPLATES
        
        assert "hyp-recipe-job" in TEMPLATES

    def test_recipe_job_has_dynamic_type(self):
        """Test that hyp-recipe-job is marked as dynamic"""
        from sagemaker.hyperpod.cli.constants.init_constants import TEMPLATES
        
        assert TEMPLATES["hyp-recipe-job"]["type"] == "dynamic"
