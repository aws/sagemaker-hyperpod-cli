import unittest
from unittest.mock import patch

from hyperpod_cli.validators.job_validator import JobValidator


class TestJobValidator(unittest.TestCase):
    def setUp(self):
        self.validator = JobValidator()

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_job_kind_invalid(self, mock_logger):
        config_name = None
        name = None
        node_count = None
        instance_type = None
        image = None
        job_kind = "invalid-job-kind"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "The only supported 'job-kind' is 'kubeflow/PyTorchJob'."
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_command_invalid(self, mock_logger):
        config_name = None
        name = None
        node_count = None
        instance_type = None
        image = None
        job_kind = "kubeflow/PyTorchJob"
        command = "python"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with("The only supported 'command' is 'torchrun'.")

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_both_config_name_and_name_provided(self, mock_logger):
        config_name = "config.yaml"
        name = "job-name"
        node_count = None
        instance_type = None
        image = None
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide only 'config-name' to submit job using config file or 'name' to submit job via CLI arguments"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_neither_config_name_nor_name_provided(self, mock_logger):
        config_name = None
        name = None
        node_count = None
        instance_type = None
        image = None
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide either 'config-name' to submit job using config file or 'name' to submit job via CLI arguments"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_name_provided_but_node_count_missing(self, mock_logger):
        config_name = None
        name = "job-name"
        node_count = None
        instance_type = "ml.p3.2xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'node-count' to specify number of nodes used for training job"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_name_provided_but_instance_type_missing(self, mock_logger):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = None
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'instance-type' to specify instance type for training job"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_name_provided_but_invalid_instance_type(self, mock_logger):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "invalid-instance-type"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide SageMaker HyperPod supported 'instance-type'"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_submit_job_args_name_provided_but_image_missing(self, mock_logger):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = None
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'image' to specify the training image for training job"
        )

    def test_validate_submit_job_args_valid_args(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1": "value1"}'

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertTrue(result)

    def test_validate_submit_job_args_invalid_json_label_selector(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = "{jiovneao"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_invalid_values_label_selector(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1":{"key2": "value1"}}'

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_invalid_values_type_label_selector(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1":[{"key2": "value2"}]}'

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_invalid_key_label_selector(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1": ["value1", {"key2": "value2"}]}'

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    @patch("json.loads")
    def test_validate_submit_job_args_label_selector_unexpected_error(self, mock_json):
        mock_json.side_effect = Exception("test error")
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = "{jiovneao"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_wrong_scheduler_type(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            "UnsupportedScheduler",
            None,
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_kueue_fields_error(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            "Kueue",
            "queue_name_without_priority",
            None,
            False,
            None,
        )

        self.assertFalse(result)

    def test_validate_submit_job_args_auto_resume_restart_policy_unexpected(self):
        config_name = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_submit_job_args(
            config_name,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            None,
            None,
            None,
            True,
            "Never",
        )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
