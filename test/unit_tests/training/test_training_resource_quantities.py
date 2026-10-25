"""Resource quantities retain their meaning through public job allocation."""

from copy import deepcopy

from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig
from kubernetes.utils.quantity import parse_quantity
import pytest

from sagemaker.hyperpod.training import HyperPodPytorchJob


def make_job(requests, limits):
    job = PyTorchJobConfig(
        job_name="resource-quantities",
        image="pytorch:latest",
        instance_type="ml.g5.xlarge",
        vcpu=1.0,
        memory=1.0,
    ).to_domain()
    resources = job.replicaSpecs[0].template.spec.containers[0].resources
    resources.requests = requests
    resources.limits = limits
    return job


@pytest.mark.parametrize(
    "cpu,memory,cpu_limit,memory_limit,expected_memory,expected_limit",
    [
        ("0.5", "1Gi", "1", "2Gi", 2**30, 2**31),
        ("500m", "1Gi", "1000m", "2Gi", 2**30, 2**31),
        ("0.5", "1024Mi", "1", "2048Mi", 2**30, 2**31),
        ("500m", "1024Mi", "1000m", "2048Mi", 2**30, 2**31),
        ("0.5", "1G", "1", "2G", 10**9, 2 * 10**9),
        ("0.5", "1e-5", "1", "2e-5", 1e-5 * 2**30, 2e-5 * 2**30),
        ("0.5", 1, "1", 2, 2**30, 2**31),
        ("0.5", "1", "1", "2", 2**30, 2**31),
        ("0.5", "1Ki", "1", "2Ki", 1024, 2048),
        ("0.5", "1m", "1", "2m", 0.001, 0.002),
    ],
)
def test_standard_quantities_preserved(
    cpu, memory, cpu_limit, memory_limit, expected_memory, expected_limit
):
    job = make_job(
        {"cpu": cpu, "memory": memory},
        {"cpu": cpu_limit, "memory": memory_limit},
    )
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    assert parse_quantity(resources.requests["cpu"]) == parse_quantity("0.5")
    assert parse_quantity(resources.limits["cpu"]) == 1
    assert float(parse_quantity(resources.requests["memory"])) == pytest.approx(
        expected_memory
    )
    assert float(parse_quantity(resources.limits["memory"])) == pytest.approx(
        expected_limit
    )


@pytest.mark.parametrize("section", ["requests", "limits"])
@pytest.mark.parametrize("resource", ["cpu", "memory"])
@pytest.mark.parametrize(
    "invalid", ["NaN", "Infinity", "-1", "1GiB", "1e10000", "1e999999999G"]
)
def test_invalid_quantity_fails_before_mutating_job(section, resource, invalid):
    job = make_job(
        {"cpu": "0.5", "memory": "1Gi"},
        {"cpu": "1", "memory": "2Gi"},
    )
    resources = job.replicaSpecs[0].template.spec.containers[0].resources
    getattr(resources, section)[resource] = invalid
    original = deepcopy(job.model_dump())
    with pytest.raises(ValueError, match=f"Invalid {resource} quantity"):
        HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    assert job.model_dump() == original


def test_vcpu_alias_accepts_millicores():
    job = make_job(
        {"vcpu": "500m", "memory": "1Gi"},
        {"vcpu": "1000m", "memory": "2Gi"},
    )
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    assert parse_quantity(resources.requests["cpu"]) == parse_quantity("0.5")
    assert parse_quantity(resources.limits["cpu"]) == 1


@pytest.mark.parametrize("memory,memory_limit", [(64.0, 128.0), (1e-5, 2e-5)])
def test_installed_template_memory_stays_in_gib(memory, memory_limit):
    job = PyTorchJobConfig(
        job_name="template-memory",
        image="pytorch:latest",
        instance_type="ml.p4d.24xlarge",
        vcpu=16.0,
        memory=memory,
        memory_limit=memory_limit,
    ).to_domain()
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    assert float(parse_quantity(resources.requests["memory"])) == pytest.approx(
        memory * 2**30
    )
    assert float(parse_quantity(resources.limits["memory"])) == pytest.approx(
        memory_limit * 2**30
    )
    assert "e" not in resources.requests["memory"].lower()
    assert "e" not in resources.limits["memory"].lower()


def test_memory_only_quantity_preserves_derived_cpu_exponent():
    job = make_job({"memory": "1Ki"}, {})
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    expected_cpu = 1024 / (16 * 2**30) * 4
    assert float(parse_quantity(resources.requests["cpu"])) == pytest.approx(
        expected_cpu
    )
    assert float(parse_quantity(resources.requests["memory"])) == pytest.approx(1024)
    assert float(parse_quantity(resources.limits["memory"])) == pytest.approx(1024)


def test_numeric_zero_preserves_existing_default_allocation():
    job = make_job({"cpu": 0, "memory": 0}, {"memory": 0})
    resolved = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
    resources = resolved.replicaSpecs[0].template.spec.containers[0].resources
    assert float(parse_quantity(resources.requests["cpu"])) == 3
    assert float(parse_quantity(resources.requests["memory"])) == 11 * 2**30
    assert resources.limits["memory"] == resources.requests["memory"]
