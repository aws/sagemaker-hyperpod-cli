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

from sagemaker.hyperpod.cli.utils import setup_logger
from test.integration_tests.utils import execute_command

logger = setup_logger(__name__)


# Fixture to provide test parameters for both elastic training scenarios
@pytest.fixture(params=[
    {
        "job_name_fixture": "test_elastic_job_name_increment",
        "create_args": [
            "--elastic-replica-increment-step", "2",
            "--max-node-count", "4",
            "--elastic-graceful-shutdown-timeout-in-seconds", "180",
            "--elastic-scaling-timeout-in-seconds", "90",
            "--elastic-scale-up-snooze-time-in-seconds", "120"
        ],
        "scenario": "increment_step"
    },
    {
        "job_name_fixture": "test_elastic_job_name_discrete",
        "create_args": [
            "--elastic-replica-discrete-values", "[2, 4, 8]",
            "--max-node-count", "8",
            "--elastic-graceful-shutdown-timeout-in-seconds", "180",
            "--elastic-scaling-timeout-in-seconds", "90"
        ],
        "scenario": "discrete_values"
    }
], ids=["increment_step", "discrete_values"])
def elastic_job_params(request):
    """Fixture providing parameters for both elastic training scenarios."""
    return request.param


class TestElasticTrainingCLI:
    """Integration tests for HyperPod CLI elastic training using hyp commands."""

    def test_list_clusters(self, cluster_name):
        """Test listing clusters"""
        assert cluster_name

    def test_get_cluster_context(self):
        """Test getting current cluster context."""
        result = execute_command(["hyp", "get-cluster-context"])
        assert result.returncode == 0

        context_output = result.stdout.strip()
        assert "Cluster context:" in context_output
        # Just verify we got a valid ARN without checking the specific name
        current_arn = context_output.split("Cluster context:")[-1].strip()
        assert "arn:aws:eks:" in current_arn

    def test_create_elastic_job(self, elastic_job_params, image_uri, request):
        """Test creating an elastic PyTorch job with different configurations."""
        # Get the job name from the fixture
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        # Build the command with common and scenario-specific args
        command = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", job_name,
            "--image", image_uri,
            "--pull-policy", "Always",
            "--tasks-per-node", "1",
            "--max-retry", "1"
        ]
        command.extend(elastic_job_params["create_args"])
        
        result = execute_command(command)
        assert result.returncode == 0
        logger.info(f"Created elastic job ({elastic_job_params['scenario']}): {job_name}")

        # Wait a moment for the job to be created
        time.sleep(5)

    def test_list_jobs(self, elastic_job_params, request):
        """Test listing jobs and verifying the elastic job is present with a valid status."""
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
        assert list_result.returncode == 0

        # Check if the job name is in the output
        assert job_name in list_result.stdout

        # Check that the job status is not Unknown
        output_lines = list_result.stdout.strip().split('\n')
        job_status = None
        for line in output_lines:
            if job_name in line:
                # Extract the status from the line (assuming format: NAME NAMESPACE STATUS AGE)
                parts = line.split()
                if len(parts) >= 3:
                    job_status = parts[2].strip()
                break

        # Verify job status is not Unknown
        assert job_status is not None, f"Could not find status for job {job_name}"
        assert job_status != "Unknown", f"Job {job_name} has Unknown status, which indicates a potential issue"

        logger.info(f"Successfully listed jobs. Job {job_name} ({elastic_job_params['scenario']}) has status: {job_status}")

    def test_wait_for_job_running(self, elastic_job_params, request):
        """Test that the elastic job transitions to Running state."""
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking elastic job status (attempt {attempt}/{max_attempts})...")

            list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
            assert list_result.returncode == 0

            output_lines = list_result.stdout.strip().split('\n')
            job_status = None
            for line in output_lines:
                if job_name in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        job_status = parts[2].strip()
                    break

            logger.info(f"Current elastic job status: {job_status}")

            if job_status == "Unknown":
                pytest.fail(f"Job {job_name} has Unknown status")

            if job_status in ["Running", "Completed"]:
                logger.info(f"Elastic job {job_name} ({elastic_job_params['scenario']}) is now in {job_status} state")
                return

            logger.info(f"Elastic job {job_name} is in {job_status} state, waiting...")
            time.sleep(30)

        pytest.fail(f"Elastic job {job_name} did not reach Running or Completed state within timeout")

    def test_wait_for_job_completion(self, elastic_job_params, request):
        """Test that the elastic job reaches Completed status."""
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        max_attempts = 20
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking elastic job completion status (attempt {attempt}/{max_attempts})...")

            list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
            assert list_result.returncode == 0

            output_lines = list_result.stdout.strip().split('\n')
            job_status = None
            for line in output_lines:
                if job_name in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        job_status = parts[2].strip()
                    break

            logger.info(f"Current elastic job status: {job_status}")

            if job_status == "Completed":
                logger.info(f"Elastic job {job_name} ({elastic_job_params['scenario']}) has successfully completed")
                return

            if job_status not in ["Running", "Completed"]:
                pytest.fail(f"Elastic job {job_name} is in {job_status} state")

            logger.info(f"Elastic job {job_name} is still running, waiting...")
            time.sleep(30)

        pytest.fail(f"Elastic job {job_name} did not reach Completed state within timeout")

    def test_list_pods(self, elastic_job_params, request):
        """Test listing pods for the elastic job."""
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        # Wait a moment to ensure pods are created
        time.sleep(10)

        list_pods_result = execute_command([
            "hyp", "list-pods", "hyp-pytorch-job",
            "--job-name", job_name
        ])
        assert list_pods_result.returncode == 0

        # Verify the output contains expected headers and job name
        output = list_pods_result.stdout.strip()
        assert f"Pods for job: {job_name}" in output
        assert "POD NAME" in output
        assert "NAMESPACE" in output

        # Verify at least one pod is listed (should contain the job name in the pod name)
        assert f"{job_name}-pod-" in output

        logger.info(f"Successfully listed pods for elastic job ({elastic_job_params['scenario']}): {job_name}")

    def test_delete_job(self, elastic_job_params, request):
        """Test deleting the elastic job."""
        job_name = request.getfixturevalue(elastic_job_params["job_name_fixture"])
        
        delete_result = execute_command(["hyp", "delete", "hyp-pytorch-job", "--job-name", job_name])
        assert delete_result.returncode == 0
        logger.info(f"Successfully deleted elastic job ({elastic_job_params['scenario']}): {job_name}")

        # Wait a moment for the job to be deleted
        time.sleep(5)

        # Verify the job is no longer listed
        list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
        assert list_result.returncode == 0

        # The job name should no longer be in the output
        assert job_name not in list_result.stdout
