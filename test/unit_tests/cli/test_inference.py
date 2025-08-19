import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
import sys
import importlib

import hyperpod_jumpstart_inference_template.registry as jreg
import hyperpod_custom_inference_template.registry as creg

# Import the non-create commands that don't need special handling
from sagemaker.hyperpod.cli.commands.inference import (
    js_create, custom_create, custom_invoke,
    js_list, custom_list,
    js_describe, custom_describe,
    js_delete, custom_delete,
    js_list_pods, custom_list_pods,
    js_get_logs, custom_get_logs,
    js_get_operator_logs, custom_get_operator_logs
)

# --------- JumpStart Commands ---------
@patch('sys.argv', ['pytest', '--version', '1.0'])
def test_js_create_with_required_args():
    """
    Test js_create with all required options via CLI runner, mocking schema and endpoint.
    """
    # Reload the inference module with mocked sys.argv
    if 'sagemaker.hyperpod.cli.commands.inference' in sys.modules:
        importlib.reload(sys.modules['sagemaker.hyperpod.cli.commands.inference'])
    
    from sagemaker.hyperpod.cli.commands.inference import js_create
    
    with patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version') as mock_load_schema, \
         patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint') as mock_endpoint_class:
        
        # Mock schema loading
        mock_load_schema.return_value = {
            "properties": {
                "model_id": {"type": "string"},
                "instance_type": {"type": "string"},
                "endpoint_name": {"type": "string", "default": ""}
            },
            "required": ["model_id", "instance_type"]
        }
        # Prepare mock model-to-domain mapping
        mock_model_class = Mock()
        mock_model_instance = Mock()
        domain_obj = Mock()
        domain_obj.create = Mock()
        mock_model_instance.to_domain.return_value = domain_obj
        mock_model_class.return_value = mock_model_instance
        mock_endpoint_class.model_construct.return_value = domain_obj

        jreg.SCHEMA_REGISTRY.clear()
        jreg.SCHEMA_REGISTRY['1.0'] = mock_model_class

        runner = CliRunner()
        result = runner.invoke(js_create(), [
            '--namespace', 'test-ns',
            '--version', '1.0',
            '--model-id', 'test-model-id',
            '--instance-type', 'ml.t2.micro',
            '--endpoint-name', 'test-endpoint'
        ])

        assert result.exit_code == 0, result.output
        domain_obj.create.assert_called_once_with(namespace='test-ns')


def test_js_create_missing_required_args():
    runner = CliRunner()
    result = runner.invoke(js_create(), [])
    assert result.exit_code != 0
    assert 'Missing option' in result.output


def test_js_list():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock()
        inst.list.return_value = [Mock(model_dump=lambda: {"metadata": {"name": "e"}})]
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_list, ['--namespace', 'ns'])
        assert result.exit_code == 0
        inst.list.assert_called_once_with('ns')


def test_js_describe():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock()
        # Mock get to return an endpoint object that has model_dump method
        mock_endpoint = Mock()
        mock_endpoint.model_dump = Mock(return_value={"name": "e"})
        inst.get.return_value = mock_endpoint
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_describe, ['--name', 'n', '--namespace', 'ns'])
        assert result.exit_code == 0
        inst.get.assert_called_once_with('n', 'ns')


def test_js_delete():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock()
        ep = Mock()
        ep.delete = Mock()
        inst.get.return_value = ep
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_delete, ['--name', 'n', '--namespace', 'ns'])
        assert result.exit_code == 0
        ep.delete.assert_called_once()


@patch('sagemaker.hyperpod.inference.hp_jumpstart_endpoint.HPJumpStartEndpoint')
def test_js_get_operator_logs(mock_hp):
    inst = Mock(get_operator_logs=Mock(return_value="ol"))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_get_operator_logs, ['--since-hours', '2'])
    assert result.exit_code == 0
    assert 'ol' in result.output


# --------- Custom Commands ---------

@patch('sys.argv', ['pytest', '--version', '1.0'])
def test_custom_create_with_required_args():
    """
    Test custom_create with all required options via CLI runner, mocking schema and endpoint.
    """
    # Reload the inference module with mocked sys.argv
    if 'sagemaker.hyperpod.cli.commands.inference' in sys.modules:
        importlib.reload(sys.modules['sagemaker.hyperpod.cli.commands.inference'])
    
    from sagemaker.hyperpod.cli.commands.inference import custom_create
    
    with patch('sagemaker.hyperpod.cli.inference_utils.load_schema_for_version') as mock_load_schema, \
         patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint') as mock_endpoint_class:
        
        # Mock schema loading to include storage flags
        mock_load_schema.return_value = {
            "properties": {
                "instance_type": {"type": "string"},
                "model_name": {"type": "string"},
                "model_source_type": {"type": "string", "enum": ["s3", "fsx"]},
                "s3_bucket_name": {"type": "string"},
                "s3_region": {"type": "string"},
                "image_uri": {"type": "string"},
                "container_port": {"type": "integer"},
                "model_volume_mount_name": {"type": "string"},
                "endpoint_name": {"type": "string", "default": ""}
            },
            "required": [
                "instance_type", "model_name", "model_source_type",
                "s3_bucket_name", "s3_region",
                "image_uri", "container_port", "model_volume_mount_name"
            ]
        }
        # Prepare mock model class
        mock_model_class = Mock()
        mock_model_instance = Mock()
        domain_obj = Mock()
        domain_obj.create = Mock()
        mock_model_instance.to_domain.return_value = domain_obj
        mock_model_class.return_value = mock_model_instance
        mock_endpoint_class.model_construct.return_value = domain_obj

        # Patch the registry mapping
        creg.SCHEMA_REGISTRY.clear()
        creg.SCHEMA_REGISTRY['1.0'] = mock_model_class
        runner = CliRunner()
        result = runner.invoke(custom_create(), [
            '--namespace', 'test-ns',
            '--version', '1.0',
            '--instance-type', 'ml.t2.micro',
            '--model-name', 'test-model',
            '--model-source-type', 's3',
            '--s3-bucket-name', 'test-bucket',
            '--s3-region', 'us-west-2',
            '--image-uri', 'test-image:latest',
            '--container-port', '8080',
            '--model-volume-mount-name', 'model-volume',
            '--endpoint-name', 'test-endpoint'
        ])

        assert result.exit_code == 0, result.output
        domain_obj.create.assert_called_once_with(namespace='test-ns')


def test_custom_create_missing_required_args():
    runner = CliRunner()
    result = runner.invoke(custom_create(), [])
    assert result.exit_code != 0
    assert 'Missing option' in result.output


def test_custom_invoke_success():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        hp_endpoint_mock = Mock()
        
        # Create the Endpoint mock
        endpoint_mock = Mock()
        mock_endpoint_instance = Mock()
        mock_endpoint_instance.endpoint_status = "InService"
        endpoint_mock.get.return_value = mock_endpoint_instance
        
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Mock boto3 client for invocation
        mock_body = Mock()
        mock_body.read.return_value.decode.return_value = '{"ok": true}'
        boto3_mock.client.return_value.invoke_endpoint.return_value = {'Body': mock_body}
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_invoke, [
            '--endpoint-name', 'ep',
            '--body', '{"x": 1}'
        ])

        assert result.exit_code == 0, result.output
        assert '"ok": true' in result.output


@patch('sagemaker.hyperpod.cli.commands.inference.boto3')
def test_custom_invoke_invalid_json(mock_boto3):
    runner = CliRunner()
    result = runner.invoke(custom_invoke, ['--endpoint-name', 'ep', '--body', 'bad'])
    assert result.exit_code != 0
    assert 'must be valid JSON' in result.output


def test_custom_list():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock()
        inst.list.return_value = [Mock(model_dump=lambda: {"metadata": {"name": "e"}})]
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_list, ['--namespace', 'ns'])
        assert result.exit_code == 0
        inst.list.assert_called_once_with('ns')


def test_custom_describe():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock()
        # Mock get to return an endpoint object that has model_dump method
        mock_endpoint = Mock()
        mock_endpoint.model_dump = Mock(return_value={"name": "e"})
        inst.get.return_value = mock_endpoint
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_describe, ['--name', 'n', '--namespace', 'ns'])
        assert result.exit_code == 0
        inst.get.assert_called_once_with('n', 'ns')


def test_custom_delete():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock()
        ep = Mock()
        ep.delete = Mock()
        inst.get.return_value = ep
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_delete, ['--name', 'n', '--namespace', 'ns'])
        assert result.exit_code == 0
        ep.delete.assert_called_once()


@patch('sagemaker.hyperpod.inference.hp_endpoint.HPEndpoint')
def test_custom_get_operator_logs(mock_hp):
    inst = Mock(get_operator_logs=Mock(return_value='ol'))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_get_operator_logs, ['--since-hours', '2'])
    assert result.exit_code == 0
    assert 'ol' in result.output


# --------- Default Namespace Tests ---------

def test_js_list_default_namespace():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock(list=Mock(return_value=[]))
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_list, [])
        assert result.exit_code == 0
        inst.list.assert_called_once_with('default')

def test_custom_list_default_namespace():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock(list=Mock(return_value=[]))
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_list, [])
        assert result.exit_code == 0
        inst.list.assert_called_once_with('default')

def test_js_list_pods():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock(list_pods=Mock(return_value="pods"))
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_list_pods, ['--namespace', 'ns'])
        assert result.exit_code == 0
        assert 'pods' in result.output

def test_custom_list_pods():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock(list_pods=Mock(return_value="pods"))
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_list_pods, ['--namespace', 'ns'])
        assert result.exit_code == 0
        assert 'pods' in result.output

def test_js_get_logs():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        # Create the HP endpoint mock
        hp_js_endpoint_mock = Mock()
        inst = Mock(get_logs=Mock(return_value="logs"))
        hp_js_endpoint_mock.model_construct.return_value = inst
        
        hp_endpoint_mock = Mock()
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(js_get_logs, ['--pod-name', 'p', '--namespace', 'ns'])
        assert result.exit_code == 0
        assert 'logs' in result.output

def test_custom_get_logs():
    # Patch the lazy loading function to return our mocks
    with patch('sagemaker.hyperpod.cli.commands.inference._ensure_inference_deps') as mock_deps:
        # Create mocks for all dependencies
        json_mock = __import__('json')
        boto3_mock = Mock()
        tabulate_mock = Mock()
        
        hp_js_endpoint_mock = Mock()
        
        # Create the HP endpoint mock
        hp_endpoint_mock = Mock()
        inst = Mock(get_logs=Mock(return_value='l'))
        hp_endpoint_mock.model_construct.return_value = inst
        
        endpoint_mock = Mock()
        generate_click_command_mock = Mock()
        js_reg_mock = Mock()
        c_reg_mock = Mock()
        telemetry_emitter_mock = Mock()
        feature_mock = Mock()
        
        # Return all mocked dependencies
        mock_deps.return_value = (
            json_mock, boto3_mock, tabulate_mock, hp_js_endpoint_mock, hp_endpoint_mock, 
            endpoint_mock, generate_click_command_mock, js_reg_mock, c_reg_mock, 
            telemetry_emitter_mock, feature_mock
        )
        
        runner = CliRunner()
        result = runner.invoke(custom_get_logs, ['--pod-name', 'p', '--namespace', 'ns'])
        assert result.exit_code == 0
        assert 'l' in result.output
