import json
import time
import pytest
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.space import (
    space_create, space_describe, space_delete, space_update,
)
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "default"
SPACE_NAME = "space-cli-v1-1-integ-" + get_time_str()
DISPLAY_NAME = f"Space CLI V1.1 Integ Test {get_time_str()}"


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


@pytest.fixture(scope="module")
def space_name():
    return SPACE_NAME


class TestSpaceCLIv1_1:
    """Integration tests for HyperPod Space CLI v1.1 options."""

    @pytest.mark.dependency(name="create_v1_1_cli")
    def test_space_create_with_v1_1_options(self, runner, space_name):
        """Test creating a space with v1.1 CLI options."""
        result = runner.invoke(space_create, [
            "--name", space_name,
            "--display-name", DISPLAY_NAME,
            "--namespace", NAMESPACE,
            "--queue-name", "default-queue",
            "--priority", "high-priority",
            "--access-type", "Public",
            "--env", json.dumps([{"name": "MY_VAR", "value": "my_value"}]),
            "--pod-security-context", json.dumps({"runAsUser": 1000}),
            "--container-security-context", json.dumps({"allowPrivilegeEscalation": False}),
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert f"Space '{space_name}' created successfully" in result.output

    @pytest.mark.dependency(depends=["create_v1_1_cli"])
    def test_describe_shows_v1_1_fields(self, runner, space_name):
        """Test that describe output contains v1.1 fields."""
        result = runner.invoke(space_describe, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--output", "json",
        ])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)

        # Verify kueue labels
        labels = data.get("metadata", {}).get("labels", {})
        assert labels.get("kueue.x-k8s.io/queue-name") == "default-queue"
        assert labels.get("kueue.x-k8s.io/priority-class") == "high-priority"

        # Verify spec fields
        spec = data.get("spec", {})
        assert spec.get("accessType") == "Public"
        assert spec.get("env") == [{"name": "MY_VAR", "value": "my_value"}]
        assert spec.get("podSecurityContext") == {"runAsUser": 1000}
        assert spec.get("containerSecurityContext") == {"allowPrivilegeEscalation": False}

    @pytest.mark.dependency(depends=["create_v1_1_cli"])
    def test_update_env_via_cli(self, runner, space_name):
        """Test updating env via CLI on a v1.1 space."""
        new_env = json.dumps([{"name": "MY_VAR", "value": "updated"}, {"name": "EXTRA", "value": "val"}])
        result = runner.invoke(space_update, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--env", new_env,
        ])
        assert result.exit_code == 0, f"Failed: {result.output}"
        assert f"Space '{space_name}' updated successfully" in result.output

        # Verify update persisted
        result = runner.invoke(space_describe, [
            "--name", space_name,
            "--namespace", NAMESPACE,
            "--output", "json",
        ])
        data = json.loads(result.output)
        env = data.get("spec", {}).get("env", [])
        assert {"name": "MY_VAR", "value": "updated"} in env
        assert {"name": "EXTRA", "value": "val"} in env

    @pytest.mark.dependency(depends=["create_v1_1_cli"])
    def test_delete_v1_1_space(self, runner, space_name):
        """Test deleting the v1.1 space."""
        result = runner.invoke(space_delete, [
            "--name", space_name,
            "--namespace", NAMESPACE,
        ])
        assert result.exit_code == 0, result.output
        assert f"Requested deletion for Space '{space_name}'" in result.output
