import uuid
import pytest
import json
from test.integration_tests.utils import execute_command
from sagemaker.hyperpod.training import (
    HyperPodPytorchJob,
    Container,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
)
from sagemaker.hyperpod.common.config import Metadata

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
                        Container(
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

