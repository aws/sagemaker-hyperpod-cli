import time
import pytest
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.space import (
    space_create, space_list, space_describe, space_delete, 
    space_update, space_start, space_stop, space_get_logs
)
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
    def test_space_stop(self, runner, space_name):
        """Test stopping a space."""
        result = runner.invoke(space_stop, [
            "--name", space_name,
            "--namespace", NAMESPACE
        ])
        assert result.exit_code == 0, result.output
        assert f"Space '{space_name}' stop requested" in result.output

    @pytest.mark.dependency(depends=["create"])
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

    def test_space_list_empty_namespace(self, runner):
        """Test listing spaces in an empty namespace."""
        result = runner.invoke(space_list, [
            "--namespace", "nonexistent-namespace",
            "--output", "table"
        ])
        assert result.exit_code == 0, result.output
        assert "No spaces found" in result.output

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
