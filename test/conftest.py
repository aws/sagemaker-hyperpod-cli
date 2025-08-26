import subprocess
import sys
import uuid
import pytest
import json
from test.integration_tests.utils import execute_command
from sagemaker.hyperpod.training import (
    HyperPodPytorchJob,
    Containers,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
)
from sagemaker.hyperpod.common.config import Metadata

@pytest.fixture(scope="session", autouse=True)
def ensure_template_package_installed():
    """Ensure template package is installed globally for CLI usage."""
    try:
        import hyperpod_cluster_stack_template
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "./hyperpod-cluster-stack-template"])
            print("✓ hyperpod-cluster-stack-template installed for CLI usage")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install template package for CLI: {e}")
            raise

def pytest_configure(config):
    """Install hyperpod-cluster-stack-template from local directory before test collection."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "./hyperpod-cluster-stack-template"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ hyperpod-cluster-stack-template installed successfully from local directory")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install hyperpod-cluster-stack-template from ./hyperpod-cluster-stack-template: {e}")
        print("Make sure the hyperpod-cluster-stack-template directory exists in the project root")
        raise

@pytest.fixture(scope="class")
def test_job_name():
    """Generate a unique job name for testing."""
    return f"test-pytorch-job-{str(uuid.uuid4())[:8]}"

@pytest.fixture(scope="class")
def image_uri():
    """Return a standard PyTorch image URI for testing."""
    return "448049793756.dkr.ecr.us-west-2.amazonaws.com/ptjob:mnist"

@pytest.fixture(scope="class")
def cluster_name():
    """Fixture to list clusters once and return the first cluster name."""
    result = execute_command(["hyp", "list-cluster"])
    assert result.returncode == 0

    try:
        json_start = result.stdout.index('[')
        json_text = result.stdout[json_start:]
        clusters = json.loads(json_text)
    except Exception as e:
        raise AssertionError(f"Failed to parse cluster list JSON: {e}\nRaw Output:\n{result.stdout}")

    assert clusters, "No clusters found in list-cluster output"
    return clusters[-1]["Cluster"]

@pytest.fixture(scope="class")
def pytorch_job(test_job_name, image_uri):
    """Create a HyperPodPytorchJob instance for testing."""
    nproc_per_node="1"
    replica_specs=[
        ReplicaSpec(
            name="pod",
            template=Template(
                spec=Spec(
                    containers=[
                        Containers(
                            name="container-name",
                            image=image_uri,
                            image_pull_policy="Always",
                            resources=Resources(
                                requests={"nvidia.com/gpu": "0"},
                                limits={"nvidia.com/gpu": "0"},
                            ),
                            # command=[]
                        )
                    ]
                )
            ),
        )
    ]
    run_policy=RunPolicy(clean_pod_policy="None")

    pytorch_job = HyperPodPytorchJob(
        metadata=Metadata(name=test_job_name),
        nproc_per_node=nproc_per_node,
        replica_specs=replica_specs,
        run_policy=run_policy,
    )

    return pytorch_job

