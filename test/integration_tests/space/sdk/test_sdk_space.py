import time
import pytest
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from hyperpod_space_template.v1_0.model import SpaceConfig, ResourceRequirements
from test.integration_tests.utils import get_time_str

# --------- Config ---------
NAMESPACE = "default"
SPACE_NAME = "space-sdk-integration-test-" + get_time_str()
DISPLAY_NAME = f"Space SDK Integration Test {get_time_str()}"

# Basic configuration for testing
TIMEOUT_MINUTES = 2
POLL_INTERVAL_SECONDS = 13

@pytest.fixture(scope="module")
def space_config():
    """Create a basic space configuration for testing."""
    return SpaceConfig(
        name=SPACE_NAME,
        display_name=DISPLAY_NAME,
        namespace=NAMESPACE,
    )

@pytest.fixture(scope="module")
def space_obj(space_config):
    """Create an HPSpace instance for testing."""
    return HPSpace(config=space_config)

@pytest.mark.dependency(name="create")
def test_create_space(space_obj):
    """Test creating a space."""
    space_obj.create()
    assert space_obj.config.name == SPACE_NAME

@pytest.mark.dependency(depends=["create"])
def test_list_spaces():
    """Test listing spaces."""
    spaces = HPSpace.list(namespace=NAMESPACE)
    names = [space.config.name for space in spaces]
    assert SPACE_NAME in names

@pytest.mark.dependency(name="get", depends=["create"])
def test_get_space():
    """Test getting a specific space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    assert space.config.name == SPACE_NAME
    assert space.config.display_name == DISPLAY_NAME

@pytest.mark.dependency(name="wait_until_running", depends=["create"])
def test_wait_until_running():
    """Poll until space reaches Running status."""
    print(f"[INFO] Waiting for space '{SPACE_NAME}' to be Running...")
    deadline = time.time() + (TIMEOUT_MINUTES * 60)
    poll_count = 0

    while time.time() < deadline:
        poll_count += 1
        print(f"[DEBUG] Poll #{poll_count}: Checking space status...")

        try:
            space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
            if space.status:
                conditions = {c['type']: c['status'] for c in space.status['conditions']}
                if conditions.get('Available', None) == "True":
                    print("[INFO] Space is Running.")
                    return
            else:
                print("[DEBUG] No status available yet")

        except Exception as e:
            print(f"[ERROR] Exception during polling: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)

    pytest.fail("[ERROR] Timed out waiting for space to be Running")

@pytest.mark.dependency(name="update", depends=["wait_until_running"])
def test_update_space():
    """Test updating space configuration."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    
    # Update resources
    new_resources = ResourceRequirements(
        requests={"cpu": "500m", "memory": "8Gi"},
        limits={"cpu": "800m", "memory": "8Gi"}
    )
    
    space.update(resources=new_resources)
    
    # Verify update
    updated_space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    assert updated_space.config.resources.requests["cpu"] == "500m"
    assert updated_space.config.resources.limits["cpu"] == "800m"

@pytest.mark.dependency(name="stop", depends=["update"])
def test_stop_space():
    """Test stopping a space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    space.stop()

    # Verify the desired status is updated
    updated_space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    assert updated_space.config.desired_status == "Stopped"

@pytest.mark.dependency(depends=["stop"])
def test_start_space():
    """Test starting a space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    space.start()
    
    # Verify the desired status is updated
    updated_space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    assert updated_space.config.desired_status == "Running"

@pytest.mark.dependency(depends=["create", "wait_until_running"])
def test_list_pods():
    """Test listing pods associated with the space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    pods = space.list_pods()
    # Pods may not exist immediately, so just verify the method works
    assert isinstance(pods, list)

@pytest.mark.dependency(depends=["create", "wait_until_running"])
def test_get_logs():
    """Test getting logs from space pods."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    
    # First check if there are any pods
    pods = space.list_pods()
    if pods:
        try:
            logs = space.get_logs(pod_name=pods[0])
            assert isinstance(logs, str)
        except Exception as e:
            # Logs might not be available immediately, which is acceptable
            print(f"[INFO] Logs not available yet: {e}")
    else:
        print("[INFO] No pods available for log retrieval")

@pytest.mark.skip(reason="Skipping space access test due to an operator setup issue")
@pytest.mark.dependency(depends=["create", "wait_until_running"])
def test_create_space_access():
    """Test creating space access for remote connection."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    access_info = space.create_space_access(connection_type="vscode-remote")
    assert "SpaceConnectionType" in access_info
    assert "SpaceConnectionUrl" in access_info
    assert access_info["SpaceConnectionType"] == "vscode-remote"

@pytest.mark.dependency(depends=["create"])
def test_delete_space():
    """Test deleting a space."""
    space = HPSpace.get(name=SPACE_NAME, namespace=NAMESPACE)
    space.delete()
    
    # Verify space is deleted by checking it's not in the list
    time.sleep(60)  # Give some time for deletion to propagate
    spaces = HPSpace.list(namespace=NAMESPACE)
    names = [space.config.name for space in spaces]
    assert SPACE_NAME not in names
