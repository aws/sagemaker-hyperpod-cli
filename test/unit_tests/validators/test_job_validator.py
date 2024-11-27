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
import unittest
from unittest.mock import patch, mock_open, MagicMock
from unittest import mock

from hyperpod_cli.constants.command_constants import (
    RestartPolicy,
    SchedulerType,
)
from hyperpod_cli.validators.job_validator import (
    JobValidator,
    verify_and_load_yaml,
    validate_yaml_content,
    validate_hyperpod_related_fields,
)


class TestJobValidator(unittest.TestCase):
    def setUp(self):
        self.validator = JobValidator()

    def test_validate_start_job_args_job_valid(
        self,
    ):
        name = "test-job"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertTrue(result)

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_job_kind_invalid(self, mock_logger):
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "invalid-job-kind"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "The only supported 'job-kind' is 'kubeflow/PyTorchJob'."
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_command_invalid(self, mock_logger):
        config_file = None
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "python"
        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "The only supported 'command' is 'torchrun'."
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_both_config_file_and_job_name_provided(
        self, mock_logger
    ):
        config_file = "config.yaml"
        name = "job-name"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide only 'config-file' to submit job using custom script or 'job-name' to submit job via CLI arguments"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_neither_config_file_nor_name_provided(
        self, mock_logger
    ):
        config_file = None
        name = None
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide either 'recipe' for recipe-based jobs or 'config-file' to submit job using config file or 'job-name' to submit job via CLI arguments"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_name_provided_but_node_count_missing(
        self, mock_logger
    ):
        config_file = None
        name = "job-name"
        node_count = None
        instance_type = "ml.p3.2xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'node-count' to specify number of nodes used for training job"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_name_provided_but_instance_type_missing(
        self, mock_logger
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = None
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'instance-type' to specify instance type for training job"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_name_provided_but_entry_script_missing(
        self, mock_logger
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.g5.xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            None,
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'entry-script' for the training job"
        )

    def test_validate_start_job_args_auto_resume_in_namespace_with_aws_hyperpod_prefix(
        self,
    ):
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        auto_resume = True
        restart_policy = "OnFailure"
        max_retry = 1

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            auto_resume,
            restart_policy,
            max_retry,
            "hyperpod-1",
            "/opt/train/src/train.py",
            None,
        )

        self.assertTrue(result)

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_auto_resume_in_any_namespace(self, mock_logger):
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        auto_resume = True
        restart_policy = "OnFailure"
        max_retry = 1

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            auto_resume,
            restart_policy,
            max_retry,
            "any-hyperpod",
            "/opt/train/src/train.py",
            None,
        )

        self.assertTrue(result)

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_no_auto_resume_has_max_retry(self, mock_logger):
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        restart_policy = "OnFailure"
        max_retry = 1

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            None,
            restart_policy,
            max_retry,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please enable 'auto_resume' with 'max_retry' option."
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_auto_resume_wrong_restart_policy(
        self, mock_logger
    ):
        name = "test-job"
        node_count = 1
        instance_type = "ml.p4d.24xlarge"
        image = "image"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        auto_resume = True
        restart_policy = "Always"
        max_retry = 1

        result = self.validator.validate_start_job_args(
            None,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            auto_resume,
            restart_policy,
            max_retry,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "To enable 'auto_resume', please ensure the 'restart-policy' is 'OnFailure'. "
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_name_provided_but_invalid_instance_type(
        self, mock_logger
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "invalid-instance-type"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide SageMaker HyperPod supported 'instance-type'"
        )

    @patch("hyperpod_cli.validators.job_validator.logger")
    def test_validate_start_job_args_name_provided_but_image_missing(self, mock_logger):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = None
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)
        mock_logger.error.assert_called_once_with(
            "Please provide 'image' to specify the training image for training job"
        )

    def test_validate_start_job_args_valid_args(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1": "value1"}'

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertTrue(result)

    def test_validate_start_job_args_invalid_json_label_selector(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = "{jiovneao"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    def test_validate_start_job_args_invalid_values_label_selector(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1":{"key2": "value1"}}'

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    def test_validate_start_job_args_invalid_values_type_label_selector(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1":[{"key2": "value2"}]}'

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    def test_validate_start_job_args_invalid_key_label_selector(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = '{"key1": ["value1", {"key2": "value2"}]}'

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    @patch("json.loads")
    def test_validate_start_job_args_label_selector_unexpected_error(self, mock_json):
        mock_json.side_effect = Exception("test error")
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"
        label_selector = "{jiovneao"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            label_selector,
            None,
            SchedulerType.KUEUE.value,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    def test_validate_start_job_args_wrong_scheduler_type(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
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
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    def test_validate_start_job_args_kueue_fields_error(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
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
            None,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertTrue(result)

    def test_validate_start_job_args_auto_resume_restart_policy_unexpected(
        self,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.KUEUE.value,
            None,
            None,
            True,
            "Never",
            1,
            "kubeflow",
            "/opt/train/src/train.py",
            None,
        )

        self.assertFalse(result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.get_sagemaker_managed_namespace")
    def test_validate_start_job_args_sagemaker_scheduler_success(
        self,
        mock_get_sagemaker_managed_namespace,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        mock_get_sagemaker_managed_namespace.return_value = "kubeflow"

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.SAGEMAKER.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
        )

        self.assertTrue(result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.get_sagemaker_managed_namespace")
    def test_validate_start_job_args_sagemaker_scheduler_invalid_namespace(
        self,
        mock_get_sagemaker_managed_namespace,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        mock_get_sagemaker_managed_namespace.return_value = None

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.SAGEMAKER.value,
            None,
            None,
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
        )

        self.assertFalse(result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.list_workload_priority_classes")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.get_sagemaker_managed_namespace")
    def test_validate_start_job_args_sagemaker_scheduler_success_with_priority(
        self,
        mock_get_sagemaker_managed_namespace,
        mock_list_workload_priority_classes,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        mock_get_sagemaker_managed_namespace.return_value = "kubeflow"
        mock_list_workload_priority_classes.return_value = {
            'items': [
                {'metadata': {'name': 'high-priority'}},
                {'metadata': {'name': 'medium-priority'}},
                {'metadata': {'name': 'test-priority'}}
            ]
        }

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.SAGEMAKER.value,
            None,
            "test-priority",
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
        )

        self.assertTrue(result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.list_workload_priority_classes")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.get_sagemaker_managed_namespace")
    def test_validate_start_job_args_sagemaker_scheduler_fail_priority_not_exist(
        self,
        mock_get_sagemaker_managed_namespace,
        mock_list_workload_priority_classes,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        mock_get_sagemaker_managed_namespace.return_value = "kubeflow"
        mock_list_workload_priority_classes.return_value = {
            'items': [
                {'metadata': {'name': 'high-priority'}},
                {'metadata': {'name': 'medium-priority'}},
            ]
        }

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.SAGEMAKER.value,
            None,
            "test-priority",
            False,
            None,
            None,
            "kubeflow",
            "/opt/train/src/train.py",
        )

        self.assertFalse(result)
    
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.list_workload_priority_classes")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.get_sagemaker_managed_namespace")
    def test_validate_start_job_args_sagemaker_scheduler_no_namespace(
        self,
        mock_get_sagemaker_managed_namespace,
        mock_list_workload_priority_classes,
    ):
        config_file = None
        name = "job-name"
        node_count = "2"
        instance_type = "ml.p4d.24xlarge"
        image = "my-image:latest"
        job_kind = "kubeflow/PyTorchJob"
        command = "torchrun"

        mock_get_sagemaker_managed_namespace.return_value = "kubeflow"
        mock_list_workload_priority_classes.return_value = {
            'items': [
                {'metadata': {'name': 'high-priority'}},
                {'metadata': {'name': 'medium-priority'}},
            ]
        }

        result = self.validator.validate_start_job_args(
            config_file,
            name,
            node_count,
            instance_type,
            image,
            job_kind,
            command,
            None,
            SchedulerType.SAGEMAKER.value,
            None,
            "test-priority",
            False,
            None,
            None,
            None,
            "/opt/train/src/train.py",
        )

        self.assertFalse(result)

    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        mock_open(read_data="cluster:\n  cluster_type: k8s\n  cluster_config: {}"),
    )
    def test_verify_and_load_yaml_valid(self, mock_exists):
        result = verify_and_load_yaml("test.yaml")
        self.assertEqual(
            result,
            {
                "cluster": {
                    "cluster_type": "k8s",
                    "cluster_config": {},
                }
            },
        )

    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        mock_open(read_data="{invalid yaml"),
    )
    def test_verify_and_load_yaml_invalid(self, mock_exists):
        result = verify_and_load_yaml("test.yaml")
        self.assertIsNone(result)
    
    @patch("os.path.exists", return_value=False)
    @patch(
        "builtins.open",
        mock_open(read_data="cluster:\n  cluster_type: k8s\n  cluster_config: {}"),
    )
    def test_verify_and_load_yaml_not_exist(self, mock_exists):
        result = verify_and_load_yaml("test.yaml")
        self.assertFalse(result)

    def test_validate_yaml_content_valid(self):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    def test_validate_yaml_content_error_no_cluster(
        self,
    ):
        mock_data = {"invalid": "invalid"}
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    def test_validate_yaml_content_error_invalid_cluster_type(
        self,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "slurm",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    def test_validate_yaml_content_error_no_cluster_config(
        self,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    def test_validate_yaml_content_valid_with_queue_name_and_priority(
        self,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "custom_labels": {"kueue.x-k8s.io/queue-name": "test"},
                    "priority_class_name": "high-priority",
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_valid_with_auto_resume(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "kubeflow",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_valid_with_auto_resume_in_aws_hyperpod_namespace(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "hyperpod",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_valid_with_auto_resume_default_namespace(    
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "default",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_valid_with_auto_resume_any_hyperpod_namespace(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "any-namespace",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertTrue(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_error_only_auto_resume_no_max_retry(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "kubeflow",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_error_with_wrong_restart_policy(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "kubeflow",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "Always",
                    "annotations": {
                        "sagemaker.amazonaws.com/enable-job-auto-resume": True,
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    @patch(
        "hyperpod_cli.validators.job_validator.validate_scheduler_related_fields",
        return_value=True,
    )
    def test_validate_yaml_content_error_only_max_retry(
        self,
        mock_validate_scheduler_related_fields,
    ):
        mock_data = {
            "cluster": {
                "cluster_type": "k8s",
                "instance_type": "ml.g5.xlarge",
                "cluster_config": {
                    "namespace": "kubeflow",
                    "pullPolicy": "IfNotPresent",
                    "restartPolicy": "OnFailure",
                    "annotations": {
                        "sagemaker.amazonaws.com/job-max-retry-count": 3,
                    },
                },
            }
        }
        result = validate_yaml_content(mock_data)
        self.assertFalse(result)

    def test_validate_hyperpod_related_fields_valid(
        self,
    ):
        result = validate_hyperpod_related_fields(
            instance_type="ml.g5.xlarge",
            queue_name="test-queue",
            priority="high-priority",
            auto_resume=False,
            restart_policy=RestartPolicy.NEVER.value,
            max_retry=None,
            namespace="kubeflow",
        )
        self.assertTrue(result)

    def test_validate_hyperpod_related_fields_invalid_instance_type(
        self,
    ):
        result = validate_hyperpod_related_fields(
            instance_type="invalid-instance-type",
            queue_name="test-queue",
            priority="high-priority",
            auto_resume=False,
            restart_policy=RestartPolicy.NEVER.value,
            max_retry=None,
            namespace="kubeflow",
        )
        self.assertFalse(result)

    def test_validate_hyperpod_related_fields_invalid_auto_resume(
        self,
    ):
        result = validate_hyperpod_related_fields(
            instance_type="ml.g5.xlarge",
            queue_name="test-queue",
            priority="high-priority",
            auto_resume=True,
            restart_policy=RestartPolicy.NEVER.value,
            max_retry=1,
            namespace="kubeflow",
        )
        self.assertFalse(result)

    def test_validate_hyperpod_related_fields_invalid_max_retry(
        self,
    ):
        result = validate_hyperpod_related_fields(
            instance_type="ml.g5.xlarge",
            queue_name="test-queue",
            priority="high-priority",
            auto_resume=False,
            restart_policy=RestartPolicy.ON_FAILURE.value,
            max_retry=1,
            namespace="kubeflow",
        )
        self.assertFalse(result)


if __name__== "__main__":
    unittest.main()
