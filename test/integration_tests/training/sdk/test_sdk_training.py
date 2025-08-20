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
import yaml
from sagemaker.hyperpod.training import (
    HyperPodPytorchJob,
)
from sagemaker.hyperpod.common.config import Metadata
from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)


class TestHyperPodTrainingSDK:
    """Integration tests for HyperPod Training SDK."""

    def test_create_job(self, pytorch_job):
        """Test creating a PyTorch job using the SDK."""
        try:
            # The create() method doesn't return anything
            pytorch_job.create()
            logger.info(f"Job creation initiated: {pytorch_job.metadata.name}")

            # Wait for the job to be created and status to be available
            # We'll try a few times with increasing delays
            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(f"Waiting for job status to be available (attempt {attempt}/{max_attempts})...")
                    # Wait with increasing delay
                    time.sleep(attempt * 5)  # 5, 10, 15, 20, 25 seconds

                    # Get the job directly instead of using refresh
                    HyperPodPytorchJob.get(pytorch_job.metadata.name, pytorch_job.metadata.namespace)

                    # If we got here without exception, the job exists
                    logger.info(f"Job successfully created: {pytorch_job.metadata.name}")
                    return
                except Exception as e:
                    if "status" in str(e) and attempt < max_attempts:
                        logger.info(f"Status not available yet, retrying... ({e})")
                        continue
                    else:
                        raise

            # If we get here, we've exhausted our attempts
            pytest.fail(f"Job was created but status never became available after {max_attempts} attempts")
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            pytest.fail(f"Failed to create job: {e}")

    def test_list_jobs(self, pytorch_job):
        """Test listing jobs and verifying the created job is present."""
        jobs = HyperPodPytorchJob.list()
        assert jobs is not None

        # Check if the job name is in the list
        job_names = [job.metadata.name for job in jobs]
        assert pytorch_job.metadata.name in job_names

    def test_refresh_job(self, pytorch_job):
        pytorch_job.refresh()
        time.sleep(30)
        assert pytorch_job.status is not None, "Job status should not be None"
        logger.info(f"Refreshed job status:\n{yaml.dump(pytorch_job.status)}")

    def test_list_pods(self, pytorch_job):
        """Test listing pods for a specific job."""
        pods = pytorch_job.list_pods()
        assert pods is not None

        # Check if at least one pod is listed
        assert len(pods) > 0

        # Store the first pod name for later use
        pytest.pod_name = pods[0]

        logger.info(f"Successfully listed pods: {pods}")

    def test_get_logs(self, pytorch_job):
        """Test getting logs for a specific pod in a job."""
        pod_name = getattr(pytest, "pod_name", None)
        if not pod_name:
            pytest.skip("No pod name available from previous test")

        logs = pytorch_job.get_logs_from_pod(pod_name)
        assert logs is not None

        logger.info(f"Successfully retrieved logs for pod: {pod_name}")

    def test_delete_job(self, pytorch_job):
        """Test deleting a job."""
        pytorch_job.delete()
        logger.info(f"Successfully deleted job: {pytorch_job.metadata.name}")

        # Wait a moment for the job to be deleted
        time.sleep(5)

        # Verify the job is no longer listed
        jobs = HyperPodPytorchJob.list()
        job_names = [job.metadata.name for job in jobs]
        assert pytorch_job.metadata.name not in job_names

def test_get_operator_logs():
    """Test getting operator logs"""
    logs = HyperPodPytorchJob.get_operator_logs(since_hours=1)
    assert logs
