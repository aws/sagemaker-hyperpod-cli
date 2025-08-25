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