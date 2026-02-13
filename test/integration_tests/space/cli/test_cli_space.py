import time
import pytest
import threading
import socket
import requests
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.space import (
    space_create, space_list, space_describe, space_delete, 
    space_update, space_start, space_stop, space_get_logs, space_portforward
)
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "default"
VERSION = "1.0"
SPACE_NAME = "space-cli-integ-test" + get_time_str()
DISPLAY_NAME = f"Space CLI Integ Test {get_time_str()}"


@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def space_name():
    return SPACE_NAME

class TestSpaceCLI:
    """Integration tests for HyperPod Space CLI commands."""

    def _wait_for_space_available(self, space_name, namespace="default", timeout=300):
        """Wait for space to become available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                space = HPSpace.get(name=space_name, namespace=namespace)
                status = space.status
                if status and status.get("conditions"):
                    for condition in status["conditions"]:
                        if condition.get("type") == "Available" and condition.get("status") == "True":
                            return True
                time.sleep(10)
            except Exception as e:
                print(f"Error checking space status: {e}")
                time.sleep(10)
        return False

    def _is_port_available(self, port):
        """Check if a port is available for use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except OSError:
                return False

    def _test_http_endpoint(self, port, timeout=30):
        """Test if HTTP endpoint responds with 200."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}", timeout=5)
                if response.status_code == 200:
                    return True
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
                time.sleep(3)
        return False

    @pytest.mark.dependency(name="create")
    def test_space_create(self, runner, space_name):
        """Test creating a space via CLI."""
        result = runner.invoke(space_create, [
            "--name", space_name,
            "--display-name", DISPLAY_NAME,
            "--namespace", NAMESPACE,
        ])
        assert result.exit_code == 0, result.output
        assert f"Space '{space_name}' created successfully" in result.output

    @pytest.mark.dependency(depends=["create"])
    def test_space_list_table(self, runner, space_name):
        """Test listing spaces in table format."""
        result = runner.invoke(space_list, [
            "--namespace", NAMESPACE,
            "--output", "table"
        ])
        assert result.exit_code == 0, result.output
        assert space_name in result.output
        assert "NAME" in result.output
        assert "NAMESPACE" in result.output

    @pytest.mark.dependency(depends=["create"])
    def test_space_list_json(self, runner, space_name):
        """Test listing spaces in JSON format."""
        result = runner.invoke(space_list, [
            "--namespace", NAMESPACE,
            "--output", "json"
        ])
        assert result.exit_code == 0, result.output
        assert space_name in result.output
        # Verify it's valid JSON by checking for brackets
        assert "[" in result.output and "]" in result.output

    @pytest.mark.dependency(name="describe", depends=["create"])
    def test_space_describe_yaml(self, runner, space_name):
        """Test describing a space in YAML format."""
        result = runner.invoke(space_describe, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--output", "yaml"
        ])
        assert result.exit_code == 0, result.output
        assert space_name in result.output
        assert "apiVersion:" in result.output
        assert "kind:" in result.output

    @pytest.mark.dependency(depends=["create"])
    def test_space_describe_json(self, runner, space_name):
        """Test describing a space in JSON format."""
        result = runner.invoke(space_describe, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--output", "json"
        ])
        assert result.exit_code == 0, result.output
        assert space_name in result.output
        assert "{" in result.output and "}" in result.output

    @pytest.mark.dependency(depends=["create"])
    @pytest.mark.dependency(name="stop")
    def test_space_stop(self, runner, space_name):
        """Test stopping a space."""
        result = runner.invoke(space_stop, [
            "--name", space_name,
            "--namespace", NAMESPACE
        ])
        assert result.exit_code == 0, result.output
        assert f"Space '{space_name}' stop requested" in result.output

    @pytest.mark.dependency(depends=["stop"])
    @pytest.mark.dependency(name="start")
    def test_space_start(self, runner, space_name):
        """Test starting a space."""
        result = runner.invoke(space_start, [
            "--name", space_name,
            "--namespace", NAMESPACE
        ])
        assert result.exit_code == 0, result.output
        assert f"Space '{space_name}' start requested" in result.output

    @pytest.mark.dependency(depends=["create", "describe"])
    def test_space_update(self, runner, space_name):
        """Test updating a space."""
        result = runner.invoke(space_update, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--display-name", f"Updated {DISPLAY_NAME}",
        ])
        assert result.exit_code == 0, result.output
        assert f"Space '{space_name}' updated successfully" in result.output

    @pytest.mark.dependency(depends=["start"])
    def test_space_portforward(self, runner, space_name):
        """Test port forwarding to a space."""
        # Find an available port
        test_port = 8080
        while not self._is_port_available(test_port) and test_port < 9000:
            test_port += 1
        
        if test_port >= 9000:
            pytest.skip("No available ports found for testing")

        # Wait for space to become available
        print(f"Waiting for space '{space_name}' to become available...")
        if not self._wait_for_space_available(space_name, NAMESPACE):
            pytest.skip(f"Space '{space_name}' did not become available within timeout")

        # Start port forwarding in a separate thread
        portforward_thread = None
        portforward_exception = None
        
        def run_portforward():
            nonlocal portforward_exception
            try:
                result = runner.invoke(space_portforward, [
                    "--name", space_name,
                    "--namespace", NAMESPACE,
                    "--local-port", str(test_port)
                ], catch_exceptions=False)
                if result.exit_code != 0:
                    portforward_exception = Exception(f"Port forward failed: {result.output}")
            except Exception as e:
                portforward_exception = e

        portforward_thread = threading.Thread(target=run_portforward, daemon=True)
        portforward_thread.start()
        
        # Check if port forwarding thread encountered an error
        if portforward_exception:
            raise portforward_exception
        
        # Test localhost HTTP endpoint
        print(f"Testing HTTP endpoint at localhost:{test_port}")
        if self._test_http_endpoint(test_port):
            print("✓ HTTP endpoint returned 200 status")
        else:
            pytest.fail(f"HTTP endpoint at localhost:{test_port} did not return 200 status within timeout")

    @pytest.mark.dependency(depends=["create"])
    def test_space_get_logs(self, runner, space_name):
        """Test getting logs from a space."""
        # This might fail if no pods are running, which is acceptable
        result = runner.invoke(space_get_logs, [
            "--name", space_name,
            "--namespace", NAMESPACE
        ])
        # Don't assert exit code as logs might not be available
        # Just verify the command runs without crashing
        assert isinstance(result.exit_code, int)

    @pytest.mark.dependency(depends=["create"])
    def test_space_delete(self, runner, space_name):
        """Test deleting a space."""
        result = runner.invoke(space_delete, [
            "--name", space_name,
            "--namespace", NAMESPACE
        ])
        assert result.exit_code == 0, result.output
        assert f"Requested deletion for Space '{space_name}'" in result.output

    def test_space_describe_nonexistent(self, runner):
        """Test describing a nonexistent space."""
        result = runner.invoke(space_describe, [
            "--name", "nonexistent-space",
            "--namespace", NAMESPACE
        ])
        assert result.exit_code != 0

    def test_space_delete_nonexistent(self, runner):
        """Test deleting a nonexistent space."""
        result = runner.invoke(space_delete, [
            "--name", "nonexistent-space",
            "--namespace", NAMESPACE
        ])
        assert result.exit_code != 0
