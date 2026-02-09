import unittest
from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig


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


if __name__ == '__main__':
    unittest.main()
