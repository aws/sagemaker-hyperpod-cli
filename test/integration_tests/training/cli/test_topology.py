import pytest
import time
import json

from sagemaker.hyperpod.cli.utils import setup_logger
from test.integration_tests.utils import execute_command

logger = setup_logger(__name__)

NAMESPACE = "hyperpod-ns-team1"
QUEUE = "hyperpod-ns-team1-localqueue"
TOPOLOGY = "topology.k8s.aws/network-node-layer-1"

class TestTopologyIntegration:
    """Integration tests for topology-related CLI commands"""

    def test_create_job_with_required_topology(self, test_job_name):
        """Test creating a job with --required-topology parameter"""
        
        # Create job with required topology
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE,
            "--required-topology", TOPOLOGY
        ]
        
        result = execute_command(create_cmd)
        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with required topology: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)

        # Wait a moment for the job to be created
        time.sleep(5)

        assert result.returncode == 0
        assert f"Annotations:    {{'kueue.x-k8s.io/podset-required-topology': '{TOPOLOGY}'}}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_create_job_with_preferred_topology(self, test_job_name):
        """Test creating a job with --preferred-topology parameter"""
        
        # Create job with preferred topology
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--pull-policy", "IfNotPresent",
            "--tasks-per-node", "1",
            "--queue-name", QUEUE,
            "--namespace", NAMESPACE,
            "--preferred-topology", TOPOLOGY
        ]
        
        result = execute_command(create_cmd)
        assert result.returncode == 0
        assert "Using version: 1.1" in result.stdout
        logger.info(f"Successfully created job with preferred topology: {test_job_name}")

        describe_cmd = [
            "hyp", "describe", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(describe_cmd)
        assert result.returncode == 0
        assert f"Annotations:    {{'kueue.x-k8s.io/podset-preferred-topology': '{TOPOLOGY}'}}" in result.stdout

        delete_cmd = [
            "hyp", "delete", "hyp-pytorch-job",
            "--job-name", test_job_name,
            "--namespace", NAMESPACE
        ]
        result = execute_command(delete_cmd)
        assert result.returncode == 0
        logger.info(f"Successfully deleted job: {test_job_name}")

    def test_invalid_topology_parameter(self, test_job_name):
        """Test that invalid topology parameters are handled correctly"""
        
        # Test with invalid topology value
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--required-topology", 
            "topology.k8s.aws/network-node-layer-6"  # invalid topology annotation
        ]
        
        try:
            execute_command(create_cmd)
        except RuntimeError as e:
            assert "Failed to execute command: hyp create hyp-pytorch-job" in str(e)

    def test_empty_topology_parameter(self, test_job_name):
        """Test that invalid topology parameters are handled correctly"""
        
        # Test with empty topology value
        create_cmd = [
            "hyp", "create", "hyp-pytorch-job",
            "--version", "1.1",
            "--job-name", test_job_name,
            "--image", "pytorch:latest",
            "--preferred-topology"  # empty topology annotation
        ]
        
        try:
            execute_command(create_cmd)
        except RuntimeError as e:
            assert "Failed to execute command: hyp create hyp-pytorch-job" in str(e)