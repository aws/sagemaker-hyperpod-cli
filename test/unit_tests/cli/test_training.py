import unittest
from unittest.mock import patch, MagicMock, Mock
import click
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.training import (
    pytorch_create,
    list_jobs,
    pytorch_describe,
)
from unittest.mock import Mock


class TestTrainingCommands(unittest.TestCase):
    """Test cases for the training commands module"""

    def setUp(self):
        self.runner = CliRunner()
        self.test_config = {
            "name": "test-job",
            "spec": {
                "nprocPerNode": "auto",
                "replicaSpecs": [
                    {
                        "name": "test-job",
                        "replicas": 1,
                        "template": {
                            "spec": {
                                "containers": [
                                    {"name": "test-job", "image": "test-image"}
                                ]
                            }
                        },
                    }
                ],
            },
        }
        self.test_config_with_namespace = {
            **self.test_config,
            "namespace": "test-namespace",
        }

    def test_commands_exist(self):
        """Test that all commands exist"""
        self.assertIsNotNone(pytorch_create)
        self.assertTrue(callable(pytorch_create))
        self.assertIsNotNone(list_jobs)
        self.assertTrue(callable(list_jobs))
        self.assertIsNotNone(pytorch_describe)
        self.assertTrue(callable(pytorch_describe))

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_basic_job_creation(self, mock_hyperpod_job):
        """Test basic job creation with required parameters"""
        # Setup mock
        mock_instance = Mock()
        mock_hyperpod_job.return_value = mock_instance

        # Run command with required parameters
        result = self.runner.invoke(
            pytorch_create,
            ["--version", "1.0", "--job-name", "test-job", "--image", "test-image"],
        )

        # Print output for debugging
        print(f"Command output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")

        # Assertions
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Using version: 1.0", result.output)

        # Verify HyperPodPytorchJob was created correctly
        mock_hyperpod_job.assert_called_once()
        call_args = mock_hyperpod_job.call_args[1]
        self.assertEqual(call_args["metadata"].name, "test-job")
        mock_instance.create.assert_called_once()

    def test_missing_required_params(self):
        """Test that command fails when required parameters are missing"""
        # Test missing job-name
        result = self.runner.invoke(pytorch_create, ["--version", "1.0"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing option '--job-name'", result.output)

        # Test missing image
        result = self.runner.invoke(
            pytorch_create, ["--version", "1.0", "--job-name", "test-job"]
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Missing option '--image'", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_optional_params(self, mock_hyperpod_job):
        """Test job creation with optional parameters"""
        mock_instance = Mock()
        mock_hyperpod_job.return_value = mock_instance

        result = self.runner.invoke(
            pytorch_create,
            [
                "--version",
                "1.0",
                "--job-name",
                "test-job",
                "--image",
                "test-image",
                "--namespace",
                "test-namespace",
                "--node-count",
                "2",
            ],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Using version: 1.0", result.output)

        mock_hyperpod_job.assert_called_once()
        call_args = mock_hyperpod_job.call_args[1]
        self.assertEqual(call_args["metadata"].name, "test-job")
        self.assertEqual(call_args["metadata"].namespace, "test-namespace")

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_list_jobs(self, mock_hyperpod_pytorch_job):
        """Test the list_jobs function"""
        mock_job1 = Mock()
        mock_job1.metadata.name = "job1"
        mock_job1.metadata.namespace = "test-namespace"
        mock_job1.status.conditions = [Mock(status="True", type="Running")]

        mock_job2 = Mock()
        mock_job2.metadata.name = "job2"
        mock_job2.metadata.namespace = "test-namespace"
        mock_job2.status.conditions = [Mock(status="True", type="Succeeded")]

        # Mock the HyperPodPytorchJob.list method
        mock_hyperpod_pytorch_job.list.return_value = [mock_job1, mock_job2]

        # Call the function
        result = self.runner.invoke(list_jobs, ["--namespace", "test-namespace"])

        # Verify the result
        self.assertEqual(result.exit_code, 0)
        mock_hyperpod_pytorch_job.list.assert_called_once_with(
            namespace="test-namespace"
        )
        self.assertIn("NAME", result.output)
        self.assertIn("job1", result.output)
        self.assertIn("job2", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_list_jobs_empty(self, mock_hyperpod_pytorch_job):
        """Test the list_jobs function with no jobs"""
        # Mock the HyperPodPytorchJob.list method to return empty list
        mock_hyperpod_pytorch_job.list.return_value = []

        # Call the function
        result = self.runner.invoke(list_jobs)

        # Verify the result
        self.assertEqual(result.exit_code, 0)
        mock_hyperpod_pytorch_job.list.assert_called_once_with(namespace="default")
        self.assertIn("No jobs found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_list_jobs_error(self, mock_hyperpod_pytorch_job):
        """Test error handling in list_jobs function"""
        # Mock the HyperPodPytorchJob.list method to raise an exception
        mock_hyperpod_pytorch_job.list.side_effect = Exception("Test error")

        # Call the function and expect an exception
        result = self.runner.invoke(list_jobs)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Failed to list jobs", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_pytorch_describe(self, mock_hyperpod_pytorch_job):
        """Test the pytorch_describe function"""
        # Mock the HyperPodPytorchJob.get method
        mock_job = MagicMock()
        mock_job.model_dump = {"name": "test-job", "status": "Running"}
        mock_hyperpod_pytorch_job.get.return_value = mock_job

        # Call the function
        result = self.runner.invoke(
            pytorch_describe,
            ["--job-name", "test-job", "--namespace", "test-namespace"],
        )

        # Verify the result
        self.assertEqual(result.exit_code, 0)
        mock_hyperpod_pytorch_job.get.assert_called_once_with(
            name="test-job", namespace="test-namespace"
        )
        self.assertIn("Job Details:", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_pytorch_describe_not_found(self, mock_hyperpod_pytorch_job):
        """Test the pytorch_describe function with job not found"""
        # Mock the HyperPodPytorchJob.get method to return None
        mock_hyperpod_pytorch_job.get.return_value = None

        # Call the function
        result = self.runner.invoke(pytorch_describe, ["--job-name", "test-job"])

        # Verify the result
        self.assertNotEqual(result.exit_code, 0)
        mock_hyperpod_pytorch_job.get.assert_called_once_with(
            name="test-job", namespace="default"
        )
        self.assertIn("not found", result.output)

    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_pytorch_describe_error(self, mock_hyperpod_pytorch_job):
        """Test error handling in pytorch_describe function"""
        # Mock the HyperPodPytorchJob.get method to raise an exception
        mock_hyperpod_pytorch_job.get.side_effect = Exception("Test error")

        # Call the function and expect an exception
        result = self.runner.invoke(pytorch_describe, ["--job-name", "test-job"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Failed to describe job", result.output)

