import unittest
from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig
from hyperpod_pytorch_job_template.v1_0.model import PyTorchJobConfig as PyTorchJobConfigV1_0


class TestPyTorchJobConfigEFA(unittest.TestCase):
    """Test EFA resource allocation in PyTorchJobConfig"""

    # def test_single_node_no_efa(self):
    #     """Test that single-node jobs don't get EFA resources"""
    #     config = PyTorchJobConfig(
    #         job_name="test-single-node",
    #         image="pytorch:latest",
    #         node_count=1,
    #         accelerators=2,
    #         instance_type="ml.p4d.24xlarge"
    #     )
        
    #     job = config.to_domain()
    #     container = job.replicaSpecs[0].template.spec.containers[0]
        
    #     # Should not have EFA resources
    #     self.assertNotIn("vpc.amazonaws.com/efa", container.resources.requests)
    #     self.assertNotIn("vpc.amazonaws.com/efa", container.resources.limits)
        
    #     # Should have GPU resources
    #     self.assertEqual(container.resources.requests["nvidia.com/gpu"], "2")

    # def test_multi_node_with_efa(self):
    #     """Test that multi-node jobs automatically get EFA resources"""
    #     config = PyTorchJobConfig(
    #         job_name="test-multi-node",
    #         image="pytorch:latest",
    #         node_count=4,
    #         accelerators=8,
    #         instance_type="ml.p4d.24xlarge"
    #     )
        
    #     job = config.to_domain()
    #     container = job.replicaSpecs[0].template.spec.containers[0]
        
    #     # Should have EFA resources
    #     self.assertEqual(container.resources.requests["vpc.amazonaws.com/efa"], "1")
    #     self.assertEqual(container.resources.limits["vpc.amazonaws.com/efa"], "1")
        
    #     # Should also have GPU resources
    #     self.assertEqual(container.resources.requests["nvidia.com/gpu"], "8")

    def test_instance_without_efa_support_no_efa(self):
        """Test that instances without EFA support don't get EFA (ml.g5.xlarge doesn't support EFA)"""
        from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob

        config = PyTorchJobConfig(
            job_name="test-no-efa-support",
            image="pytorch:latest",
            accelerators=1,
            instance_type="ml.g5.xlarge"
        )

        job = config.to_domain()
        # Call allocate_quotas_if_applicable to convert generic keys to actual resource keys
        job_with_resources = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
        container = job_with_resources.replicaSpecs[0].template.spec.containers[0]

        # Should not have EFA resources (instance doesn't support it)
        self.assertNotIn("vpc.amazonaws.com/efa", container.resources.requests)
        self.assertNotIn("vpc.amazonaws.com/efa", container.resources.limits)

        # Should have GPU resources
        self.assertIn("nvidia.com/gpu", container.resources.requests)

    def test_accelerators_with_efa_support_gets_default_efa(self):
        """Test that specifying accelerators on EFA-capable instance gets EFA from constants"""
        from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob

        config = PyTorchJobConfig(
            job_name="test-accelerators-default-efa",
            image="pytorch:latest",
            accelerators=4,
            instance_type="ml.p4d.24xlarge"
        )

        job = config.to_domain()
        # Call allocate_quotas_if_applicable to convert generic keys to actual resource keys
        job_with_resources = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
        container = job_with_resources.replicaSpecs[0].template.spec.containers[0]

        # Should have EFA from constants
        self.assertIn("vpc.amazonaws.com/efa", container.resources.requests)
        self.assertIn("vpc.amazonaws.com/efa", container.resources.limits)
        self.assertEqual(int(container.resources.requests["vpc.amazonaws.com/efa"]), 4)

    def test_user_specified_efa_overrides_default(self):
        """Test that user-specified EFA value overrides the default from constants"""
        from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob

        config = PyTorchJobConfig(
            job_name="test-custom-efa",
            image="pytorch:latest",
            accelerators=4,
            efa_interfaces=2,
            instance_type="ml.p4d.24xlarge"
        )

        job = config.to_domain()
        # Call allocate_quotas_if_applicable to convert generic keys to actual resource keys
        job_with_resources = HyperPodPytorchJob.allocate_quotas_if_applicable(job)
        container = job_with_resources.replicaSpecs[0].template.spec.containers[0]

        # Should use user-specified EFA value
        self.assertEqual(int(container.resources.requests["vpc.amazonaws.com/efa"]), 2)
        self.assertEqual(int(container.resources.limits["vpc.amazonaws.com/efa"]), 2)

    # def test_multi_node_with_memory_and_cpu(self):
    #     """Test EFA with other resource types"""
    #     config = PyTorchJobConfig(
    #         job_name="test-multi-resources",
    #         image="pytorch:latest",
    #         node_count=2,
    #         accelerators=4,
    #         vcpu=16.0,
    #         memory=64.0,
    #         instance_type="ml.p4d.24xlarge"
    #     )
        
    #     job = config.to_domain()
    #     container = job.replicaSpecs[0].template.spec.containers[0]
        
    #     # Should have all resources including EFA
    #     self.assertEqual(container.resources.requests["vpc.amazonaws.com/efa"], "1")
    #     self.assertEqual(container.resources.requests["nvidia.com/gpu"], "4")
    #     self.assertEqual(container.resources.requests["cpu"], "16.0")
    #     self.assertEqual(container.resources.requests["memory"], "64.0Gi")

    # def test_accelerators_without_instance_type(self):
    #     """Test that accelerators work without instance_type (fixes the main issue)"""
    #     config = PyTorchJobConfig(
    #         job_name="test-no-instance-type",
    #         image="pytorch:latest",
    #         accelerators=4
    #         # No instance_type specified
    #     )
        
    #     job = config.to_domain()
    #     container = job.replicaSpecs[0].template.spec.containers[0]
        
    #     # Should respect accelerators value even without instance_type
    #     self.assertEqual(container.resources.requests["nvidia.com/gpu"], "4")
    #     # Limits should default to "0" since accelerators_limit not specified
    #     self.assertEqual(container.resources.limits["nvidia.com/gpu"], "0")


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
