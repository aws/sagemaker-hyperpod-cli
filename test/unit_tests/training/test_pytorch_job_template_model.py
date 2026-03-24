import unittest
from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig
from hyperpod_pytorch_job_template.v1_0.model import PyTorchJobConfig as PyTorchJobConfigV1_0
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob


class TestResourceAllocation(unittest.TestCase):
    """Test resource allocation through the full pipeline (to_domain + allocate_quotas_if_applicable).

    These tests verify that config fields are correctly resolved into k8s resource keys
    (e.g. 'accelerators' -> 'nvidia.com/gpu') and that EFA is auto-populated from instance constants.
    """

    def _resolve(self, **kwargs):
        """Helper: create config, convert to domain, and run quota allocation."""
        config = PyTorchJobConfig(image="pytorch:latest", **kwargs)
        job = config.to_domain()
        return HyperPodPytorchJob.allocate_quotas_if_applicable(job)

    def _get_resources(self, job):
        container = job.replicaSpecs[0].template.spec.containers[0]
        return container.resources.requests, container.resources.limits

    def test_single_node_gpu_job(self):
        """Single-node GPU job gets resolved accelerator key and no EFA (g5.xlarge has 0 EFA)."""
        job = self._resolve(job_name="test-single", accelerators=1, instance_type="ml.g5.xlarge")
        requests, limits = self._get_resources(job)

        self.assertIn("nvidia.com/gpu", requests)
        self.assertNotIn("vpc.amazonaws.com/efa", requests)

    def test_multi_node_gpu_job_with_efa(self):
        """Multi-node GPU job on EFA-capable instance gets auto-populated EFA from constants."""
        job = self._resolve(job_name="test-multi", accelerators=8, instance_type="ml.p4d.24xlarge")
        requests, limits = self._get_resources(job)

        self.assertEqual(int(requests["nvidia.com/gpu"]), 8)
        self.assertIn("vpc.amazonaws.com/efa", requests)
        self.assertEqual(int(requests["vpc.amazonaws.com/efa"]), 4)  # p4d has 4 EFA interfaces

    def test_user_specified_efa_overrides_default(self):
        """User-specified EFA value takes precedence over the instance default."""
        job = self._resolve(job_name="test-efa", accelerators=4, efa_interfaces=2, instance_type="ml.p4d.24xlarge")
        requests, limits = self._get_resources(job)

        self.assertEqual(int(requests["vpc.amazonaws.com/efa"]), 2)
        self.assertEqual(int(limits["vpc.amazonaws.com/efa"]), 2)

    def test_instance_without_efa_gets_no_efa(self):
        """Instance that doesn't support EFA (g5.xlarge) gets no EFA resources."""
        job = self._resolve(job_name="test-no-efa", accelerators=1, instance_type="ml.g5.xlarge")
        requests, limits = self._get_resources(job)

        self.assertNotIn("vpc.amazonaws.com/efa", requests)
        self.assertNotIn("vpc.amazonaws.com/efa", limits)
        self.assertIn("nvidia.com/gpu", requests)

    def test_all_resource_types_together(self):
        """Accelerators, CPU, memory, and EFA all resolve correctly in a single job."""
        job = self._resolve(
            job_name="test-all", accelerators=4, vcpu=16.0, memory=64.0,
            instance_type="ml.p4d.24xlarge",
        )
        requests, limits = self._get_resources(job)

        self.assertIn("nvidia.com/gpu", requests)
        self.assertIn("cpu", requests)
        self.assertIn("memory", requests)
        self.assertIn("vpc.amazonaws.com/efa", requests)

    def test_accelerators_without_instance_type_rejected(self):
        """Specifying accelerators without instance_type raises a clear error."""
        from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
            Containers, ReplicaSpec, Resources, Spec, Template,
        )

        job = HyperPodPytorchJob(
            metadata={"name": "test-no-instance-type", "namespace": "default"},
            replica_specs=[ReplicaSpec(
                name="pod",
                template=Template(
                    spec=Spec(containers=[Containers(
                        name="test",
                        image="pytorch:latest",
                        resources=Resources(
                            requests={"nvidia.com/gpu": "4"},
                            limits={"nvidia.com/gpu": "4"},
                        ),
                    )])
                ),
            )],
        )

        with self.assertRaises(ValueError, msg="--instance-type is required when specifying accelerator resources"):
            HyperPodPytorchJob.allocate_quotas_if_applicable(job)


class TestDeepHealthCheckNodeSelector(unittest.TestCase):
    """Test that deep_health_check_passed_nodes_only generates the correct nodeSelector label."""

    EXPECTED_LABEL_KEY = "sagemaker.amazonaws.com/deep-health-check-status"
    EXPECTED_LABEL_VALUE = "Passed"

    def test_v1_1_model_to_domain_deep_health_check_label(self):
        """Test v1.1 model to_domain() produces the correct node selector label."""
        config = PyTorchJobConfig(
            job_name="test-dhc",
            image="pytorch:latest",
            deep_health_check_passed_nodes_only=True,
            instance_type="ml.g5.xlarge",
            accelerators=1,
        )
        job = config.to_domain()
        node_selector = job.replicaSpecs[0].template.spec.nodeSelector
        self.assertIn(self.EXPECTED_LABEL_KEY, node_selector)
        self.assertEqual(node_selector[self.EXPECTED_LABEL_KEY], self.EXPECTED_LABEL_VALUE)

    def test_v1_1_model_to_domain_no_deep_health_check(self):
        """Test v1.1 model to_domain() omits the label when flag is False."""
        config = PyTorchJobConfig(
            job_name="test-no-dhc",
            image="pytorch:latest",
            deep_health_check_passed_nodes_only=False,
            instance_type="ml.g5.xlarge",
            accelerators=1,
        )
        job = config.to_domain()
        node_selector = job.replicaSpecs[0].template.spec.nodeSelector or {}
        self.assertNotIn(self.EXPECTED_LABEL_KEY, node_selector)

    def test_v1_0_model_to_domain_deep_health_check_label(self):
        """Test v1.0 model to_domain() produces the correct node selector label."""
        config = PyTorchJobConfigV1_0(
            job_name="test-dhc-v0",
            image="pytorch:latest",
            deep_health_check_passed_nodes_only=True,
            instance_type="ml.g5.xlarge",
        )
        job = config.to_domain()
        node_selector = job.replicaSpecs[0].template.spec.nodeSelector
        self.assertIn(self.EXPECTED_LABEL_KEY, node_selector)
        self.assertEqual(node_selector[self.EXPECTED_LABEL_KEY], self.EXPECTED_LABEL_VALUE)


if __name__ == '__main__':
    unittest.main()
