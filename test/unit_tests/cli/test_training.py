import unittest
from unittest.mock import patch, MagicMock, Mock
import click
from click.testing import CliRunner
from sagemaker.hyperpod.cli.commands.training import (
    pytorch_create,
    list_jobs,
    pytorch_describe,
    pytorch_get_operator_logs,
    pytorch_exec,
)
from hyperpod_pytorch_job_template.v1_1.model import ALLOWED_TOPOLOGY_LABELS
import sys
import os
import importlib

# Add the hyperpod-pytorch-job-template to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'hyperpod-pytorch-job-template'))

try:
    from hyperpod_pytorch_job_template.v1_1.model import PyTorchJobConfig, VolumeConfig
    from pydantic import ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


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

    @patch('sys.argv', ['pytest', '--version', '1.0'])
    def test_basic_job_creation(self):
        """Test basic job creation with required parameters"""
        # Reload the training module with mocked sys.argv, as sys.argv is loaded during the import
        if 'sagemaker.hyperpod.cli.commands.training' in sys.modules:
            importlib.reload(sys.modules['sagemaker.hyperpod.cli.commands.training'])

        from sagemaker.hyperpod.cli.commands.training import pytorch_create

        with patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob") as mock_hyperpod_job:
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

    @patch('sys.argv', ['pytest', '--version', '1.1'])
    def test_optional_params(self):
        """Test job creation with optional parameters"""
        # Reload the training module with mocked sys.argv
        if 'sagemaker.hyperpod.cli.commands.training' in sys.modules:
            importlib.reload(sys.modules['sagemaker.hyperpod.cli.commands.training'])

        from sagemaker.hyperpod.cli.commands.training import pytorch_create

        with patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob") as mock_hyperpod_job:
            mock_instance = Mock()
            mock_hyperpod_job.return_value = mock_instance

            result = self.runner.invoke(
                pytorch_create,
                [
                    "--version",
                    "1.1",
                    "--job-name",
                    "test-job",
                    "--image",
                    "test-image",
                    "--namespace",
                    "test-namespace",
                    "--node-count",
                    "2",
                    "--queue-name",
                    "localqueue",
                    "--required-topology",
                    "topology.k8s.aws/ultraserver-id",
                ],
            )

            print(f"Command output: {result.output}")
            # self.assertEqual(result.exit_code, 0)
            self.assertIn("Using version: 1.1", result.output)

            mock_hyperpod_job.assert_called_once()
            call_args = mock_hyperpod_job.call_args[1]
            self.assertEqual(call_args["metadata"].name, "test-job")
            self.assertEqual(call_args["metadata"].namespace, "test-namespace")
            self.assertEqual(call_args["metadata"].labels["kueue.x-k8s.io/queue-name"], "localqueue")
            self.assertEqual(call_args["metadata"].annotations["kueue.x-k8s.io/podset-required-topology"], "topology.k8s.aws/ultraserver-id")

    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_list_jobs(self, mock_hyperpod_pytorch_job, mock_namespace_exists):
        """Test the list_jobs function"""
        mock_namespace_exists.return_value = True
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
        # Updated to match the new @handle_cli_exceptions() decorator behavior
        self.assertIn("Test error", result.output)

    @patch('sagemaker.hyperpod.common.cli_decorators._namespace_exists')
    @patch("sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob")
    def test_pytorch_describe(self, mock_hyperpod_pytorch_job, mock_namespace_exists):
        """Test the pytorch_describe function"""
        mock_namespace_exists.return_value = True
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
        self.assertIn("Test error", result.output)

    def test_valid_topology_label_cli(self):
        """Test CLI accepts valid topology labels."""

        for label in ALLOWED_TOPOLOGY_LABELS:
            # Test preferred-topology
            result = self.runner.invoke(pytorch_create, [
                '--job-name', f'test-job-{hash(label) % 1000}',  # Unique job names
                '--image', 'pytorch:latest',
                '--preferred-topology', label
            ])
            # Should not have validation errors (may fail later due to other reasons)
            self.assertNotIn('Topology label', result.output)
            self.assertNotIn('must be one of:', result.output)

            # Test required-topology
            result = self.runner.invoke(pytorch_create, [
                '--job-name', f'test-job-req-{hash(label) % 1000}',  # Unique job names
                '--image', 'pytorch:latest',
                '--required-topology', label
            ])
            # Should not have validation errors (may fail later due to other reasons)
            self.assertNotIn('Topology label', result.output)
            self.assertNotIn('must be one of:', result.output)

    def test_invalid_topology_label_cli(self):
        """Test CLI rejects invalid topology labels."""
        invalid_labels = [
            'invalid.label',
            'topology.k8s.aws/invalid-layer',
            'custom/topology-label'
        ]

        for label in invalid_labels:
            # Test preferred-topology-label
            result = self.runner.invoke(pytorch_create, [
                '--job-name', 'test-job',
                '--image', 'pytorch:latest',
                '--preferred-topology', label
            ])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('Topology label', result.output)
            self.assertIn('must be one of:', result.output)

            # Test required-topology
            result = self.runner.invoke(pytorch_create, [
                '--job-name', 'test-job',
                '--image', 'pytorch:latest',
                '--required-topology', label
            ])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn('Topology label', result.output)
            self.assertIn('must be one of:', result.output)

    def test_pytorch_exec_requires_job_name(self):
        """Test that pytorch_exec requires job-name"""
        result = self.runner.invoke(pytorch_exec, ['ls'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("job-name", result.output.lower())

    def test_pytorch_exec_requires_pod_or_all_pods(self):
        """Test that pytorch_exec requires either --pod or --all-pods"""
        result = self.runner.invoke(pytorch_exec, [
            '--job-name', 'test-job',
            'ls'
        ])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Must specify exactly one", result.output)

    @patch('sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob.get')
    def test_pytorch_exec_single_pod_success(self, mock_get):
        """Test successful pytorch_exec on single pod"""
        mock_job = Mock()
        mock_job.exec_command.return_value = "command output"
        mock_get.return_value = mock_job

        result = self.runner.invoke(pytorch_exec, [
            '--job-name', 'test-job',
            '--pod', 'test-pod',
            '--', 'ls', '-la'
        ])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("command output", result.output)
        mock_job.exec_command.assert_called_once_with(['ls', '-la'], 'test-pod', False, None)

    @patch('sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob.get')
    def test_pytorch_exec_error_handling(self, mock_get):
        """Test pytorch_exec error handling"""
        mock_job = Mock()
        mock_job.exec_command.side_effect = ValueError("Pod not found")
        mock_get.return_value = mock_job

        result = self.runner.invoke(pytorch_exec, [
            '--job-name', 'test-job',
            '--pod', 'nonexistent-pod',
            '--', 'ls'
        ])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Pod not found", result.output)


@unittest.skipUnless(PYDANTIC_AVAILABLE, "Pydantic model not available")
class TestValidationPatterns(unittest.TestCase):
    """Test cases for validation patterns added to PyTorchJobConfig"""

    def setUp(self):
        """Set up test fixtures"""
        self.valid_base_config = {
            "job_name": "test-job",
            "image": "pytorch:latest"
        }

    def test_job_name_validation_success(self):
        """Test successful job_name validation"""
        valid_names = [
            "test-job",
            "job123",
            "a",
            "my-training-job-123",
            "job-with-multiple-hyphens"
        ]
        
        for name in valid_names:
            with self.subTest(job_name=name):
                config = PyTorchJobConfig(job_name=name, image="pytorch:latest")
                self.assertEqual(config.job_name, name)

    def test_job_name_validation_failure(self):
        """Test job_name validation failures"""
        invalid_names = [
            "",  # Empty string
            "-invalid",  # Starts with hyphen
            "invalid-",  # Ends with hyphen
            "Invalid",  # Contains uppercase
            "job_with_underscore",  # Contains underscore
            "job.with.dots",  # Contains dots
            "job with spaces",  # Contains spaces
            "a" * 64,  # Too long (>63 characters)
        ]
        
        for name in invalid_names:
            with self.subTest(job_name=name):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(job_name=name, image="pytorch:latest")

    def test_image_validation_success(self):
        """Test successful image validation"""
        valid_images = [
            "pytorch:latest",
            "my-registry.com/pytorch:1.0",
            "ubuntu",
            "registry.k8s.io/pause:3.9"
        ]
        
        for image in valid_images:
            with self.subTest(image=image):
                config = PyTorchJobConfig(job_name="test-job", image=image)
                self.assertEqual(config.image, image)

    def test_image_validation_failure(self):
        """Test image validation failures"""
        # Note: Currently only minLength=1 is enforced for image field
        invalid_images = [
            "",  # Empty string
        ]
        
        for image in invalid_images:
            with self.subTest(image=image):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(job_name="test-job", image=image)

    def test_queue_name_validation_success(self):
        """Test successful queue_name validation"""
        valid_queue_names = [
            "training-queue",
            "queue123",
            "a",
            "my-queue-name",
            "queue-with-multiple-hyphens",
            "a" * 63,  # Exactly 63 characters
        ]
        
        for queue_name in valid_queue_names:
            with self.subTest(queue_name=queue_name):
                config = PyTorchJobConfig(
                    job_name="test-job", 
                    image="pytorch:latest", 
                    queue_name=queue_name
                )
                self.assertEqual(config.queue_name, queue_name)

    def test_queue_name_validation_failure(self):
        """Test queue_name validation failures"""
        invalid_queue_names = [
            "",  # Empty string
            "-invalid",  # Starts with hyphen
            "invalid-",  # Ends with hyphen
            "Invalid",  # Contains uppercase
            "queue_with_underscore",  # Contains underscore
            "queue.with.dots",  # Contains dots
            "queue with spaces",  # Contains spaces
            "a" * 64,  # Too long (>63 characters)
        ]
        
        for queue_name in invalid_queue_names:
            with self.subTest(queue_name=queue_name):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(
                        job_name="test-job", 
                        image="pytorch:latest", 
                        queue_name=queue_name
                    )

    def test_integer_field_validation_success(self):
        """Test successful integer field validation"""
        # Test node_count
        config = PyTorchJobConfig(
            job_name="test-job", 
            image="pytorch:latest", 
            node_count=5
        )
        self.assertEqual(config.node_count, 5)
        
        # Test tasks_per_node - should remain as "auto" when set to "auto"
        config = PyTorchJobConfig(
            job_name="test-job", 
            image="pytorch:latest", 
            tasks_per_node="auto"
        )
        self.assertEqual(config.tasks_per_node, "auto")
        
        # Test max_retry
        config = PyTorchJobConfig(
            job_name="test-job", 
            image="pytorch:latest", 
            max_retry=3
        )
        self.assertEqual(config.max_retry, 3)

    def test_integer_field_validation_failure(self):
        """Test integer field validation failures"""
        # Test node_count with invalid values
        invalid_node_counts = [0, -1, -10]
        for count in invalid_node_counts:
            with self.subTest(node_count=count):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(
                        job_name="test-job", 
                        image="pytorch:latest", 
                        node_count=count
                    )
        
        # Test tasks_per_node with invalid values
        invalid_tasks_per_node = [0, -1, -5]
        for tasks in invalid_tasks_per_node:
            with self.subTest(tasks_per_node=tasks):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(
                        job_name="test-job", 
                        image="pytorch:latest", 
                        tasks_per_node=tasks
                    )
        
        # Test max_retry with invalid values
        invalid_max_retry = [-1, -10]
        for retry in invalid_max_retry:
            with self.subTest(max_retry=retry):
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(
                        job_name="test-job", 
                        image="pytorch:latest", 
                        max_retry=retry
                    )

    def test_volume_validation_success(self):
        """Test successful volume validation"""
        # Test valid hostPath volume
        hostpath_volume = VolumeConfig(
            name="data",
            type="hostPath",
            mount_path="/data",
            path="/host/data"
        )
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            volume=[hostpath_volume]
        )
        self.assertEqual(len(config.volume), 1)
        self.assertEqual(config.volume[0].name, "data")
        
        # Test valid PVC volume
        pvc_volume = VolumeConfig(
            name="storage",
            type="pvc",
            mount_path="/storage",
            claim_name="my-pvc"
        )
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            volume=[pvc_volume]
        )
        self.assertEqual(len(config.volume), 1)
        self.assertEqual(config.volume[0].claim_name, "my-pvc")

    def test_volume_validation_failure(self):
        """Test volume validation failures"""
        # Test hostPath volume missing path
        with self.assertRaises(ValidationError):
            VolumeConfig(
                name="data",
                type="hostPath",
                mount_path="/data"
                # Missing path field
            )
        
        # Test PVC volume missing claim_name
        with self.assertRaises(ValidationError):
            VolumeConfig(
                name="storage",
                type="pvc",
                mount_path="/storage"
                # Missing claim_name field
            )
        
        # Test invalid mount path (not absolute)
        with self.assertRaises(ValidationError):
            VolumeConfig(
                name="data",
                type="hostPath",
                mount_path="data",  # Should start with /
                path="/host/data"
            )
        
        # Test invalid host path (not absolute)
        with self.assertRaises(ValidationError):
            VolumeConfig(
                name="data",
                type="hostPath",
                mount_path="/data",
                path="host/data"  # Should start with /
            )

    def test_volume_duplicate_validation(self):
        """Test volume duplicate name and mount path validation"""
        # Test duplicate volume names
        volume1 = VolumeConfig(
            name="data",
            type="hostPath",
            mount_path="/data1",
            path="/host/data1"
        )
        volume2 = VolumeConfig(
            name="data",  # Same name
            type="hostPath",
            mount_path="/data2",
            path="/host/data2"
        )
        
        with self.assertRaises(ValidationError) as cm:
            PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                volume=[volume1, volume2]
            )
        self.assertIn("Duplicate volume names found", str(cm.exception))
        
        # Test duplicate mount paths
        volume3 = VolumeConfig(
            name="data1",
            type="hostPath",
            mount_path="/data",  # Same mount path
            path="/host/data1"
        )
        volume4 = VolumeConfig(
            name="data2",
            type="hostPath",
            mount_path="/data",  # Same mount path
            path="/host/data2"
        )
        
        with self.assertRaises(ValidationError) as cm:
            PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                volume=[volume3, volume4]
            )
        self.assertIn("Duplicate mount paths found", str(cm.exception))

    def test_environment_variable_validation_success(self):
        """Test successful environment variable validation"""
        valid_env_vars = {
            "CUDA_VISIBLE_DEVICES": "0,1",
            "MY_VAR": "value",
            "_PRIVATE_VAR": "secret",
            "VAR123": "test",
            "a": "b"
        }
        
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            environment=valid_env_vars
        )
        self.assertEqual(config.environment, valid_env_vars)

    def test_environment_variable_validation_failure(self):
        """Test environment variable validation failures"""
        invalid_env_vars = [
            {"123INVALID": "value"},  # Starts with number
            {"INVALID-VAR": "value"},  # Contains hyphen
            {"INVALID.VAR": "value"},  # Contains dot
            {"INVALID VAR": "value"},  # Contains space
            {"": "value"},  # Empty name
        ]
        
        for env_var in invalid_env_vars:
            with self.subTest(env_var=env_var):
                with self.assertRaises(ValidationError) as cm:
                    PyTorchJobConfig(
                        job_name="test-job",
                        image="pytorch:latest",
                        environment=env_var
                    )
                self.assertIn("must be a valid C_IDENTIFIER", str(cm.exception))

    def test_label_selector_validation_success(self):
        """Test successful label selector validation"""
        valid_labels = {
            "accelerator": "nvidia",
            "network": "efa",
            "node-type": "gpu",
            "a": "b",
            "kubernetes.io/arch": "amd64",
            "example.com/custom-label": "value"
        }
        
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            label_selector=valid_labels
        )
        self.assertEqual(config.label_selector, valid_labels)

    def test_label_selector_validation_failure(self):
        """Test label selector validation failures"""
        invalid_labels = [
            {"-invalid": "value"},  # Starts with hyphen
            {"invalid-": "value"},  # Ends with hyphen
            {"invalid..key": "value"},  # Double dots
            {"": "value"},  # Empty key
            {" invalid": "value"},  # Starts with space
            {"invalid/": "value"},  # Ends with slash
            {"/invalid": "value"},  # Starts with slash
        ]
        
        for label in invalid_labels:
            with self.subTest(label=label):
                with self.assertRaises(ValidationError) as cm:
                    PyTorchJobConfig(
                        job_name="test-job",
                        image="pytorch:latest",
                        label_selector=label
                    )
                self.assertIn("must follow Kubernetes label naming conventions", str(cm.exception))

    def test_command_args_validation_success(self):
        """Test successful command and args validation"""
        valid_command = ["python", "train.py"]
        valid_args = ["--epochs", "10", "--batch-size", "32"]
        
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            command=valid_command,
            args=valid_args
        )
        self.assertEqual(config.command, valid_command)
        self.assertEqual(config.args, valid_args)

    def test_command_args_validation_failure(self):
        """Test command and args validation failures"""
        # Test empty strings in command
        with self.assertRaises(ValidationError) as cm:
            PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                command=["python", "", "train.py"]
            )
        self.assertIn("must be a non-empty string", str(cm.exception))
        
        # Test whitespace-only strings in args
        with self.assertRaises(ValidationError) as cm:
            PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                args=["--epochs", "   ", "--batch-size", "32"]
            )
        self.assertIn("must be a non-empty string", str(cm.exception))

    def test_string_field_min_length_validation(self):
        """Test minLength validation for string fields"""
        string_fields = [
            ("namespace", ""),
            ("pull_policy", ""),
            ("instance_type", ""),
            ("scheduler_type", ""),
            ("priority", ""),
            ("service_account_name", ""),
        ]
        
        for field_name, invalid_value in string_fields:
            with self.subTest(field=field_name):
                kwargs = {
                    "job_name": "test-job",
                    "image": "pytorch:latest",
                    field_name: invalid_value
                }
                with self.assertRaises(ValidationError):
                    PyTorchJobConfig(**kwargs)

    def test_comprehensive_valid_config(self):
        """Test a comprehensive valid configuration"""
        volume = VolumeConfig(
            name="data",
            type="hostPath",
            mount_path="/data",
            path="/host/data"
        )
        
        config = PyTorchJobConfig(
            job_name="my-training-job",
            image="pytorch:1.12.0",
            namespace="ml-team",
            command=["python", "train.py"],
            args=["--epochs", "100"],
            environment={"CUDA_VISIBLE_DEVICES": "0,1"},
            pull_policy="Always",
            instance_type="ml.p4d.24xlarge",
            node_count=2,
            tasks_per_node="auto",
            label_selector={"accelerator": "nvidia"},
            queue_name="training-queue",
            priority="high",
            max_retry=3,
            volume=[volume],
            service_account_name="training-sa"
        )
        
        # Verify all fields are set correctly
        self.assertEqual(config.job_name, "my-training-job")
        self.assertEqual(config.image, "pytorch:1.12.0")
        self.assertEqual(config.namespace, "ml-team")
        self.assertEqual(config.command, ["python", "train.py"])
        self.assertEqual(config.args, ["--epochs", "100"])
        self.assertEqual(config.environment, {"CUDA_VISIBLE_DEVICES": "0,1"})
        self.assertEqual(config.pull_policy, "Always")
        self.assertEqual(config.instance_type, "ml.p4d.24xlarge")
        self.assertEqual(config.node_count, 2)
        self.assertEqual(config.tasks_per_node, "auto") # Should remain as "auto"
        self.assertEqual(config.label_selector, {"accelerator": "nvidia"})
        self.assertEqual(config.queue_name, "training-queue")
        self.assertEqual(config.priority, "high")
        self.assertEqual(config.max_retry, 3)
        self.assertEqual(len(config.volume), 1)
        self.assertEqual(config.service_account_name, "training-sa")

    def test_valid_topology_labels(self):
        """Test that valid topology labels are accepted."""

        for label in ALLOWED_TOPOLOGY_LABELS:
            config = PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                preferred_topology=label
            )
            self.assertEqual(config.preferred_topology, label)

            config = PyTorchJobConfig(
                job_name="test-job",
                image="pytorch:latest",
                required_topology=label
            )
            self.assertEqual(config.required_topology, label)

    def test_invalid_topology_labels(self):
        """Test that invalid topology labels are rejected."""
        invalid_labels = [
            'invalid.label',
            'topology.k8s.aws/invalid-layer',
            'custom/topology-label'
        ]

        for label in invalid_labels:
            with self.assertRaises(ValueError):
                PyTorchJobConfig(
                    job_name="test-job",
                    image="pytorch:latest",
                    preferred_topology=label
                )

            with self.assertRaises(ValueError):
                PyTorchJobConfig(
                    job_name="test-job",
                    image="pytorch:latest",
                    required_topology=label
                )

    def test_none_topology_labels(self):
        """Test that None topology labels are accepted."""
        config = PyTorchJobConfig(
            job_name="test-job",
            image="pytorch:latest",
            preferred_topology=None,
            required_topology=None
        )
        self.assertIsNone(config.preferred_topology)
        self.assertIsNone(config.required_topology)

@patch('sagemaker.hyperpod.cli.commands.training.HyperPodPytorchJob')
def test_pytorch_get_operator_logs(mock_hp):
    mock_hp.get_operator_logs.return_value = "operator logs"
    runner = CliRunner()
    result = runner.invoke(pytorch_get_operator_logs, ['--since-hours', '2'])
    assert result.exit_code == 0
    assert 'operator logs' in result.output
    mock_hp.get_operator_logs.assert_called_once_with(since_hours=2.0)
