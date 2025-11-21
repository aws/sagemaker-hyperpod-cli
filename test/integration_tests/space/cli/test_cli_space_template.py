import pytest
import tempfile
import os
import yaml
import json
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.space_template import (
    space_template_create, space_template_list, space_template_describe,
    space_template_delete, space_template_update
)
from test.integration_tests.utils import get_time_str

# --------- Test Configuration ---------
NAMESPACE = "default"
TEMPLATE_NAME = "space-template-cli-integ-test" + get_time_str()

# Template configuration aligned with template.yaml
TEMPLATE_CONFIG = {
    "apiVersion": "workspace.jupyter.org/v1alpha1",
    "kind": "WorkspaceTemplate",
    "metadata": {
        "name": TEMPLATE_NAME,
        "namespace": NAMESPACE
    },
    "spec": {
        "displayName": f"Space Template CLI Integ Test {get_time_str()}",
        "description": "Integration test template for Space Template CLI",
        "defaultImage": "jk8s-application-jupyter-uv:latest",
        "allowedImages": [
            "jk8s-application-jupyter-uv:latest"
        ],
        "defaultResources": {
            "requests": {
                "cpu": "200m",
                "memory": "256Mi"
            },
            "limits": {
                "cpu": "500m",
                "memory": "512Mi"
            }
        },
        "resourceBounds": {
            "cpu": {
                "min": "100m",
                "max": "2"
            },
            "memory": {
                "min": "128Mi",
                "max": "4Gi"
            },
            "gpu": {
                "min": "0",
                "max": "1"
            }
        },
        "primaryStorage": {
            "defaultSize": "1Gi",
            "minSize": "100Mi",
            "maxSize": "20Gi"
        },
        "appType": "jupyter"
    }
}

@pytest.fixture(scope="module")
def runner():
    return CliRunner()

@pytest.fixture(scope="module")
def template_yaml_file():
    """Create a temporary YAML file with template configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(TEMPLATE_CONFIG, f)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)

@pytest.fixture(scope="module")
def template_name():
    return TEMPLATE_NAME

class TestSpaceTemplateCLI:
    """Integration tests for HyperPod Space Template CLI commands."""

    @pytest.mark.dependency(name="create")
    def test_space_template_create(self, runner, template_yaml_file, template_name):
        """Test creating a space template via CLI."""
        result = runner.invoke(space_template_create, [
            "--file", template_yaml_file
        ])
        assert result.exit_code == 0, result.output
        assert f"Space template '{template_name}' in namespace '{NAMESPACE}' created successfully" in result.output

    @pytest.mark.dependency(depends=["create"])
    def test_space_template_list_table(self, runner, template_name):
        """Test listing space templates in table format."""
        result = runner.invoke(space_template_list, [
            "--namespace", NAMESPACE,
            "--output", "table"
        ])
        assert result.exit_code == 0, result.output
        assert template_name in result.output
        assert "NAMESPACE" in result.output
        assert "NAME" in result.output
        assert "DISPLAY_NAME" in result.output
        assert "DEFAULT_IMAGE" in result.output

    @pytest.mark.dependency(depends=["create"])
    def test_space_template_list_json(self, runner, template_name):
        """Test listing space templates in JSON format."""
        result = runner.invoke(space_template_list, [
            "--namespace", NAMESPACE,
            "--output", "json"
        ])
        assert result.exit_code == 0, result.output
        assert template_name in result.output
        
        # Verify it's valid JSON
        try:
            templates_data = json.loads(result.output)
            assert isinstance(templates_data, list)
            
            # Find our template in the list
            our_template = next((t for t in templates_data if t.get("metadata", {}).get("name") == template_name), None)
            assert our_template is not None
            
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON output from space template list command")

    @pytest.mark.dependency(name="describe", depends=["create"])
    def test_space_template_describe_yaml(self, runner, template_name):
        """Test describing a space template in YAML format."""
        result = runner.invoke(space_template_describe, [
            "--name", template_name,
            "--namespace", NAMESPACE,
            "--output", "yaml"
        ])
        assert result.exit_code == 0, result.output
        assert template_name in result.output
        assert "apiVersion:" in result.output
        assert "kind:" in result.output
        
        # Verify YAML structure
        try:
            template_data = yaml.safe_load(result.output)
            assert template_data["metadata"]["name"] == template_name
            assert template_data["metadata"]["namespace"] == NAMESPACE
            
        except yaml.YAMLError:
            pytest.fail("Invalid YAML output from space template describe command")

    @pytest.mark.dependency(depends=["create"])
    def test_space_template_describe_json(self, runner, template_name):
        """Test describing a space template in JSON format."""
        result = runner.invoke(space_template_describe, [
            "--name", template_name,
            "--namespace", NAMESPACE,
            "--output", "json"
        ])
        assert result.exit_code == 0, result.output
        assert template_name in result.output
        
        # Verify JSON structure
        try:
            template_data = json.loads(result.output)
            assert template_data["metadata"]["name"] == template_name
            assert template_data["metadata"]["namespace"] == NAMESPACE
            assert template_data["kind"] == "WorkspaceTemplate"
            
        except json.JSONDecodeError:
            pytest.fail("Invalid JSON output from space template describe command")

    @pytest.mark.dependency(depends=["create", "describe"])
    def test_space_template_update(self, runner, template_name):
        """Test updating a space template."""
        # Create updated config
        updated_config = TEMPLATE_CONFIG.copy()
        updated_config["spec"]["description"] = "Updated CLI integration test template"
        updated_config["spec"]["defaultResources"]["requests"]["cpu"] = "300m"
        
        # Create temporary file with updated config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(updated_config, f)
            temp_file = f.name
        
        try:
            result = runner.invoke(space_template_update, [
                "--name", template_name,
                "--namespace", NAMESPACE,
                "--file", temp_file
            ])
            assert result.exit_code == 0, result.output
            assert f"Space template '{template_name}' in namespace '{NAMESPACE}' updated successfully" in result.output
            
            # Verify update by describing the template
            describe_result = runner.invoke(space_template_describe, [
                "--name", template_name,
                "--namespace", NAMESPACE,
                "--output", "json"
            ])
            assert describe_result.exit_code == 0
            
            try:
                template_data = json.loads(describe_result.output)
                assert template_data["spec"]["description"] == "Updated CLI integration test template"
                assert template_data["spec"]["defaultResources"]["requests"]["cpu"] == "300m"
            except json.JSONDecodeError:
                pytest.fail("Invalid JSON output from space template describe after update")
                
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.dependency(depends=["create"])
    def test_space_template_delete(self, runner, template_name):
        """Test deleting a space template."""
        result = runner.invoke(space_template_delete, [
            "--name", template_name,
            "--namespace", NAMESPACE
        ])
        assert result.exit_code == 0, result.output
        assert f"Requested deletion for Space template '{template_name}' in namespace '{NAMESPACE}'" in result.output

    def test_space_template_list_empty_namespace(self, runner):
        """Test listing space templates in an empty namespace."""
        result = runner.invoke(space_template_list, [
            "--namespace", "nonexistent-namespace",
            "--output", "table"
        ])
        assert result.exit_code == 0, result.output
        assert "No space templates found" in result.output

    def test_space_template_describe_nonexistent(self, runner):
        """Test describing a nonexistent space template."""
        result = runner.invoke(space_template_describe, [
            "--name", "nonexistent-template",
            "--namespace", NAMESPACE
        ])
        assert result.exit_code != 0

    def test_space_template_delete_nonexistent(self, runner):
        """Test deleting a nonexistent space template."""
        result = runner.invoke(space_template_delete, [
            "--name", "nonexistent-template",
            "--namespace", NAMESPACE
        ])
        assert result.exit_code != 0
