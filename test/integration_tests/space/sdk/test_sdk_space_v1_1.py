import time
import pytest
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from hyperpod_space_template.v1_1.model import SpaceConfig, ResourceRequirements, AccessStrategyRef
from test.integration_tests.utils import get_time_str

# --------- Config ---------
NAMESPACE = "default"
SPACE_NAME = "space-sdk-v1-1-integ-" + get_time_str()
DISPLAY_NAME = f"Space SDK V1.1 Integration Test {get_time_str()}"

TIMEOUT_MINUTES = 2
POLL_INTERVAL_SECONDS = 13


@pytest.fixture(scope="module")
def space_config():
    """Create a v1.1 space configuration with new fields."""
    return SpaceConfig(
        name=SPACE_NAME,
        display_name=DISPLAY_NAME,
        namespace=NAMESPACE,
        queue_name="default-queue",
        priority="high-priority",
        env=[{"name": "TEST_VAR", "value": "test_value"}],
        access_type="Public",
        pod_security_context={"runAsUser": 1000},
        container_security_context={"allowPrivilegeEscalation": False},
    )


@pytest.fixture(scope="module")
def space_obj(space_config):
    """Create an HPSpace instance for testing."""
    return HPSpace(config=space_config)


@pytest.mark.dependency(name="create_v1_1")
def test_create_space(space_obj):
    """Test creating a space with v1.1 fields."""
    space_obj.create()
    assert space_obj.config.name == SPACE_NAME


@pytest.mark.dependency(depends=["create_v1_1"])
def test_get_space_has_v1_1_fields():
    """Test that v1.1 fields are persisted and retrievable."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    assert space.config.name == SPACE_NAME
    assert space.config.display_name == DISPLAY_NAME

    # Verify kueue labels in raw resource
    labels = space.raw_resource.get("metadata", {}).get("labels", {})
    assert labels.get("kueue.x-k8s.io/queue-name") == "default-queue"
    assert labels.get("kueue.x-k8s.io/priority-class") == "high-priority"

    # Verify spec fields
    spec = space.raw_resource.get("spec", {})
    assert spec.get("accessType") == "Public"
    assert spec.get("env") == [{"name": "TEST_VAR", "value": "test_value"}]
    assert spec.get("podSecurityContext") == {"runAsUser": 1000}
    assert spec.get("containerSecurityContext") == {"allowPrivilegeEscalation": False}


@pytest.mark.dependency(depends=["create_v1_1"])
def test_list_includes_v1_1_space():
    """Test that listing spaces includes the v1.1 space."""
    spaces = HPSpace.list(namespace=NAMESPACE)
    names = [s.config.name for s in spaces]
    assert SPACE_NAME in names


@pytest.mark.dependency(depends=["create_v1_1"])
def test_update_env():
    """Test updating env field on a v1.1 space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    space.update(env=[{"name": "TEST_VAR", "value": "updated"}, {"name": "NEW_VAR", "value": "new"}])

    updated = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    spec = updated.raw_resource.get("spec", {})
    assert {"name": "TEST_VAR", "value": "updated"} in spec.get("env", [])
    assert {"name": "NEW_VAR", "value": "new"} in spec.get("env", [])


@pytest.mark.dependency(depends=["create_v1_1"])
def test_delete_space():
    """Test deleting the v1.1 space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    space.delete()

    time.sleep(60)
    spaces = HPSpace.list(namespace=NAMESPACE)
    names = [s.config.name for s in spaces]
    assert SPACE_NAME not in names
