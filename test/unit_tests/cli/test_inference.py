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
         patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint') as mock_endpoint_class, \
         patch('sagemaker.hyperpod.common.cli_decorators._is_valid_jumpstart_model_id') as mock_model_validation, \
         patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists') as mock_namespace_exists:

        # Mock enhanced error handling
        mock_model_validation.return_value = True  # Allow test model-id
        mock_namespace_exists.return_value = True  # Allow test namespace

        # Mock schema loading
        mock_load_schema.return_value = {
            "properties": {
                "model_id": {"type": "string"},
                "instance_type": {"type": "string"}
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
        result = runner.invoke(js_create, [
            '--namespace', 'test-ns',
            '--version', '1.0',
            '--model-id', 'test-model-id',
            '--instance-type', 'ml.t2.micro',
            '--endpoint-name', 'test-endpoint'
        ])

        assert result.exit_code == 0, result.output
        domain_obj.create.assert_called_once_with(name=None, namespace='test-ns')


def test_js_create_missing_required_args():
    runner = CliRunner()
    result = runner.invoke(js_create, [])
    assert result.exit_code != 0
    assert 'Missing option' in result.output


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_list(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    inst.list.return_value = [Mock(metadata=Mock(model_dump=lambda: {"name": "e"}))]
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_list, ['--namespace', 'ns'])
    assert result.exit_code == 0
    inst.list.assert_called_once_with('ns')


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_describe(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    inst.get.return_value = Mock(model_dump=lambda: {"name": "e"})
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_describe, ['--name', 'n', '--namespace', 'ns'])
    assert result.exit_code == 0
    inst.get.assert_called_once_with('n', 'ns')


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_delete(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    ep = Mock()
    ep.delete = Mock()
    inst.get.return_value = ep
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_delete, ['--name', 'n', '--namespace', 'ns'])
    assert result.exit_code == 0
    ep.delete.assert_called_once()


@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
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
                "model_volume_mount_name": {"type": "string"}
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
        result = runner.invoke(custom_create, [
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
        domain_obj.create.assert_called_once_with(name=None, namespace='test-ns')


def test_custom_create_missing_required_args():
    runner = CliRunner()
    result = runner.invoke(custom_create, [])
    assert result.exit_code != 0
    assert 'Missing option' in result.output


@patch('sagemaker.hyperpod.cli.commands.inference.Endpoint.get')
@patch('sagemaker.hyperpod.cli.commands.inference.boto3')
def test_custom_invoke_success(mock_boto3, mock_endpoint_get):
    mock_endpoint = Mock()
    mock_endpoint.endpoint_status = "InService"
    mock_endpoint_get.return_value = mock_endpoint

    mock_body = Mock()
    mock_body.read.return_value.decode.return_value = '{"ok": true}'
    mock_boto3.client.return_value.invoke_endpoint.return_value = {'Body': mock_body}

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


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_list(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    inst.list.return_value = [Mock(metadata=Mock(model_dump=lambda: {"name": "e"}))]
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_list, ['--namespace', 'ns'])
    assert result.exit_code == 0
    inst.list.assert_called_once_with('ns')


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_describe(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    inst.get.return_value = Mock(model_dump=lambda: {"name": "e"})
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_describe, ['--name', 'n', '--namespace', 'ns'])
    assert result.exit_code == 0
    inst.get.assert_called_once_with('n', 'ns')


@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_delete(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock()
    ep = Mock()
    ep.delete = Mock()
    inst.get.return_value = ep
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_delete, ['--name', 'n', '--namespace', 'ns'])
    assert result.exit_code == 0
    ep.delete.assert_called_once()


@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_get_operator_logs(mock_hp):
    inst = Mock(get_operator_logs=Mock(return_value='ol'))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_get_operator_logs, ['--since-hours', '2'])
    assert result.exit_code == 0
    assert 'ol' in result.output


# --------- Default Namespace Tests ---------

@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_list_default_namespace(mock_hp):
    inst = Mock(list=Mock(return_value=[]))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_list, [])
    assert result.exit_code == 0
    inst.list.assert_called_once_with('default')

@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_list_default_namespace(mock_hp):
    inst = Mock(list=Mock(return_value=[]))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_list, [])
    assert result.exit_code == 0
    inst.list.assert_called_once_with('default')

@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_list_pods(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock(list_pods=Mock(return_value="pods"))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_list_pods, ['--namespace', 'ns', '--endpoint-name', 'js-endpoint'])
    assert result.exit_code == 0
    assert 'pods' in result.output

@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_list_pods(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock(list_pods=Mock(return_value="pods"))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_list_pods, ['--namespace', 'ns', '--endpoint-name', 'custom-endpoint'])
    assert result.exit_code == 0
    assert 'pods' in result.output

@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPJumpStartEndpoint')
def test_js_get_logs(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock(get_logs=Mock(return_value="logs"))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(js_get_logs, ['--pod-name', 'p', '--namespace', 'ns'])
    assert result.exit_code == 0
    assert 'logs' in result.output

@patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
@patch('sagemaker.hyperpod.cli.commands.inference.HPEndpoint')
def test_custom_get_logs(mock_hp, mock_namespace_exists):
    mock_namespace_exists.return_value = True
    inst = Mock(get_logs=Mock(return_value='l'))
    mock_hp.model_construct.return_value = inst
    runner = CliRunner()
    result = runner.invoke(custom_get_logs, ['--pod-name', 'p', '--namespace', 'ns'])
    assert result.exit_code == 0
    assert 'l' in result.output
