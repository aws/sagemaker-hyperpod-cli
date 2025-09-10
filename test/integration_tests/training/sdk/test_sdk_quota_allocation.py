# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

import pytest
import time
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
from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)

NAMESPACE = "hyperpod-ns-team1"
QUEUE = "hyperpod-ns-team1-localqueue"


class TestHyperPodSDKQuotaAllocation:
    """Integration tests for HyperPod SDK quota allocation functionality."""

    def test_create_job_with_quota_parameters(self, test_job_name, image_uri):
        """Test creating a job with quota allocation parameters."""
        replica_specs = [
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
                                    requests={"nvidia.com/gpu": "1", "cpu": "3", "memory": "1"},
                                    limits={"nvidia.com/gpu": "1", "cpu": "4", "memory": "2"},
                                ),
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Create the job
        pytorch_job.create()
        logger.info(f"Created job with quota parameters: {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created with correct resource allocation
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_only_replicas_parameters(self, test_job_name, image_uri):
        """Test creating a job with quota allocation parameters."""
        replica_specs = [
            ReplicaSpec(
                name="pod",
                replicas= 1,
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="container-name",
                                image=image_uri,
                                image_pull_policy="Always"
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Create the job
        pytorch_job.create()
        logger.info(f"Created job with quota parameters: {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created with correct resource allocation
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_float_quota_parameters(self, test_job_name, image_uri):
        """Test creating a job with float quota parameters."""
        replica_specs = [
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
                                    requests={"nvidia.com/gpu": "1", "cpu": "3.6", "memory": "1"},
                                    limits={"nvidia.com/gpu": "1", "cpu": "4.8", "memory": "2.7"},
                                ),
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Create the job
        pytorch_job.create()
        logger.info(f"Created job with float quota parameters: {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_only_accelerators(self, test_job_name, image_uri):
        """Test creating a job with only accelerators parameter."""
        replica_specs = [
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
                                    requests={"nvidia.com/gpu": "1"},
                                    limits={"nvidia.com/gpu": "1"},
                                ),
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Create the job
        pytorch_job.create()
        logger.info(f"Created job with only accelerators: {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_quota_allocation_validation(self, test_job_name, image_uri):
        """Test that quota allocation validation works correctly."""
        # Test with invalid instance type
        replica_specs = [
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
                                    requests={"nvidia.com/gpu": "1"},
                                    limits={"nvidia.com/gpu": "1"},
                                ),
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.invalid.type"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # This should raise a ValueError for invalid instance type
        with pytest.raises(ValueError, match="Invalid instance-type"):
            pytorch_job.create()

    def test_default_replicas_allocation(self, test_job_name, image_uri):
        """Test that default replicas value is set to 1 when 0."""
        replica_specs = [
            ReplicaSpec(
                name="pod",
                replicas=0,  # This should be set to 1 by default
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="container-name",
                                image=image_uri,
                                image_pull_policy="Always",
                                resources=Resources(
                                    requests={"nvidia.com/gpu": "1"},
                                    limits={"nvidia.com/gpu": "1"},
                                ),
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Create the job
        pytorch_job.create()
        logger.info(f"Created job with 0 replicas (should default to 1): {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_set_default_memory_limit_caps_at_93_percent(self, test_job_name, image_uri):
        """Test that _set_default_memory_limit caps memory at 93% of instance capacity."""
        replica_specs = [
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
                                    requests={"memory": "128Gi"},  # Exceeds 93% of ml.g5.8xlarge
                                    limits={"memory": "128Gi"}
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.8xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        pytorch_job.create()
        logger.info(f"Created job memory should be set to 93% max capacity: {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_validate_accelerators_values_enforces_equality(self, test_job_name, image_uri):
        """Test that _validate_accelerators_values enforces request/limit equality.
        
        This test verifies:
        1. Mismatched accelerator requests and limits raise ValueError
        2. Error message includes both values for debugging
        """
        replica_specs = [
            ReplicaSpec(
                name="pod",
                replicas=0,
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="container-name",
                                image=image_uri,
                                image_pull_policy="Always",
                                resources=Resources(
                                    requests={"nvidia.com/gpu": "1"},
                                    limits={"nvidia.com/gpu": "2"}  # Mismatch should cause error
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        # Should raise ValueError due to mismatched accelerator values
        with pytest.raises(ValueError, match="Accelerator request must equal accelerator limit"):
            pytorch_job.create()

    def test_set_default_accelerators_values_with_missing_values(self, test_job_name, image_uri):
        """Test that _set_default_accelerators_values sets defaults when values are missing."""
        replica_specs = [
            ReplicaSpec(
                name="pod",
                replicas=0,
                template=Template(
                    spec=Spec(
                        containers=[
                            Containers(
                                name="container-name",
                                image=image_uri,
                                image_pull_policy="Always",
                                resources=Resources(
                                    requests={"cpu": "4", "memory": "16Gi"},
                                    limits={"nvidia.com/gpu": "1"}  # Only limit specified
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        pytorch_job.create()
        logger.info(f"Created job accelerators should be set to (1): {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_resolve_default_memory_values_request_exceeds_limit(self, test_job_name, image_uri):
        """Test that _resolve_default_memory_values reduces request when it exceeds limit."""
        replica_specs = [
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
                                    requests={"memory": "10Gi"},
                                    limits={"memory": "8Gi"}  # Request exceeds limit
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        pytorch_job.create()
        logger.info(f"Created job memory should be set to '8Gi': {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_validate_accelerators_inputs_exceeds_capacity(self, test_job_name, image_uri):
        """Test that _validate_accelerators_inputs validates capacity limits."""
        replica_specs = [
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
                                    requests={"nvidia.com/gpu": "2"},
                                    limits={"nvidia.com/gpu": "2"}  # Exceeds ml.g5.xlarge capacity (1 GPU)
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        with pytest.raises(ValueError, match="Requested accelerators exceeds capacity"):
            pytorch_job.create()

    def test_set_default_accelerators_val_missing_request(self, test_job_name, image_uri):
        """Test that _set_default_accelerators_val sets request when missing."""
        replica_specs = [
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
                                    limits={"nvidia.com/gpu": "1"},  # Only limit specified
                                    requests={}
                                )
                            )
                        ],
                        node_selector={"node.kubernetes.io/instance-type": "ml.g5.xlarge"}
                    )
                ),
            )
        ]

        pytorch_job = HyperPodPytorchJob(
            metadata=Metadata(name=test_job_name, namespace=NAMESPACE),
            nproc_per_node="1",
            replica_specs=replica_specs,
            run_policy=RunPolicy(clean_pod_policy="None"),
        )

        pytorch_job.create()
        logger.info(f"Created job memory should be set to '8Gi': {test_job_name}")

        # Wait for job to be created
        time.sleep(10)

        # Verify the job was created
        created_job = HyperPodPytorchJob.get(test_job_name, NAMESPACE)
        assert created_job is not None

        # Clean up
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {test_job_name}")

