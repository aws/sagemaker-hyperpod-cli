import pytest
import time
import json
import subprocess

from sagemaker.hyperpod.cli.utils import setup_logger
from test.integration_tests.utils import execute_command

logger = setup_logger(__name__)

NAMESPACE = "hyperpod-ns-team1"
QUEUE = "hyperpod-ns-team1-localqueue"

class TestGpuQuotaAllocationIntegration:
    """Integration tests for Gpu-Quota Allocation related CLI commands"""

    def test_create_job_with_integer_quota_parameters(self, test_job_name):
        """Test creating a job with accelerators, vcpu and memory parameters"""

        # Create job with required gpu quota parameters
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--instance-type", "ml.g5.8xlarge",
            "--vcpu", "3",
            "--memory", "1",
            "--accelerators-limit", "1",
            "--vcpu-limit", "4",
            "--memory-limit", "2",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]

        result = execute_command(create_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with required gpu quota parameters: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)
        logger.info(f"describe result: {result}")
        assert result.returncode == 0
        assert "      Limits:   {'cpu': '4', 'memory': '2Gi', 'nvidia.com/gpu': '1'}" in result.stdout
        assert "      Requests: {'cpu': '3', 'memory': '1Gi', 'nvidia.com/gpu': '1'}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_float_quota_parameters(self, test_job_name):
        """Test creating a job with float values for accelerators, vcpu and memory parameters"""

        # Create job with required gpu quota parameters with float values
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--instance-type", "ml.g5.8xlarge",
            "--vcpu", "3.6",
            "--memory", "1",
            "--accelerators-limit", "1",
            "--vcpu-limit", "4.8",
            "--memory-limit", "2.7",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]

        result = execute_command(create_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with required gpu quota parameters: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)
        assert result.returncode == 0
        assert "      Limits:   {'cpu': '4800m', 'memory': '2899102924800m', 'nvidia.com/gpu': '1'}" in result.stdout
        assert "      Requests: {'cpu': '3600m', 'memory': '1Gi', 'nvidia.com/gpu': '1'}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_only_accelerators_parameter(self, test_job_name):
        """Test creating a job with only accelerators parameter"""

        # Create job with only accelerators parameter
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--instance-type", "ml.g5.8xlarge",
            "--accelerators-limit", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]

        result = execute_command(create_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with required gpu quota parameters: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)
        assert result.returncode == 0
        assert "      Limits:   {'memory': '104Gi', 'nvidia.com/gpu': '1'}" in result.stdout
        assert "      Requests: {'cpu': '29', 'memory': '104Gi', 'nvidia.com/gpu': '1'}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_accelerators_memory_parameters(self, test_job_name):
        """Test creating a job with accelerators, memory parameters"""
        # Create job with only accelerators, memory parameters
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--memory", "1.9",
            "--instance-type", "ml.g5.8xlarge",
            "--accelerators-limit", "1",
            "--memory-limit", "2.7",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]

        result = execute_command(create_cmd)
        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with required gpu quota parameters: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0
        assert "      Limits:   {'memory': '2899102924800m', 'nvidia.com/gpu': '1'}" in result.stdout
        assert "      Requests: {'cpu': '29', 'memory': '2040109465600m', 'nvidia.com/gpu': '1'}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_invalid_node_count_accelerators_parameter(self, test_job_name):
        """Test that invalid case where both node-count and accelerators are provided"""

        # Test with both node-count and accelerators parameters
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--instance-type", "ml.g5.8xlarge",
            "--vcpu", "3",
            "--memory", "1",
            "--accelerators-limit", "1",
            "--vcpu-limit", "4",
            "--memory-limit", "2",
            "--node-count", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]
        result = subprocess.run(
                    create_cmd,
                    capture_output=True,
                    text=True
                )
        assert result.returncode != 0
        assert "Either node-count OR a combination of accelerators, vcpu, " in result.stdout
        assert "memory-in-gib must be specified for instance-type ml.g5.8xlarge" in result.stdout

    def test_invalid_no_node_count_or_quota_parameter(self, test_job_name):
        """Test that case where both node-count and any of the quota parameters are provided"""
        # Test with no node-count, no accelerators/vcpu/memory parameters
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--instance-type", "ml.g5.8xlarge",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]
        result = subprocess.run(
            create_cmd,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_invalid_instance_type_parameter(self, test_job_name):
        """Test case where invalid instance type parameter is provided"""

        # Test with both node-count and accelerators parameters
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--accelerators", "1",
            "--instance-type", "ml.n5.8xlarge",
            "--vcpu", "3",
            "--memory", "1",
            "--accelerators-limit", "1",
            "--vcpu-limit", "4",
            "--memory-limit", "2",
            "--node-count", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE
        ]
        result = subprocess.run(
            create_cmd,
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "Invalid instance-type ml.n5.8xlarge" in result.stdout
        logger.info("Successfully verified invalid instance type error")
