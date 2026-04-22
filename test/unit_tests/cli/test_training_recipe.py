import pytest
import json
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from kubernetes.client.rest import ApiException
from kubernetes import config
import click

from sagemaker.hyperpod.cli.commands.training_recipe import (
    _configure_dynamic_template,
    _create_dynamic_template,
    _init_training_job,
    # create_recipe_job_interactive
)
from sagemaker.hyperpod.cli.recipe_utils import (
    _validate_dynamic_template,
    _update_config_field,
    _fetch_recipe_from_hub,
    _validate_and_convert_value,
    _collect_parameter_interactively,
    _get_sagemaker_client,
    _get_s3_client,
    _get_k8s_custom_client,
    _download_s3_json,
    _download_s3_content,
    load_dynamic_schema
)


class TestValidateDynamicTemplate:
    """Test cases for _validate_dynamic_template function"""

    def test_validate_dynamic_template_success(self):
        """Test successful validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create .override_spec.json
            spec = {
                "job_name": {"type": "string", "required": True},
                "epochs": {"type": "integer", "min": 1, "max": 100, "required": False}
            }
            (temp_path / ".override_spec.json").write_text(json.dumps(spec))
            
            # Create valid config.yaml
            config = {"job_name": "test-job", "epochs": 50}
            (temp_path / "config.yaml").write_text(yaml.dump(config))
            
            # Should not raise exception
            result = _validate_dynamic_template(temp_path)
            assert result is True

    def test_validate_dynamic_template_missing_spec(self):
        """Test validation with missing .override_spec.json"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with pytest.raises(FileNotFoundError, match=".override_spec.json not found"):
                _validate_dynamic_template(temp_path)

    def test_validate_dynamic_template_missing_required_field(self):
        """Test validation with missing required field"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create .override_spec.json
            spec = {
                "job_name": {"type": "string", "required": True},
                "epochs": {"type": "integer", "required": False}
            }
            (temp_path / ".override_spec.json").write_text(json.dumps(spec))
            
            # Create config.yaml missing required field
            config = {"epochs": 50}
            (temp_path / "config.yaml").write_text(yaml.dump(config))
            
            with pytest.raises(ValueError, match="job_name: Required field is missing or empty"):
                _validate_dynamic_template(temp_path)


class TestCreateDynamicTemplate:
    """Test cases for _create_dynamic_template function"""

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._validate_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._submit_k8s_resources')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_k8s_custom_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_create_dynamic_template_success(self, mock_secho, mock_custom_client, mock_submit, mock_validate):
        """Test successful template creation and submission"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create k8s.jinja template
            k8s_template = """---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ job_name }}-config
---
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: {{ job_name }}"""
            (temp_path / "k8s.jinja").write_text(k8s_template)
            (temp_path / "config.yaml").write_text("job_name: test-job")
            
            config_data = {"job_name": "test-job"}
            
            # Mock validation success
            mock_validate.return_value = True
            
            # Mock Kubernetes client
            mock_custom_instance = MagicMock()
            mock_custom_client.return_value = mock_custom_instance
            
            # Execute
            _create_dynamic_template(temp_path, config_data)
            
            # Verify validation was called
            mock_validate.assert_called_once_with(temp_path)
            
            # Verify submit was called
            mock_submit.assert_called_once()
            
            # Verify success messages
            mock_secho.assert_any_call("✔️ Configuration validated successfully", fg="green")
            mock_secho.assert_any_call("✔️ Successfully submitted to HyperPod", fg="green")


class TestInitTrainingJob:
    """Test cases for _init_training_job function"""

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_training_job_success(self, mock_secho, mock_get_s3_client, mock_get_sagemaker_client):
        """Test successful recipe job initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock SageMaker client
            mock_sagemaker = MagicMock()
            mock_sagemaker.describe_hub_content.return_value = {
                'HubContentDocument': json.dumps({
                    'RecipeCollection': [{
                        'Type': 'FineTuning',
                        'CustomizationTechnique': 'lora',
                        'SupportedInstanceTypes': ['ml.p4d.24xlarge'],
                        'HpEksOverrideParamsS3Uri': 's3://bucket/override.json',
                        'HpEksPayloadTemplateS3Uri': 's3://bucket/template.yaml'
                    }]
                })
            }
            mock_get_sagemaker_client.return_value = mock_sagemaker
            
            # Mock S3 client
            mock_s3 = MagicMock()
            mock_s3.get_object.side_effect = [
                {'Body': MagicMock(read=lambda: json.dumps({"job_name": {"type": "string", "required": True}}).encode())},
                {'Body': MagicMock(read=lambda: b'apiVersion: v1\nkind: Job')}
            ]
            mock_get_s3_client.return_value = mock_s3
            
            result = _init_training_job(temp_dir, "hyp-recipe-job", "test-model", "lora", "ml.p4d.24xlarge")
            
            assert result is True
            assert Path(temp_dir, ".override_spec.json").exists()
            assert Path(temp_dir, "config.yaml").exists()
            assert Path(temp_dir, "k8s.jinja").exists()


    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_recipe_job_no_technique(self, mock_secho, mock_get_s3_client, mock_get_sagemaker_client):
        """Test that recipe job initialization fails when technique is None (technique is required)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_sagemaker = MagicMock()
            mock_get_sagemaker_client.return_value = mock_sagemaker

            result = _init_training_job(temp_dir, "hyp-recipe-job", "test-model", None, "ml.p4d.24xlarge")

            assert result is False

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._interactive_cluster_selection')
    @patch('sagemaker.hyperpod.cli.commands.cluster.set_cluster_context')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_training_job_with_interactive_selection(self, mock_secho, mock_get_s3_client, mock_get_sagemaker_client, mock_set_context, mock_interactive):
        """Test training job initialization with interactive cluster selection"""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_interactive.return_value = ("test-cluster", "ml.p4d.24xlarge")
            mock_set_context.main = MagicMock()

            mock_sagemaker = MagicMock()
            mock_sagemaker.describe_hub_content.return_value = {
                'HubContentDocument': json.dumps({
                    'RecipeCollection': [{
                        'Type': 'FineTuning',
                        'CustomizationTechnique': 'SFT',
                        'SupportedInstanceTypes': ['ml.p4d.24xlarge'],
                        'HpEksOverrideParamsS3Uri': 's3://bucket/override.json',
                        'HpEksPayloadTemplateS3Uri': 's3://bucket/template.yaml'
                    }]
                })
            }
            mock_get_sagemaker_client.return_value = mock_sagemaker

            mock_s3 = MagicMock()
            mock_s3.get_object.side_effect = [
                {'Body': MagicMock(read=lambda: json.dumps({"job_name": {"type": "string", "required": True}}).encode())},
                {'Body': MagicMock(read=lambda: b'apiVersion: v1\nkind: Job')}
            ]
            mock_get_s3_client.return_value = mock_s3

            result = _init_training_job(temp_dir, "hyp-recipe-job", "test-model", "SFT")

            assert result is True
            mock_interactive.assert_called_once()
            assert Path(temp_dir, ".override_spec.json").exists()
            assert Path(temp_dir, "config.yaml").exists()
            assert Path(temp_dir, "k8s.jinja").exists()

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._interactive_cluster_selection')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_training_job_interactive_selection_fails(self, mock_secho, mock_get_sagemaker_client, mock_interactive):
        """Test training job initialization when interactive selection fails"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock interactive selection failure
            mock_interactive.return_value = (None, None)
            
            mock_sagemaker = MagicMock()
            mock_get_sagemaker_client.return_value = mock_sagemaker
            
            result = _init_training_job(temp_dir, "hyp-recipe-job", "test-model", "lora")
            
            assert result is False
            mock_interactive.assert_called_once()


class TestUpdateConfigField:
    """Test cases for _update_config_field function"""

    def test_update_config_field_success(self):
        """Test successful config field update"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text("job_name: old-name\nepochs: 10\n")
            
            spec = {
                "job_name": {"type": "string", "required": True},
                "epochs": {"type": "integer", "min": 1, "max": 100}
            }
            
            _update_config_field(config_path, spec, "epochs", "50")
            
            updated_content = config_path.read_text()
            assert "epochs: 50" in updated_content
            assert "job_name: old-name" in updated_content

    def test_update_config_field_validation_error(self):
        """Test config field update with validation error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text("job_name: test\nepochs: 10\n")
            
            spec = {
                "epochs": {"type": "integer", "min": 1, "max": 100}
            }
            
            with pytest.raises(SystemExit):
                _update_config_field(config_path, spec, "epochs", "150")  # Exceeds max


class TestFetchRecipeFromHub:
    """Test cases for _fetch_recipe_from_hub function"""

    def test_fetch_recipe_single_match(self):
        """Test fetching recipe recipe with single matching recipe"""
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = {
            'HubContentDocument': json.dumps({
                'RecipeCollection': [{
                    'Type': 'FineTuning',
                    'CustomizationTechnique': 'lora',
                    'SupportedInstanceTypes': ['ml.p4d.24xlarge', 'ml.g5.xlarge']
                }]
            })
        }
        
        result = _fetch_recipe_from_hub(mock_client, "test-model", "hyp-recipe-job", "lora", "ml.p4d.24xlarge")
        
        assert result['Type'] == 'FineTuning'
        assert result['CustomizationTechnique'] == 'lora'
        assert 'ml.p4d.24xlarge' in result['SupportedInstanceTypes']

    def test_fetch_recipe_no_technique_success(self):
        """Test that fetching recipe without technique raises ValueError (technique is required)"""
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = {
            'HubContentDocument': json.dumps({
                'RecipeCollection': [{'Type': 'FineTuning', 'SupportedInstanceTypes': ['ml.p4d.24xlarge']}]
            })
        }

        with pytest.raises(ValueError, match="technique is required"):
            _fetch_recipe_from_hub(mock_client, "test-model", "hyp-recipe-job", None, "ml.p4d.24xlarge")



    def test_fetch_recipe_no_instance_type_match(self):
        """Test fetching recipe with no matching instance type"""
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = {
            'HubContentDocument': json.dumps({
                'RecipeCollection': [
                    {
                        'Type': 'FineTuning',
                        'CustomizationTechnique': 'lora',
                        'SupportedInstanceTypes': ['ml.g5.xlarge']
                    },
                    {
                        'Type': 'FineTuning',
                        'CustomizationTechnique': 'lora',
                        'SupportedInstanceTypes': ['ml.g4dn.xlarge']
                    }
                ]
            })
        }
        
        with pytest.raises(ValueError, match="Instance type ml.p4d.24xlarge not supported. Supported: \\['ml.g4dn.xlarge', 'ml.g5.xlarge'\\]"):
            _fetch_recipe_from_hub(mock_client, "test-model", "hyp-recipe-job", "lora", "ml.p4d.24xlarge")


class TestValidateAndConvertValue:
    """Test cases for _validate_and_convert_value function"""

    def test_validate_integer_success(self):
        """Test successful integer validation"""
        result = _validate_and_convert_value("42", {"type": "integer", "min": 1, "max": 100})
        assert result == 42

    def test_validate_integer_type_error(self):
        """Test integer validation with invalid type"""
        with pytest.raises(ValueError, match="Invalid integer value: 'not_a_number'. Please enter a valid integer."):
            _validate_and_convert_value("not_a_number", {"type": "integer"})

    def test_validate_float_success(self):
        """Test successful float validation"""
        result = _validate_and_convert_value("3.14", {"type": "float", "min": 0.0, "max": 10.0})
        assert result == 3.14

    def test_validate_float_min_error(self):
        """Test float validation below minimum"""
        with pytest.raises(ValueError, match="Value -1.0 is below the minimum allowed value of 0.0."):
            _validate_and_convert_value("-1.0", {"type": "float", "min": 0.0})

    def test_validate_float_max_error(self):
        """Test float validation above maximum"""
        with pytest.raises(ValueError, match="Value 15.0 exceeds the maximum allowed value of 10.0."):
            _validate_and_convert_value("15.0", {"type": "float", "max": 10.0})

    def test_validate_enum_success(self):
        """Test successful enum validation"""
        result = _validate_and_convert_value("option1", {"type": "string", "enum": ["option1", "option2"]})
        assert result == "option1"

    def test_validate_enum_error(self):
        """Test enum validation with invalid option"""
        with pytest.raises(ValueError, match="Invalid option 'invalid'. Please choose from: option1, option2."):
            _validate_and_convert_value("invalid", {"type": "string", "enum": ["option1", "option2"]})


# class TestCreateFineTuningJobInteractive:
#     """Test cases for create_recipe_job_interactive function"""

#     @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
#     def test_create_missing_parameters(self, mock_secho):
#         """Test create command with missing required parameters"""
#         # Call the function directly, not the Click command
#         from sagemaker.hyperpod.cli.commands.training_recipe import create_recipe_job_interactive
        
#         # Get the actual function, not the Click command wrapper
#         func = create_recipe_job_interactive.callback
#         result = func(None, "lora", "ml.p4d.24xlarge")
        
#         assert result is False
#         mock_secho.assert_called_with("❌ --model-name, --technique, and --instance-type are required for hyp-recipe-job", fg="red")

#     @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
#     def test_create_missing_technique(self, mock_secho):
#         """Test create command with missing technique"""
#         from sagemaker.hyperpod.cli.commands.training_recipe import create_recipe_job_interactive
        
#         func = create_recipe_job_interactive.callback
#         result = func("test-model", None, "ml.p4d.24xlarge")
        
#         assert result is False
#         mock_secho.assert_called_with("❌ --model-name, --technique, and --instance-type are required for hyp-recipe-job", fg="red")

#     @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
#     def test_create_missing_instance_type(self, mock_secho):
#         """Test create command with missing instance type"""
#         from sagemaker.hyperpod.cli.commands.training_recipe import create_recipe_job_interactive
        
#         func = create_recipe_job_interactive.callback
#         result = func("test-model", "lora", None)
        
#         assert result is False
#         mock_secho.assert_called_with("❌ --model-name, --technique, and --instance-type are required for hyp-recipe-job", fg="red")

#     @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
#     @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
#     @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_k8s_custom_client')
#     @patch('sagemaker.hyperpod.cli.commands.training_recipe._collect_all_parameters_interactively')
#     @patch('sagemaker.hyperpod.cli.commands.training_recipe._submit_k8s_resources')
#     @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
#     def test_create_success(self, mock_secho, mock_submit, mock_collect, mock_k8s_client, mock_s3_client, mock_sagemaker_client):
#         """Test successful create command"""
#         from sagemaker.hyperpod.cli.commands.training_recipe import create_recipe_job_interactive
        
#         # Mock SageMaker client
#         mock_sagemaker = MagicMock()
#         mock_sagemaker.describe_hub_content.return_value = {
#             'HubContentDocument': json.dumps({
#                 'RecipeCollection': [{
#                     'Type': 'FineTuning',
#                     'CustomizationTechnique': 'lora',
#                     'SupportedInstanceTypes': ['ml.p4d.24xlarge'],
#                     'HpEksOverrideParamsS3Uri': 's3://bucket/override.json',
#                     'HpEksPayloadTemplateS3Uri': 's3://bucket/template.yaml'
#                 }]
#             })
#         }
#         mock_sagemaker_client.return_value = mock_sagemaker
        
#         # Mock S3 client
#         mock_s3 = MagicMock()
#         mock_s3.get_object.side_effect = [
#             {'Body': MagicMock(read=lambda: json.dumps({"job_name": {"type": "string", "required": True}}).encode())},
#             {'Body': MagicMock(read=lambda: b'apiVersion: v1\nkind: Job')}
#         ]
#         mock_s3_client.return_value = mock_s3
        
#         # Mock interactive collection
#         mock_collect.return_value = {"job_name": "test-job"}
        
#         # Mock submit to return True
#         mock_submit.return_value = True
        
#         func = create_recipe_job_interactive.callback
#         result = func("test-model", "lora", "ml.p4d.24xlarge")
        
#         assert result is True
#         mock_secho.assert_any_call("✅ Recipe job created successfully!", fg="green", bold=True)


class TestInitFineTuningJobErrorPaths:
    """Test error paths for _init_training_job function"""

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._fetch_recipe_from_hub')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_missing_s3_uris(self, mock_secho, mock_fetch_recipe, mock_get_sagemaker_client, mock_get_s3_client):
        """Test init with missing S3 URIs in recipe"""
        mock_fetch_recipe.return_value = {}
        
        result = _init_training_job("test-dir", "hyp-recipe-job", "model", "technique", "instance")
        
        assert result is False
        mock_secho.assert_called_with("❌ Missing S3 URIs in recipe", fg="red")

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_s3_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._get_sagemaker_client')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe._fetch_recipe_from_hub')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_init_exception_handling(self, mock_secho, mock_fetch_recipe, mock_get_sagemaker_client, mock_get_s3_client):
        """Test init with exception handling"""
        mock_fetch_recipe.side_effect = Exception("Test error")
        
        result = _init_training_job("test-dir", "hyp-recipe-job", "model", "technique", "instance")
        
        assert result is False
        mock_secho.assert_called_with("❌ Error: Test error", fg="red")


class TestCollectParameterInteractively:
    """Test cases for _collect_parameter_interactively function"""

    @patch('builtins.input', return_value='test_value')
    @patch('sagemaker.hyperpod.cli.recipe_utils.click.secho')
    def test_collect_required_parameter(self, mock_secho, mock_input):
        """Test collecting a required parameter"""
        param_spec = {
            'type': 'string',
            'description': 'Test parameter',
            'required': True
        }
        
        key, value = _collect_parameter_interactively('test_param', param_spec)
        
        assert key == 'test_param'
        assert value == 'test_value'

    @patch('builtins.input', return_value='')
    @patch('sagemaker.hyperpod.cli.recipe_utils.click.secho')
    def test_collect_optional_parameter_empty(self, mock_secho, mock_input):
        """Test collecting optional parameter with empty input"""
        param_spec = {
            'type': 'string',
            'description': 'Test parameter',
            'required': False
        }
        
        key, value = _collect_parameter_interactively('test_param', param_spec)
        
        assert key == 'test_param'
        assert value is None

    @patch('builtins.input', side_effect=['', 'valid_value'])
    @patch('sagemaker.hyperpod.cli.recipe_utils.click.secho')
    def test_collect_required_parameter_retry(self, mock_secho, mock_input):
        """Test collecting required parameter with retry on empty input"""
        param_spec = {
            'type': 'string',
            'description': 'Test parameter',
            'required': True
        }
        
        key, value = _collect_parameter_interactively('test_param', param_spec)
        
        assert key == 'test_param'
        assert value == 'valid_value'
        mock_secho.assert_any_call("❌ This field is required. Please provide a value.", fg="red")

    @patch('builtins.input', return_value='')
    @patch('sagemaker.hyperpod.cli.recipe_utils.click.secho')
    def test_collect_parameter_with_default(self, mock_secho, mock_input):
        """Test collecting parameter with default value"""
        param_spec = {
            'type': 'string',
            'description': 'Test parameter',
            'required': False,
            'default': 'default_value'
        }
        
        key, value = _collect_parameter_interactively('test_param', param_spec)
        
        assert key == 'test_param'
        assert value == 'default_value'


class TestClientManagement:
    """Test cases for client management functions"""

    @patch('sagemaker.hyperpod.cli.recipe_utils.boto3.client')
    def test_get_sagemaker_client(self, mock_boto3_client):
        """Test SageMaker client creation"""
        # Reset global client
        import sagemaker.hyperpod.cli.recipe_utils as utils
        utils._sagemaker_client = None
        
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        client = _get_sagemaker_client()
        
        assert client == mock_client
        mock_boto3_client.assert_called_once_with(
            "sagemaker",
        )

    @patch('sagemaker.hyperpod.cli.recipe_utils.boto3.client')
    def test_get_s3_client(self, mock_boto3_client):
        """Test S3 client creation"""
        # Reset global client
        import sagemaker.hyperpod.cli.recipe_utils as utils
        utils._s3_client = None
        
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        client = _get_s3_client()
        
        assert client == mock_client
        mock_boto3_client.assert_called_once_with("s3")

    @patch('sagemaker.hyperpod.cli.recipe_utils.client.CustomObjectsApi')
    @patch('sagemaker.hyperpod.cli.recipe_utils.config.load_kube_config')
    def test_get_k8s_client_success(self, mock_load_config, mock_custom_api):
        """Test Kubernetes client creation success"""
        # Reset global client
        import sagemaker.hyperpod.cli.recipe_utils as utils
        utils._k8s_custom_client = None
        
        mock_client = MagicMock()
        mock_custom_api.return_value = mock_client
        
        client = _get_k8s_custom_client()
        
        assert client == mock_client
        mock_load_config.assert_called_once()

    @patch('sagemaker.hyperpod.cli.recipe_utils.client.CustomObjectsApi')
    @patch('sagemaker.hyperpod.cli.recipe_utils.config.load_incluster_config')
    @patch('sagemaker.hyperpod.cli.recipe_utils.config.load_kube_config')
    def test_get_k8s_client_fallback(self, mock_load_config, mock_load_incluster, mock_custom_api):
        """Test Kubernetes client creation with fallback"""
        # Reset global client
        import sagemaker.hyperpod.cli.recipe_utils as utils
        utils._k8s_custom_client = None
        
        mock_load_config.side_effect = config.ConfigException("Config error")
        mock_client = MagicMock()
        mock_custom_api.return_value = mock_client
        
        client = _get_k8s_custom_client()
        
        assert client == mock_client
        mock_load_incluster.assert_called_once()

    @patch('sagemaker.hyperpod.cli.recipe_utils.config.load_incluster_config')
    @patch('sagemaker.hyperpod.cli.recipe_utils.config.load_kube_config')
    def test_get_k8s_client_failure(self, mock_load_config, mock_load_incluster):
        """Test Kubernetes client creation failure"""
        # Reset global client
        import sagemaker.hyperpod.cli.recipe_utils as utils
        utils._k8s_custom_client = None
        
        mock_load_config.side_effect = config.ConfigException("Config error")
        mock_load_incluster.side_effect = config.ConfigException("Incluster error")
        
        with pytest.raises(Exception, match="Could not configure kubernetes python client"):
            _get_k8s_custom_client()


class TestCreateDynamicTemplateErrorPaths:
    """Test error paths for _create_dynamic_template function"""

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._validate_dynamic_template')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.sys.exit')
    def test_create_validation_error(self, mock_exit, mock_secho, mock_validate):
        """Test create with validation error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            mock_validate.side_effect = ValueError("Validation failed")
            
            _create_dynamic_template(temp_path, {})
            
            mock_secho.assert_called_with("❌ Validation failed", fg="red")
            mock_exit.assert_called_with(1)

    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.sys.exit')
    def test_create_missing_template(self, mock_exit, mock_secho):
        """Test create with missing k8s.jinja template"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            _create_dynamic_template(temp_path, {})
            
            mock_secho.assert_called_with("❌ .override_spec.json not found", fg="red")
            mock_exit.assert_called_with(1)


class TestDownloadFunctions:
    """Test cases for S3 download functions"""

    @patch('sagemaker.hyperpod.cli.recipe_utils.json.loads')
    def test_download_s3_json(self, mock_json_loads):
        """Test S3 JSON download"""
        from sagemaker.hyperpod.cli.recipe_utils import _download_s3_json
        
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'{"key": "value"}')
        }
        mock_json_loads.return_value = {"key": "value"}
        
        result = _download_s3_json(mock_s3_client, "s3://bucket/key.json")
        
        assert result == {"key": "value"}
        mock_s3_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.json")

    def test_download_s3_content(self):
        """Test S3 content download"""
        from sagemaker.hyperpod.cli.recipe_utils import _download_s3_content
        
        mock_s3_client = MagicMock()
        mock_s3_client.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'file content')
        }
        
        result = _download_s3_content(mock_s3_client, "s3://bucket/file.txt")
        
        assert result == "file content"
        mock_s3_client.get_object.assert_called_once_with(Bucket="bucket", Key="file.txt")


class TestInstanceTypeOverride:
    """Test cases for instance type override functionality in _generate_dynamic_config_yaml"""

    def _make_schema(self, instance_default="ml.g5.2xlarge"):
        return {
            "instance_type": {"type": "string", "required": True, "default": instance_default},
            "other_param":   {"type": "string", "required": False, "default": "default_value"},
        }

    @patch('sagemaker.hyperpod.cli.recipe_utils.load_dynamic_schema')
    def test_generate_config_with_instance_type_override(self, mock_load_schema):
        """Test that instance_type field is overridden with user input"""
        from sagemaker.hyperpod.cli.recipe_utils import _generate_dynamic_config_yaml
        mock_load_schema.return_value = self._make_schema()

        with tempfile.TemporaryDirectory() as temp_dir:
            _generate_dynamic_config_yaml(
                Path(temp_dir), "hyp-recipe-job",
                model_name="test-model", technique="SFT", instance_type="ml.g5.48xlarge"
            )
            content = (Path(temp_dir) / "config.yaml").read_text()
            assert "ml.g5.48xlarge" in content

    @patch('sagemaker.hyperpod.cli.recipe_utils.load_dynamic_schema')
    def test_generate_config_without_instance_type_override(self, mock_load_schema):
        """Test that default instance_type is used when no override provided"""
        from sagemaker.hyperpod.cli.recipe_utils import _generate_dynamic_config_yaml
        mock_load_schema.return_value = self._make_schema()

        with tempfile.TemporaryDirectory() as temp_dir:
            _generate_dynamic_config_yaml(
                Path(temp_dir), "hyp-recipe-job",
                model_name="test-model", technique="SFT"
            )
            content = (Path(temp_dir) / "config.yaml").read_text()
            assert "ml.g5.2xlarge" in content

    @patch('sagemaker.hyperpod.cli.recipe_utils.load_dynamic_schema')
    def test_generate_config_instance_type_override_only_affects_instance_type_field(self, mock_load_schema):
        """Test that instance_type override only affects the instance_type field"""
        from sagemaker.hyperpod.cli.recipe_utils import _generate_dynamic_config_yaml
        mock_load_schema.return_value = self._make_schema()

        with tempfile.TemporaryDirectory() as temp_dir:
            _generate_dynamic_config_yaml(
                Path(temp_dir), "hyp-recipe-job",
                model_name="test-model", technique="SFT", instance_type="ml.g5.48xlarge"
            )
            content = (Path(temp_dir) / "config.yaml").read_text()
            assert "ml.g5.48xlarge" in content
            assert "default_value" in content


class TestInteractiveClusterSelection:
    """Test cases for _interactive_cluster_selection function"""

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._fetch_recipe_from_hub')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_interactive_cluster_selection_no_supported_instance_types(self, mock_secho, mock_fetch_recipe):
        """Test interactive cluster selection with no supported instance types"""
        from sagemaker.hyperpod.cli.commands.training_recipe import _interactive_cluster_selection
        
        # Mock recipe with no supported instance types
        mock_fetch_recipe.return_value = {
            'SupportedInstanceTypes': []
        }
        
        mock_sagemaker_client = MagicMock()
        result = _interactive_cluster_selection(mock_sagemaker_client, "test-model", "hyp-recipe-job", "lora")
        
        assert result == (None, None)
        mock_secho.assert_any_call("❌ No supported instance types found in recipe", fg="red")

    @patch('sagemaker.hyperpod.cli.commands.training_recipe._fetch_recipe_from_hub')
    @patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho')
    def test_interactive_cluster_selection_exception_handling(self, mock_secho, mock_fetch_recipe):
        """Test interactive cluster selection with exception handling"""
        from sagemaker.hyperpod.cli.commands.training_recipe import _interactive_cluster_selection
        
        # Mock recipe fetch to raise exception
        mock_fetch_recipe.side_effect = Exception("Test error")
        
        mock_sagemaker_client = MagicMock()
        result = _interactive_cluster_selection(mock_sagemaker_client, "test-model", "hyp-recipe-job", "lora")
        
        assert result == (None, None)
        mock_secho.assert_any_call("❌ Error during cluster selection: Test error", fg="red")


class TestHypCliDeleteCommand:
    """Test cases for the CLI delete command fix"""

    def test_recipe_delete_command_registration(self):
        """Test that recipe delete command is properly registered"""
        from sagemaker.hyperpod.cli.hyp_cli import delete
        
        # Check that hyp-recipe-job delete command exists
        commands = delete.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Get the command and verify it's the delete command, not describe
        recipe_cmd = delete.get_command(None, "hyp-recipe-job")
        assert recipe_cmd is not None
        assert "Delete" in recipe_cmd.help or "delete" in recipe_cmd.help.lower()

    def test_recipe_delete_command_help_text(self):
        """Test that recipe delete command has correct help text"""
        from sagemaker.hyperpod.cli.hyp_cli import delete
        
        recipe_cmd = delete.get_command(None, "hyp-recipe-job")
        assert recipe_cmd is not None
        assert "Delete a HyperPod recipe job" in recipe_cmd.help


    def test_recipe_commands_registration(self):
        """Test that recipe commands are properly registered"""
        from sagemaker.hyperpod.cli.hyp_cli import list, describe, delete, list_pods, get_logs, get_operator_logs
        
        # Check list command
        commands = list.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Check describe command
        commands = describe.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Check delete command
        commands = delete.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Check list-pods command
        commands = list_pods.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Check get-logs command
        commands = get_logs.list_commands(None)
        assert "hyp-recipe-job" in commands
        
        # Check get-operator-logs command
        commands = get_operator_logs.list_commands(None)
        assert "hyp-recipe-job" in commands

    def test_recipe_command_help_texts(self):
        """Test that recipe commands have correct help text"""
        from sagemaker.hyperpod.cli.hyp_cli import list, describe, delete
        
        # Check list command help
        recipe_list_cmd = list.get_command(None, "hyp-recipe-job")
        assert recipe_list_cmd is not None
        assert "List all HyperPod recipe jobs" in recipe_list_cmd.help
        
        # Check describe command help
        recipe_describe_cmd = describe.get_command(None, "hyp-recipe-job")
        assert recipe_describe_cmd is not None
        assert "Describe a HyperPod recipe job" in recipe_describe_cmd.help
        
        # Check delete command help
        recipe_delete_cmd = delete.get_command(None, "hyp-recipe-job")
        assert recipe_delete_cmd is not None
        assert "Delete a HyperPod recipe job" in recipe_delete_cmd.help


class TestIsHubContentArn:
    def test_valid_private_hub_arn_with_version(self):
        from sagemaker.hyperpod.cli.recipe_utils import _is_hub_content_arn
        assert _is_hub_content_arn(
            "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/Model/my-model/1.0.0"
        ) is True

    def test_valid_public_hub_arn(self):
        from sagemaker.hyperpod.cli.recipe_utils import _is_hub_content_arn
        assert _is_hub_content_arn(
            "arn:aws:sagemaker:us-west-2:aws:hub-content/SageMakerPublicHub/Model/my-model/3.1.0"
        ) is True

    def test_valid_arn_without_version(self):
        from sagemaker.hyperpod.cli.recipe_utils import _is_hub_content_arn
        assert _is_hub_content_arn(
            "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/Model/my-model"
        ) is True

    def test_jumpstart_id_is_not_arn(self):
        from sagemaker.hyperpod.cli.recipe_utils import _is_hub_content_arn
        assert _is_hub_content_arn("meta-textgeneration-llama-3-1-8b-instruct") is False

    def test_hf_id_is_not_arn(self):
        from sagemaker.hyperpod.cli.recipe_utils import _is_hub_content_arn
        assert _is_hub_content_arn("meta-llama/Llama-3.1-8B-Instruct") is False


class TestParseHubContentArn:
    def test_parses_all_components_with_version(self):
        from sagemaker.hyperpod.cli.recipe_utils import _parse_hub_content_arn
        result = _parse_hub_content_arn(
            "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/ModelReference/my-model/3.1.0"
        )
        assert result == {
            "HubName": "MyHub",
            "HubContentType": "ModelReference",
            "HubContentName": "my-model",
            "HubContentVersion": "3.1.0",
        }

    def test_parses_without_version(self):
        from sagemaker.hyperpod.cli.recipe_utils import _parse_hub_content_arn
        result = _parse_hub_content_arn(
            "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/Model/my-model"
        )
        assert "HubContentVersion" not in result
        assert result["HubName"] == "MyHub"
        assert result["HubContentName"] == "my-model"


class TestFetchRecipeFromPrivateHub:
    def test_calls_describe_with_parsed_params(self):
        from sagemaker.hyperpod.cli.recipe_utils import _fetch_recipe_from_private_hub
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = {
            "HubContentDocument": json.dumps({"RecipeCollection": []})
        }
        arn = "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/Model/my-model/1.0.0"
        _fetch_recipe_from_private_hub(mock_client, arn)
        mock_client.describe_hub_content.assert_called_once_with(
            HubName="MyHub", HubContentType="Model",
            HubContentName="my-model", HubContentVersion="1.0.0"
        )

    def test_raises_on_invalid_arn(self):
        from sagemaker.hyperpod.cli.recipe_utils import _fetch_recipe_from_private_hub
        with pytest.raises(ValueError, match="Invalid Hub Content ARN"):
            _fetch_recipe_from_private_hub(MagicMock(), "not-an-arn")


class TestResolveHuggingfaceModelId:
    def test_resolves_via_search(self):
        from sagemaker.hyperpod.cli.recipe_utils import _resolve_huggingface_model_id
        mock_client = MagicMock()
        mock_client.list_hub_contents.return_value = {
            "HubContentSummaries": [{
                "HubContentName": "meta-textgeneration-llama-3-1-8b-instruct",
                "HubContentSearchKeywords": ["@recipe:finetuning_sft_lora"],
            }]
        }
        result = _resolve_huggingface_model_id(mock_client, "meta-llama/Llama-3.1-8B-Instruct")
        assert result == "meta-textgeneration-llama-3-1-8b-instruct"

    def test_falls_back_to_static_table(self):
        from sagemaker.hyperpod.cli.recipe_utils import _resolve_huggingface_model_id
        mock_client = MagicMock()
        mock_client.list_hub_contents.return_value = {"HubContentSummaries": []}
        result = _resolve_huggingface_model_id(mock_client, "Qwen/Qwen3-0.6B")
        assert result == "huggingface-reasoning-qwen3-06b"

    def test_raises_for_unknown_model(self):
        from sagemaker.hyperpod.cli.recipe_utils import _resolve_huggingface_model_id
        mock_client = MagicMock()
        mock_client.list_hub_contents.return_value = {"HubContentSummaries": []}
        with pytest.raises(ValueError, match="may not be supported"):
            _resolve_huggingface_model_id(mock_client, "someorg/Unknown-Model")

    def test_raises_on_ambiguous_matches(self):
        from sagemaker.hyperpod.cli.recipe_utils import _resolve_huggingface_model_id
        mock_client = MagicMock()
        mock_client.list_hub_contents.return_value = {
            "HubContentSummaries": [
                {"HubContentName": "model-a", "HubContentSearchKeywords": ["@recipe:finetuning_sft_lora"]},
                {"HubContentName": "model-b", "HubContentSearchKeywords": ["@recipe:finetuning_sft_lora"]},
            ]
        }
        with pytest.raises(ValueError, match="may not be supported"):
            _resolve_huggingface_model_id(mock_client, "someorg/SomeModel")


class TestFetchRecipeFromHubModelIdFormats:
    def _hub_doc(self, technique="SFT"):
        return {
            "HubContentDocument": json.dumps({"RecipeCollection": [{
                "Type": "FineTuning",
                "CustomizationTechnique": technique,
                "SupportedInstanceTypes": ["ml.p4d.24xlarge"],
                "HpEksOverrideParamsS3Uri": "s3://b/o",
                "HpEksPayloadTemplateS3Uri": "s3://b/t",
            }]})
        }

    def test_jumpstart_id_path(self):
        from sagemaker.hyperpod.cli.recipe_utils import _fetch_recipe_from_hub
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = self._hub_doc()
        result = _fetch_recipe_from_hub(mock_client, "meta-textgeneration-llama-3-1-8b-instruct", "hyp-recipe-job", "SFT")
        mock_client.describe_hub_content.assert_called_once_with(
            HubName="SageMakerPublicHub", HubContentType="Model",
            HubContentName="meta-textgeneration-llama-3-1-8b-instruct"
        )
        assert result["CustomizationTechnique"] == "SFT"

    def test_arn_path_uses_private_hub(self):
        from sagemaker.hyperpod.cli.recipe_utils import _fetch_recipe_from_hub
        mock_client = MagicMock()
        mock_client.describe_hub_content.return_value = self._hub_doc()
        arn = "arn:aws:sagemaker:us-west-2:123456789012:hub-content/MyHub/Model/my-model/1.0.0"
        _fetch_recipe_from_hub(mock_client, arn, "hyp-recipe-job", "SFT")
        mock_client.describe_hub_content.assert_called_once_with(
            HubName="MyHub", HubContentType="Model",
            HubContentName="my-model", HubContentVersion="1.0.0"
        )

    def test_hf_id_resolves_via_search(self):
        from sagemaker.hyperpod.cli.recipe_utils import _fetch_recipe_from_hub
        mock_client = MagicMock()
        mock_client.list_hub_contents.return_value = {
            "HubContentSummaries": [{
                "HubContentName": "meta-textgeneration-llama-3-1-8b-instruct",
                "HubContentSearchKeywords": ["@recipe:finetuning_sft_lora"],
            }]
        }
        mock_client.describe_hub_content.return_value = self._hub_doc()
        _fetch_recipe_from_hub(mock_client, "meta-llama/Llama-3.1-8B-Instruct", "hyp-recipe-job", "SFT", is_huggingface=True)
        mock_client.describe_hub_content.assert_called_once_with(
            HubName="SageMakerPublicHub", HubContentType="Model",
            HubContentName="meta-textgeneration-llama-3-1-8b-instruct"
        )


class TestWarnIfInstanceTypeUnavailable:
    def test_warns_when_instance_type_missing(self):
        from sagemaker.hyperpod.cli.commands.training_recipe import _warn_if_instance_type_unavailable
        node = MagicMock()
        node.metadata.labels = {"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
        with patch('sagemaker.hyperpod.cli.commands.training_recipe.config') as mock_cfg, \
             patch('sagemaker.hyperpod.cli.commands.training_recipe.client') as mock_k8s_client, \
             patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho') as mock_secho:
            mock_k8s_client.CoreV1Api.return_value.list_node.return_value.items = [node]
            _warn_if_instance_type_unavailable("ml.p5.48xlarge")
            mock_secho.assert_called_once()
            assert "ml.p5.48xlarge" in mock_secho.call_args[0][0]

    def test_silent_when_instance_type_present(self):
        from sagemaker.hyperpod.cli.commands.training_recipe import _warn_if_instance_type_unavailable
        node = MagicMock()
        node.metadata.labels = {"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
        with patch('sagemaker.hyperpod.cli.commands.training_recipe.config'), \
             patch('sagemaker.hyperpod.cli.commands.training_recipe.client') as mock_k8s_client, \
             patch('sagemaker.hyperpod.cli.commands.training_recipe.click.secho') as mock_secho:
            mock_k8s_client.CoreV1Api.return_value.list_node.return_value.items = [node]
            _warn_if_instance_type_unavailable("ml.g5.8xlarge")
            mock_secho.assert_not_called()

    def test_silent_on_exception(self):
        from sagemaker.hyperpod.cli.commands.training_recipe import _warn_if_instance_type_unavailable
        with patch('sagemaker.hyperpod.cli.commands.training_recipe.config') as mock_cfg:
            mock_cfg.load_kube_config.side_effect = Exception("no kubeconfig")
            _warn_if_instance_type_unavailable("ml.p5.48xlarge")
