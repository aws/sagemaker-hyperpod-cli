import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from kubernetes.client.rest import ApiException

from sagemaker.hyperpod.cli.commands.ray_dashboard_connection import create_ray_dashboard_connection


class TestRayDashboardConnectionCommand:
    """Test cases for ray-dashboard-connection command"""

    def setup_method(self):
        self.runner = CliRunner()

    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_success_returns_url(self, mock_custom_objects_api_class, mock_get_client):
        """Test successful creation returns the connection URL"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.return_value = {
            "status": {
                "connectionUrl": "https://my-cluster.spaces.example.com/bearer-auth?token=abc123"
            }
        }
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
            '--namespace', 'team-a',
        ])

        assert result.exit_code == 0
        assert "https://my-cluster.spaces.example.com/bearer-auth?token=abc123" in result.output
        mock_api.create_namespaced_custom_object.assert_called_once_with(
            group="connection.access.sagemaker.amazonaws.com",
            version="v1alpha1",
            namespace="team-a",
            plural="raydashboardconnections",
            body={
                "apiVersion": "connection.access.sagemaker.amazonaws.com/v1alpha1",
                "kind": "RayDashboardConnection",
                "metadata": {"namespace": "team-a"},
                "spec": {"clusterName": "my-raycluster"},
            },
        )

    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_default_namespace(self, mock_custom_objects_api_class, mock_get_client):
        """Test namespace defaults to 'default' when not specified"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.return_value = {
            "status": {"connectionUrl": "https://example.com/dashboard"}
        }
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
        ])

        assert result.exit_code == 0
        assert "https://example.com/dashboard" in result.output
        call_kwargs = mock_api.create_namespaced_custom_object.call_args[1]
        assert call_kwargs["namespace"] == "default"

    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_empty_url_raises_error(self, mock_custom_objects_api_class, mock_get_client):
        """Test that empty connectionUrl raises an error"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.return_value = {
            "status": {"connectionUrl": ""}
        }
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
            '--namespace', 'default',
        ])

        assert result.exit_code != 0
        assert "Failed to get dashboard URL" in result.output
        assert "contact your cluster administrator" in result.output

    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_no_status_raises_error(self, mock_custom_objects_api_class, mock_get_client):
        """Test that missing status raises an error"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.return_value = {
            "metadata": {"name": "generated-name"}
        }
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
        ])

        assert result.exit_code != 0
        assert "Failed to get dashboard URL" in result.output

    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_404_api_not_installed(self, mock_custom_objects_api_class, mock_get_client):
        """Test 404 when operator is not installed shows install instructions"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.side_effect = ApiException(
            status=404,
            reason="Not Found",
            http_resp=Mock(
                status=404,
                reason="Not Found",
                data=b'{"message":"the server could not find the requested resource","details":{"group":"connection.access.sagemaker.amazonaws.com","kind":"raydashboardconnections"}}'
            ),
        )
        mock_api.create_namespaced_custom_object.side_effect.body = (
            '{"message":"the server could not find the requested resource",'
            '"details":{"group":"connection.access.sagemaker.amazonaws.com","kind":"raydashboardconnections"}}'
        )
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
            '--namespace', 'default',
        ])

        assert result.exit_code != 0
        assert "RayDashboardConnection API is not available" in result.output
        assert "hyperpod-ray-endpoint-operator" in result.output

    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists', return_value=True)
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_404_namespace_not_found(self, mock_custom_objects_api_class, mock_get_client, mock_ns_exists):
        """Test 404 for missing namespace shows raw error"""
        mock_api = Mock()
        mock_api.create_namespaced_custom_object.side_effect = ApiException(
            status=404,
            reason="Not Found",
            http_resp=Mock(status=404, reason="Not Found", data=b'{"message":"namespaces not-exists not found"}'),
        )
        mock_api.create_namespaced_custom_object.side_effect.body = '{"message":"namespaces not-exists not found"}'
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
            '--namespace', 'not-exists',
        ])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "not-exists" in result.output

    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists', return_value=True)
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection._get_eks_api_client')
    @patch('sagemaker.hyperpod.cli.commands.ray_dashboard_connection.client.CustomObjectsApi')
    def test_create_403_raises_exception(self, mock_custom_objects_api_class, mock_get_client, mock_ns_exists):
        """Test 403 forbidden is propagated as an error"""
        mock_api = Mock()
        exc = ApiException(
            status=403,
            reason="Forbidden",
            http_resp=Mock(status=403, reason="Forbidden", data=b'{"message":"forbidden"}'),
        )
        exc.body = '{"message":"forbidden"}'
        mock_api.create_namespaced_custom_object.side_effect = exc
        mock_custom_objects_api_class.return_value = mock_api
        mock_get_client.return_value = Mock()

        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--cluster-name', 'my-raycluster',
        ])

        assert result.exit_code != 0

    def test_missing_cluster_name(self):
        """Test that --cluster-name is required"""
        result = self.runner.invoke(create_ray_dashboard_connection, [
            '--namespace', 'default',
        ])

        assert result.exit_code != 0
        assert "Missing option '--cluster-name'" in result.output
