import pytest
import tempfile
import os
import yaml
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate
from test.integration_tests.utils import get_time_str

# --------- Config ---------
NAMESPACE = "default"
TEMPLATE_NAME = "space-template-sdk-integ-test-" + get_time_str()

# Sample template configuration aligned with template.yaml
TEMPLATE_CONFIG = {
    "apiVersion": "workspace.jupyter.org/v1alpha1",
    "kind": "WorkspaceTemplate",
    "metadata": {
        "name": TEMPLATE_NAME,
        "namespace": NAMESPACE
    },
    "spec": {
        "displayName": f"Space Template SDK Integ Test {get_time_str()}",
        "description": "Integration test template for Space Template SDK",
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
def template_obj_from_file(template_yaml_file):
    """Create HPSpaceTemplate from YAML file."""
    return HPSpaceTemplate(file_path=template_yaml_file)

@pytest.fixture(scope="module")
def template_obj_from_dict():
    """Create HPSpaceTemplate from dictionary."""
    return HPSpaceTemplate(config_data=TEMPLATE_CONFIG)

class TestHPSpaceTemplate:
    """Integration tests for HyperPod Space Template SDK."""

    @pytest.mark.dependency(name="create")
    def test_create_template(self, template_obj_from_dict):
        """Test creating a space template."""
        template_obj_from_dict.create()
        assert template_obj_from_dict.name == TEMPLATE_NAME

    @pytest.mark.dependency(depends=["create"])
    def test_list_templates(self):
        """Test listing space templates."""
        templates = HPSpaceTemplate.list(namespace=NAMESPACE)
        names = [template.name for template in templates]
        assert TEMPLATE_NAME in names

    @pytest.mark.dependency(name="get", depends=["create"])
    def test_get_template(self):
        """Test getting a specific space template."""
        template = HPSpaceTemplate.get(name=TEMPLATE_NAME, namespace=NAMESPACE)
        assert template.name == TEMPLATE_NAME
        assert template.namespace == NAMESPACE
        assert template.config_data["spec"]["defaultImage"] == "jk8s-application-jupyter-uv:latest"

    @pytest.mark.dependency(depends=["create", "get"])
    def test_update_template(self):
        """Test updating a space template."""
        # Create updated config
        updated_config = TEMPLATE_CONFIG.copy()
        updated_config["spec"]["description"] = "Updated integration test template"
        updated_config["spec"]["defaultResources"]["requests"]["cpu"] = "300m"
        
        # Create temporary file with updated config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(updated_config, f)
            temp_file = f.name
        
        try:
            template = HPSpaceTemplate.get(name=TEMPLATE_NAME, namespace=NAMESPACE)
            template.update(file_path=temp_file)
            
            # Verify update
            updated_template = HPSpaceTemplate.get(name=TEMPLATE_NAME, namespace=NAMESPACE)
            assert updated_template.config_data["spec"]["description"] == "Updated integration test template"
            assert updated_template.config_data["spec"]["defaultResources"]["requests"]["cpu"] == "300m"
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.dependency(depends=["create"])
    def test_delete_template(self):
        """Test deleting a space template."""
        template = HPSpaceTemplate.get(name=TEMPLATE_NAME, namespace=NAMESPACE)
        template.delete()
        
        # Verify template is deleted
        templates = HPSpaceTemplate.list(namespace=NAMESPACE)
        names = [template.name for template in templates]
        assert TEMPLATE_NAME not in names
