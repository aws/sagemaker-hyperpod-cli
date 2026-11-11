"""Every training replica set receives validation and quota allocation."""

from copy import deepcopy
from unittest.mock import patch

from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig
import pytest

from sagemaker.hyperpod.training import HyperPodPytorchJob, Resources


def make_multi_replica_job():
    chief = PyTorchJobConfig(
        job_name="multi-replica",
        image="pytorch:latest",
        instance_type="ml.g5.xlarge",
        accelerators=1,
    ).to_domain()
    worker = PyTorchJobConfig(
        job_name="worker",
        image="pytorch:latest",
        instance_type="ml.p4d.24xlarge",
        accelerators=4,
        replica_count=2,
    ).to_domain()
    chief.replicaSpecs[0].name = "chief"
    worker.replicaSpecs[0].name = "workers"
    chief.replicaSpecs.extend(worker.replicaSpecs)
    return chief


def test_all_replica_sets_receive_instance_specific_resources():
    job = make_multi_replica_job()
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    chief, workers = resolved.replicaSpecs
    chief_resources = chief.template.spec.containers[0].resources
    worker_resources = workers.template.spec.containers[0].resources

    assert int(chief_resources.requests["nvidia.com/gpu"]) == 1
    assert "vpc.amazonaws.com/efa" not in chief_resources.requests
    assert int(worker_resources.requests["nvidia.com/gpu"]) == 4
    assert int(worker_resources.limits["nvidia.com/gpu"]) == 4
    assert int(worker_resources.requests["vpc.amazonaws.com/efa"]) == 4
    assert int(worker_resources.limits["vpc.amazonaws.com/efa"]) == 4
    assert "accelerators" not in worker_resources.requests
    assert [replica.name for replica in resolved.replicaSpecs] == ["chief", "workers"]
    assert workers.replicas == 2


@pytest.mark.parametrize("unmanaged_index", [0, 1])
def test_replica_without_instance_type_does_not_skip_other_replicas(unmanaged_index):
    job = make_multi_replica_job()
    unmanaged = job.replicaSpecs[unmanaged_index]
    unmanaged.template.spec.nodeSelector = None
    unmanaged.template.spec.containers[0].resources.requests = {"cpu": "1"}
    unmanaged.template.spec.containers[0].resources.limits = {"cpu": "2"}
    original = deepcopy(unmanaged.model_dump())

    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    assert resolved.replicaSpecs[unmanaged_index].model_dump() == original
    managed = resolved.replicaSpecs[1 - unmanaged_index]
    resources = managed.template.spec.containers[0].resources
    assert "nvidia.com/gpu" in resources.requests
    assert "accelerators" not in resources.requests


@pytest.mark.parametrize("invalid", ["accelerator-capacity", "missing-instance-type"])
def test_later_invalid_replica_is_rejected_without_partial_mutation(invalid):
    job = make_multi_replica_job()
    worker = job.replicaSpecs[1]
    if invalid == "accelerator-capacity":
        resources = worker.template.spec.containers[0].resources
        resources.requests["accelerators"] = "9"
        resources.limits["accelerators"] = "9"
        expected_error = "exceeds instance capacity"
    else:
        worker.template.spec.nodeSelector = None
        expected_error = "instance_type is required"
    original = deepcopy(job.model_dump())

    with pytest.raises(ValueError, match=expected_error):
        HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    assert job.model_dump() == original


@pytest.mark.parametrize("index", [0, 1])
@pytest.mark.parametrize(
    "resources",
    [
        None,
        Resources(),
        Resources(requests={"cpu": "1"}),
        Resources(limits={"memory": "8Gi"}),
    ],
)
def test_unmanaged_replica_with_optional_resources_preserves_other_allocations(
    index, resources
):
    job = make_multi_replica_job()
    unmanaged = job.replicaSpecs[index]
    unmanaged.template.spec.nodeSelector = None
    unmanaged.template.spec.containers[0].resources = resources
    original = deepcopy(unmanaged.model_dump())
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    assert resolved.replicaSpecs[index].model_dump() == original
    managed_resources = (
        resolved.replicaSpecs[1 - index].template.spec.containers[0].resources
    )
    assert "nvidia.com/gpu" in managed_resources.requests
    assert "accelerators" not in managed_resources.requests


@pytest.mark.parametrize(
    "resources",
    [
        None,
        Resources(),
        Resources(requests={"cpu": "1"}),
        Resources(limits={"memory": "8Gi"}),
    ],
)
def test_managed_replica_with_optional_resources_is_allocated(resources):
    job = make_multi_replica_job()
    job.replicaSpecs[1].template.spec.containers[0].resources = resources
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    chief_resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    worker_resources = resolved.replicaSpecs[1].template.spec.containers[0].resources
    assert int(chief_resources.requests["nvidia.com/gpu"]) == 1
    assert "cpu" in worker_resources.requests
    assert "memory" in worker_resources.requests
    assert "accelerators" not in worker_resources.requests


@patch("sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request")
@patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
@patch.object(HyperPodPytorchJob, "verify_kube_config")
def test_create_serializes_allocations_with_optional_worker_resources(
    verify_config, api, telemetry
):
    job = make_multi_replica_job()
    job.metadata.namespace = "default"
    worker = job.replicaSpecs[1]
    worker.template.spec.nodeSelector = None
    worker.template.spec.containers[0].resources = None
    job.create()
    body = api.return_value.create_namespaced_custom_object.call_args.kwargs["body"]
    chief, worker_payload = body["spec"]["replicaSpecs"]
    requests = chief["template"]["spec"]["containers"][0]["resources"]["requests"]
    assert int(requests["nvidia.com/gpu"]) == 1
    assert "cpu" in requests and "memory" in requests
    assert "resources" not in worker_payload["template"]["spec"]["containers"][0]


@patch("sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request")
@patch("sagemaker.hyperpod.training.hyperpod_pytorch_job.client.CustomObjectsApi")
@patch.object(HyperPodPytorchJob, "verify_kube_config")
def test_create_rejects_invalid_later_replica_before_api_submission(
    verify_config, api, telemetry
):
    job = make_multi_replica_job()
    job.metadata.namespace = "default"
    job.replicaSpecs[1].template.spec.nodeSelector = None
    with pytest.raises(ValueError, match="instance_type is required"):
        job.create()
    api.assert_not_called()


@pytest.mark.parametrize("replicas", [None, []])
def test_missing_replica_list_remains_unchanged(replicas):
    job = make_multi_replica_job()
    job.replicaSpecs = replicas
    assert HyperPodPytorchJob.allocate_quotas_if_applicable(job) is job
    assert job.replicaSpecs == replicas


def test_later_replica_without_template_fails_without_partial_mutation():
    job = make_multi_replica_job()
    job.replicaSpecs[1].template = None
    original = deepcopy(job.model_dump())
    with pytest.raises(ValueError, match="No containers found"):
        HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    assert job.model_dump() == original
