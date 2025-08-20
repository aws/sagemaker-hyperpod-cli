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


class TestHypCLICommands:
    """Integration tests for HyperPod CLI using hyp commands."""

    def test_list_clusters(self, cluster_name):
        """Test listing clusters """
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

    def test_create_job(self, test_job_name, image_uri):
        """Test creating a PyTorch job using the correct CLI parameters."""
        result = execute_command([
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.0",
            "--job-name", test_job_name,
            "--image", image_uri,
            "--pull-policy", "Always",
            "--tasks-per-node", "1",
            "--max-retry", "1"
        ])
        assert result.returncode == 0
        logger.info(f"Created job: {test_job_name}")

        # Wait a moment for the job to be created
        time.sleep(5)

    def test_list_jobs(self, test_job_name):
        """Test listing jobs and verifying the created job is present with a valid status."""
        list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
        assert list_result.returncode == 0

        # Check if the job name is in the output
        assert test_job_name in list_result.stdout

        # Check that the job status is not Unknown
        output_lines = list_result.stdout.strip().split('\n')
        job_status = None
        for line in output_lines:
            if test_job_name in line:
                # Extract the status from the line (assuming format: NAME NAMESPACE STATUS AGE)
                parts = line.split()
                if len(parts) >= 3:
                    job_status = parts[2].strip()
                break

        # Verify job status is not Unknown
        assert job_status is not None, f"Could not find status for job {test_job_name}"
        assert job_status != "Unknown", f"Job {test_job_name} has Unknown status, which indicates a potential issue"

        logger.info(f"Successfully listed jobs. Job {test_job_name} has status: {job_status}")

    def test_wait_for_job_running(self, test_job_name):
        """Test that the job transitions to Running state before proceeding with pod tests."""
        max_attempts = 10  # Maximum number of attempts (5 minutes total with 30-second intervals)
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking job status (attempt {attempt}/{max_attempts})...")

            # Get the job status
            list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
            assert list_result.returncode == 0

            # Check if the job is in Running or Completed state
            output_lines = list_result.stdout.strip().split('\n')
            job_status = None
            for line in output_lines:
                if test_job_name in line:
                    # Extract the status from the line (assuming format: NAME NAMESPACE STATUS AGE)
                    parts = line.split()
                    if len(parts) >= 3:
                        job_status = parts[2].strip()
                    break

            logger.info(f"Current job status: {job_status}")

            # If job status is Unknown, fail immediately
            if job_status == "Unknown":
                pytest.fail(f"Job {test_job_name} has Unknown status, which indicates a potential issue. Test failed.")

            # If job is Running or Completed, we can proceed
            if job_status in ["Running", "Completed"]:
                logger.info(f"Job {test_job_name} is now in {job_status} state")
                return

            # If job is still in Created or another state, wait and try again
            logger.info(f"Job {test_job_name} is in {job_status} state, waiting...")
            time.sleep(30)  # Wait 30 seconds before checking again

        # If we've exhausted all attempts, fail the test
        pytest.fail(f"Job {test_job_name} did not reach Running state within the timeout period")

    def test_wait_for_job_completion(self, test_job_name):
        """Test that the job reaches Completed status within 10 minutes, with early failure if not Running."""
        max_attempts = 20  # Maximum number of attempts (10 minutes total with 30-second intervals)
        for attempt in range(1, max_attempts + 1):
            logger.info(f"Checking job completion status (attempt {attempt}/{max_attempts})...")

            # Get the job status
            list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
            assert list_result.returncode == 0

            # Check the job status
            output_lines = list_result.stdout.strip().split('\n')
            job_status = None
            for line in output_lines:
                if test_job_name in line:
                    # Extract the status from the line (assuming format: NAME NAMESPACE STATUS AGE)
                    parts = line.split()
                    if len(parts) >= 3:
                        job_status = parts[2].strip()
                    break

            logger.info(f"Current job status: {job_status}")

            # If job is Completed, test passes
            if job_status == "Completed":
                logger.info(f"Job {test_job_name} has successfully completed")
                return

            # If job is not Running or Completed, fail the test
            if job_status not in ["Running", "Completed"]:
                pytest.fail(f"Job {test_job_name} is in {job_status} state, which is not Running or Completed. Test failed.")

            # If job is still Running, wait and try again
            logger.info(f"Job {test_job_name} is still running, waiting...")
            time.sleep(30)  # Wait 30 seconds before checking again

        # If we've exhausted all attempts, fail the test
        pytest.fail(f"Job {test_job_name} did not reach Completed state within the 10-minute timeout period")

    def test_list_pods(self, test_job_name):
        """Test listing pods for a specific job."""
        # Wait a moment to ensure pods are created
        time.sleep(10)

        list_pods_result = execute_command([
            "hyp", "list-pods", "hyp-pytorch-job",
            "--job-name", test_job_name
        ])
        assert list_pods_result.returncode == 0

        # Verify the output contains expected headers and job name
        output = list_pods_result.stdout.strip()
        assert f"Pods for job: {test_job_name}" in output
        assert "POD NAME" in output
        assert "NAMESPACE" in output

        # Verify at least one pod is listed (should contain the job name in the pod name)
        assert f"{test_job_name}-pod-" in output

        logger.info(f"Successfully listed pods for job: {test_job_name}")

    def test_get_logs(self, test_job_name):
        """Test getting logs for a specific pod in a job."""
        # First, get the pod name from list-pods command
        list_pods_result = execute_command([
            "hyp", "list-pods", "hyp-pytorch-job",
            "--job-name", test_job_name
        ])
        assert list_pods_result.returncode == 0

        # Extract the pod name from the output
        output_lines = list_pods_result.stdout.strip().split('\n')
        pod_name = None
        for line in output_lines:
            if f"{test_job_name}-pod-" in line:
                # Extract the pod name from the line
                pod_name = line.split()[0].strip()
                break

        assert pod_name is not None, f"Could not find pod for job {test_job_name}"
        logger.info(f"Found pod: {pod_name}")

        # Now get logs for this pod
        get_logs_result = execute_command([
            "hyp", "get-logs", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--pod-name", pod_name
        ])
        assert get_logs_result.returncode == 0

        # Verify the output contains the expected header
        logs_output = get_logs_result.stdout.strip()
        assert f"Listing logs for pod: {pod_name}" in logs_output

        logger.info(f"Successfully retrieved logs for pod: {pod_name}")

    def test_describe_job(self, test_job_name):
        """Test describing a specific job and verifying the output."""
        describe_result = execute_command(["hyp", "describe", "hyp-pytorch-job", "--job-name", test_job_name])
        assert describe_result.returncode == 0

        # Check if either the job name is in the output or metadata is present
        assert test_job_name in describe_result.stdout
        logger.info(f"Successfully described job: {test_job_name}")

    @pytest.mark.run(order=99)
    def test_delete_job(self, test_job_name):
        """Test deleting a job and verifying deletion."""
        delete_result = execute_command(["hyp", "delete", "hyp-pytorch-job", "--job-name", test_job_name])
        assert delete_result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

        # Wait a moment for the job to be deleted
        time.sleep(5)

        # Verify the job is no longer listed
        list_result = execute_command(["hyp", "list", "hyp-pytorch-job"])
        assert list_result.returncode == 0

        # The job name should no longer be in the output
        assert test_job_name not in list_result.stdout

def test_pytorch_get_operator_logs():
    """Test getting operator logs via CLI"""
    result = execute_command(["hyp", "get-operator-logs", "hyp-pytorch-job", "--since-hours", "1"])
    assert result.returncode == 0
