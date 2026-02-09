import time

from sagemaker.hyperpod.cli.utils import setup_logger
from test.integration_tests.utils import execute_command

logger = setup_logger(__name__)

NAMESPACE = "hyperpod-ns-team1"
QUEUE = "hyperpod-ns-team1-localqueue"

class TestAcceleratorPartitionIntegration:
    """Integration tests for accelerator partition CLI commands"""

    def test_create_job_with_accelerator_partition(self, test_job_name, skip_validate_accelerator_partition_in_cluster):
        """Test creating a job with accelerator partition parameters"""
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE,
            "--instance-type", "ml.p4d.24xlarge",
            "--accelerator-partition-type", "mig-1g.5gb",
            "--accelerator-partition-count", "2"
        ]

        result = execute_command(create_cmd)
        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with accelerator partition: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]

        result = execute_command(describe_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0

        # Check that accelerator partition resources are in the job spec
        assert "nvidia.com/mig-1g.5gb" in result.stdout
        assert "'nvidia.com/mig-1g.5gb': '2'" in result.stdout

        # Clean up
        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_accelerator_partition_and_limit(self, test_job_name, skip_validate_accelerator_partition_in_cluster):
        """Test creating a job with accelerator partition count and limit"""

        # Clean up any existing job first
        try:
            delete_cmd = [
                "hyp", "delete", "hyp-pytorch-job",
                "--job-name", test_job_name,
                "--namespace", NAMESPACE
            ]
            execute_command(delete_cmd)
            time.sleep(2)
        except RuntimeError:
            pass  # Job doesn't exist

        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE,
            "--instance-type", "ml.p4d.24xlarge",
            "--accelerator-partition-type", "mig-2g.10gb",
            "--accelerator-partition-count", "1",
            "--accelerator-partition-limit", "2"
        ]

        result = execute_command(create_cmd)
        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with accelerator partition and limit: {test_job_name}")

        # Wait a moment for the job to be created
        time.sleep(5)

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)
        assert result.returncode == 0

        # Verify both request and limit are set
        assert "nvidia.com/mig-2g.10gb" in result.stdout
        assert "'nvidia.com/mig-2g.10gb': '1'" in result.stdout
        assert "'nvidia.com/mig-2g.10gb': '2'" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_invalid_accelerator_partition_type(self, test_job_name, skip_validate_accelerator_partition_in_cluster):
        """Test that invalid accelerator partition types are rejected"""

        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--namespace", NAMESPACE,
            "--queue-name", QUEUE,
            "--instance-type", "ml.p4d.24xlarge",
            "--accelerator-partition-type", "invalid-partition-type",
            "--accelerator-partition-count", "1"
        ]

        try:
            execute_command(create_cmd)
        except RuntimeError as e:
            assert "Failed to execute command: hyp create hyp-pytorch-job" in str(e)

    def test_accelerator_partition_count_without_type(self, test_job_name, skip_validate_accelerator_partition_in_cluster):
        """Test that accelerator partition count without type is handled correctly"""
        
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--namespace", NAMESPACE,
            "--queue-name", QUEUE,
            "--instance-type", "ml.p4d.24xlarge",
            "--accelerator-partition-count", "2"
            # Missing --accelerator-partition-type
        ]
        
        try:
            execute_command(create_cmd)
        except RuntimeError as e:
            assert "Failed to execute command: hyp create hyp-pytorch-job" in str(e)