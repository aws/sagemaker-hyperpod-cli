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
import json
import unittest
import click
import subprocess
import pytest
import os
import yaml
from unittest import mock
from unittest.mock import MagicMock, mock_open

from click.testing import CliRunner
from kubernetes.client import (
    V1Namespace, 
    V1ObjectMeta,
)
from hyperpod_cli.commands.job import (
    cancel_job,
    get_job,
    list_jobs,
    list_pods,
    patch_job,
    start_job,
    suppress_standard_output_context,
    validate_only_config_file_argument,
)
from hyperpod_cli.service.cancel_training_job import (
    CancelTrainingJob,
)
from hyperpod_cli.service.get_training_job import (
    GetTrainingJob,
)
from hyperpod_cli.service.list_pods import (
    ListPods,
)
from hyperpod_cli.service.list_training_jobs import (
    ListTrainingJobs,
)

VALID_CONFIG_FILE_DATA = "cluster:\n  cluster_type: k8s\n  instance_type: ml.g5.xlarge\n  cluster_config: {pullPolicy: IfNotPresent}"


class JobTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_cancel_job = MagicMock(spec=CancelTrainingJob)
        self.mock_get_job = MagicMock(spec=GetTrainingJob)
        self.mock_list_jobs = MagicMock(spec=ListTrainingJobs)
        self.list_pods = MagicMock(spec=ListPods)

        # Patch gettext for now because see some issues locally for localization
        mock.patch("gettext.dgettext", lambda domain, message: message).start()
        
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob")
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob.get_training_job")
    def test_get_job_happy_case(
        self,
        mock_get_training_job_service_and_get_job: mock.Mock,
        mock_get_training_job_service: mock.Mock,
    ):
        mock_get_training_job_service.return_value = self.mock_get_job
        mock_get_training_job_service_and_get_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(get_job, ["--job-name", "example-job"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob")
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob.get_training_job")
    @mock.patch("logging.Logger.debug")
    def test_get_job_happy_case_debug_mode(
        self,
        mock_debug,
        mock_get_training_job_service_and_get_job: mock.Mock,
        mock_get_training_job_service: mock.Mock,
    ):
        mock_get_training_job_service.return_value = self.mock_get_job
        mock_get_training_job_service_and_get_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(get_job, ["--job-name", "example-job"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob")
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob.get_training_job")
    def test_get_job_happy_case_with_namespace(
        self,
        mock_get_training_job_service_and_get_job: mock.Mock,
        mock_get_training_job_service: mock.Mock,
    ):
        mock_get_training_job_service.return_value = self.mock_get_job
        mock_get_training_job_service_and_get_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(
            get_job,
            [
                "--job-name",
                "example-job",
                "--namespace",
                "kubeflow",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob")
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob.get_training_job")
    def test_get_job_happy_case_with_namespace_and_verbose(
        self,
        mock_get_training_job_service_and_get_job: mock.Mock,
        mock_get_training_job_service: mock.Mock,
    ):
        mock_get_training_job_service.return_value = self.mock_get_job
        mock_get_training_job_service_and_get_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(
            get_job,
            [
                "--job-name",
                "example-job",
                "--namespace",
                "kubeflow",
                "--verbose",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob")
    @mock.patch("hyperpod_cli.service.get_training_job.GetTrainingJob.get_training_job")
    def test_get_job_when_subprocess_command_gives_exception(
        self,
        mock_get_training_job_service_and_get_job: mock.Mock,
        mock_get_training_job_service: mock.Mock,
    ):
        mock_get_training_job_service.return_value = self.mock_get_job
        mock_get_training_job_service_and_get_job.side_effect = Exception("Boom!")
        result = self.runner.invoke(get_job, ["--job-name", "example-job"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to get training job",
            result.output,
        )

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_happy_case(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": []})
        result = self.runner.invoke(list_jobs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    @mock.patch("logging.Logger.debug")
    def test_list_job_happy_case_debug_mode(
        self,
        mock_debug,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": []})
        result = self.runner.invoke(list_jobs, ["--debug"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    @mock.patch("logging.Logger.debug")
    def test_list_job_happy_case_default_output_mode_json(
        self,
        mock_debug,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": [{
            "Name": "test-job-name",
            "Namespace": "test_namespace",
            "CreationTime": "2025-01-01T01:01:01Z",
            "State": "Succeeded"
        }]})
        result = self.runner.invoke(list_jobs, ["--output", "json"])
        self.assertEqual(result.exit_code, 0)
        print(result.output)
        expected_output = '{\n    "jobs": [\n        {\n            "Name": "test-job-name",\n            "Namespace": "test_namespace",\n            "CreationTime": "2025-01-01T01:01:01Z",\n            "State": "Succeeded"\n        }\n    ]\n}\n'
        self.assertEqual(expected_output, result.output)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    @mock.patch("logging.Logger.debug")
    def test_list_job_happy_case_default_output_mode_table(
        self,
        mock_debug,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": [{
            "Name": "test-job-name",
            "Namespace": "test_namespace",
            "CreationTime": "2025-01-01T01:01:01Z",
            "State": "Succeeded"
        }]})
        result = self.runner.invoke(list_jobs, ["--output", "table"])
        self.assertEqual(result.exit_code, 0)
        print(result.output)
        expected_output = ' Name          | Namespace      | CreationTime         | State\n---------------+----------------+----------------------+-----------\n test-job-name | test_namespace | 2025-01-01T01:01:01Z | Succeeded\n'
        self.assertEqual(expected_output, result.output)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_happy_case_with_namespace(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": []})
        result = self.runner.invoke(list_jobs, ["--namespace", "kubeflow"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_happy_case_with_all_namespace(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({'jobs': []})
        result = self.runner.invoke(list_jobs, ["-A"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_happy_case_with_all_namespace_and_selector(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = json.dumps({"jobs": []})
        result = self.runner.invoke(list_jobs, ["-A", "-l", "test=test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_happy_case_with_bad_field(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.return_value = "{}"
        result = self.runner.invoke(list_jobs, ["--job-name", "kubeflow"])
        self.assertEqual(result.exit_code, 2)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch(
        "hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs"
    )
    def test_list_job_when_subprocess_command_gives_exception(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.mock_list_jobs
        mock_list_training_job_service_and_list_jobs.side_effect = Exception("Boom!")
        result = self.runner.invoke(list_jobs)
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to list training job",
            result.output,
        )

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_happy_case(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.list_pods
        mock_list_training_job_service_and_list_jobs.return_value = "{}"
        result = self.runner.invoke(
            list_pods,
            ["--job-name", "example-job"],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    @mock.patch("logging.Logger.debug")
    def test_list_pods_happy_case_debug_mode(
        self,
        mock_debug,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.list_pods
        mock_list_training_job_service_and_list_jobs.return_value = "{}"
        result = self.runner.invoke(
            list_pods,
            [
                "--job-name",
                "example-job",
                "--debug",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_happy_case_with_namespace(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.list_pods
        mock_list_training_job_service_and_list_jobs.return_value = "{}"
        result = self.runner.invoke(
            list_pods,
            [
                "--job-name",
                "example-job",
                "--namespace",
                "kubeflow",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    def test_list_pods_error_missing_name_option(
        self,
    ):
        result = self.runner.invoke(list_pods, ["example-job"])
        self.assertEqual(2, result.exit_code)
        self.assertIn(
            "Missing option '--job-name'",
            result.output,
        )

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_when_subprocess_command_gives_exception(
        self,
        mock_list_training_job_service_and_list_jobs: mock.Mock,
        mock_list_training_job_service: mock.Mock,
    ):
        mock_list_training_job_service.return_value = self.list_pods
        mock_list_training_job_service_and_list_jobs.side_effect = Exception("Boom!")
        result = self.runner.invoke(
            list_pods,
            ["--job-name", "example-job"],
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to list pods for training job",
            result.output,
        )

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job"
    )
    def test_cancel_job_happy_case(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.return_value = "{}"
        result = self.runner.invoke(
            cancel_job,
            ["--job-name", "example-job"],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("{}\n", result.output)

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job"
    )
    @mock.patch("logging.Logger.debug")
    def test_cancel_job_happy_case_debug_mode(
        self,
        mock_debug,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.return_value = "{}"
        result = self.runner.invoke(
            cancel_job,
            [
                "--job-name",
                "example-job",
                "--debug",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("{}\n", result.output)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job"
    )
    def test_cancel_job_happy_case_with_namespace(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.return_value = "{}"
        result = self.runner.invoke(
            cancel_job,
            [
                "--job-name",
                "example-job",
                "--namespace",
                "kubeflow",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("{}\n", result.output)

    def test_cancel_job_error_missing_name_option(
        self,
    ):
        result = self.runner.invoke(cancel_job, ["example-job"])
        self.assertIn(
            "Missing option '--job-name'",
            result.output,
        )

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job"
    )
    def test_cancel_job_when_subprocess_command_gives_exception(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.side_effect = Exception("Boom!")
        result = self.runner.invoke(
            cancel_job,
            ["--job-name", "example-job"],
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to cancel training job",
            result.output,
        )

    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
            catch_exceptions=False
        )
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
        self.assertEqual(result.exit_code, 0)

    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_namespace(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--namespace",
                "hyperpod-test",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("logging.Logger.debug")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_debug_mode(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_debug,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--debug",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        mock_debug.assert_called()

    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_gpu(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.g5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_custom_label_selection(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                '{"key1": "value1", "key2": "value2"}',
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("yaml.dump")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_label_selection_not_json_str(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_yaml_dump,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_yaml_dump.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                "{NonJsonStr",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("yaml.dump")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_label_selection_invalid_values(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_yaml_dump,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_yaml_dump.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                '{"key1": "value1", "key2": {"key3": "value2"}}',
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.job.validate_yaml_content")
    @mock.patch("hyperpod_cli.commands.job.verify_and_load_yaml")
    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_config_file(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
        mock_verify_and_load_yaml,
        mock_validate_yaml_content,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_verify_and_load_yaml.return_value = yaml.safe_load(VALID_CONFIG_FILE_DATA)
        mock_validate_yaml_content.return_value = True

        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            ["--config-file", "file.yaml"],
            catch_exceptions=False,
        )
        print(result.exception)
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.validate_yaml_content")
    @mock.patch("hyperpod_cli.commands.job.verify_and_load_yaml")
    @mock.patch('subprocess.run')
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_config_file_absolute_path(
        self,
        mock_boto,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_dump,
        mock_subprocess_run,
        mock_verify_and_load_yaml,
        mock_validate_yaml_content,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_verify_and_load_yaml.return_value = yaml.dump(VALID_CONFIG_FILE_DATA)
        mock_validate_yaml_content.return_value = True

        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--config-file",
                "/absolute/path/to/file.yaml",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("yaml.safe_load")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_invalid_template(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_yaml_load,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_yaml_load.return_value = {"invalid": "dict"}
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_aws_credentials_error(
        self,
        mock_boto3,
        mock_validator_cls,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = False
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("os.path.isabs", return_value=True)
    @mock.patch(
        "os.path.split",
        return_value=(
            "/absolute/path/to",
            "file.yaml",
        ),
    )
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_invalid_config_file_path(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_split,
        mock_isabs,
        mock_kubernetes_client,
        mock_exists,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        result = self.runner.invoke(
            start_job,
            [
                "--config-file",
                "/absolute/path/to/file.yaml",
            ],
        )
        self.assertNotEqual(result.exit_code, 0)

    @mock.patch("os.path.exists")
    @mock.patch("os.path.join")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("os.path.isabs", return_value=True)
    @mock.patch(
        "os.path.split",
        return_value=(
            "/absolute/path/to",
            "file.yaml",
        ),
    )
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_invalid_config_file(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_split,
        mock_isabs,
        mock_kubernetes_client,
        mock_join,
        mock_exists,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_join.return_value = "/path/to/config/invalid.yaml"
        mock_exists.side_effect = lambda path: path != "/path/to/config/invalid.yaml"
        result = self.runner.invoke(
            start_job,
            [
                "--config-file",
                "/absolute/path/to/file.yaml",
            ],
        )
        self.assertNotEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_command_failed(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=1,           # Simulate a failed command
            stdout='Command failed',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch(
        "hyperpod_cli.validators.job_validator.JobValidator.validate_start_job_args",
        return_value=False,
    )
    def test_start_job_with_invalid_args(self, mock_validate):
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "invalid-type",
                "--image",
                "invalid-image",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_auto_resume_enabled(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--auto-resume",
                "True",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_deep_health_check_passed_nodes_only(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--deep-health-check-passed-nodes-only",
                "True",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_kueue(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--queue-name",
                "test-priority-queue",
                "--priority",
                "high-priority",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_kueue_invalid(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_validator.validate_start_job_args.return_value = False
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=1,           # Simulate a failed command
            stdout='Command failed',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--queue-name",
                "test-priority-queue",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_service_account(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--service-account-name",
                "test-account-service",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_persistent_volume_claims(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--persistent-volume-claims",
                "claim1:test1,claim2:test2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_with_local_volume(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--persistent-volume-claims",
                "claim1:test1,claim2:test2",
                "--entry-script",
                "/opt/train/src/train.py",
                "--volumes",
                "data:/data:/data",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_namespace_auto_discover(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_discover_accessible_namespace,
        mock_get_cluster_console_url,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = None
        mock_discover_accessible_namespace.return_value = "discovered_namespace"
        mock_get_cluster_console_url.return_value = "test-console-link"

        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
            catch_exceptions=False
        )

        call_args_list = mock_yaml_dump.call_args_list
        args, kwargs = call_args_list[0]

        # Verify that namespace is filled with auto-discovered one
        self.assertIn("'namespace': 'discovered_namespace'", str(args[0]))
        self.assertEqual(result.exit_code, 0)
    
    @mock.patch('subprocess.run')
    @mock.patch("hyperpod_cli.commands.job._get_auto_fill_queue_name")
    @mock.patch("hyperpod_cli.commands.job.validate_yaml_content")
    @mock.patch("hyperpod_cli.commands.job.verify_and_load_yaml")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_namespace_auto_fill_queue_name(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_discover_accessible_namespace,
        mock_get_cluster_console_url,
        mock_verify_and_load_yaml,
        mock_validate_yaml_content,
        mock_auto_fill_queue_name,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_discover_accessible_namespace.return_value = "test-namespace"
        mock_get_cluster_console_url.return_value = "test-console-link"
        mock_verify_and_load_yaml.return_value = yaml.safe_load(VALID_CONFIG_FILE_DATA)
        mock_validate_yaml_content.return_value = True
        mock_auto_fill_queue_name.return_value = "test-queue"

        sm_managed_ns = V1Namespace(
            metadata=V1ObjectMeta(
                name="test-namespace",
                labels={
                    "sagemaker.amazonaws.com/sagemaker-managed-queue": "true",
                    "sagemaker.amazonaws.com/quota-allocation-id": "test-team",
                },
            ),
        )
        mock_kubernetes_client().get_sagemaker_managed_namespace.return_value = sm_managed_ns

        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
            ],
            catch_exceptions=False
        )

        call_args_list = mock_yaml_dump.call_args_list
        args, kwargs = call_args_list[0]

        # Verify that the queue name is filled with SageMaker managed local queue
        self.assertIn("'kueue.x-k8s.io/queue-name': 'test-queue'", str(args[0]))
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_cli_args_namespace_with_priority(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_discover_accessible_namespace,
        mock_get_cluster_console_url,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_discover_accessible_namespace.return_value = "test-namespace"
        mock_get_cluster_console_url.return_value = "test-console-link"
        sm_managed_ns = V1Namespace(
            metadata=V1ObjectMeta(
                name="test-namespace",
                labels={
                    "sagemaker.amazonaws.com/sagemaker-managed-queue": "true",
                    "sagemaker.amazonaws.com/quota-allocation-id": "test-team",
                },
            ),
        )
        mock_kubernetes_client().get_sagemaker_managed_namespace.return_value = sm_managed_ns

        result = self.runner.invoke(
            start_job,
            [
                "--job-name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--entry-script",
                "/opt/train/src/train.py",
                "--priority",
                "test-priority"
            ],
            catch_exceptions=False
        )

        call_args_list = mock_yaml_dump.call_args_list
        args, kwargs = call_args_list[0]

        # Verify that priority is passed correctly as a custom label
        self.assertIn("'kueue.x-k8s.io/priority-class': 'test-priority'", str(args[0]))
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    def test_patch_job_with_namespace_success(self, mock_discover_accessible_namespace, mock_kubernetes_client):
        mock_client = MagicMock()
        mock_kubernetes_client.return_value = mock_client
        mock_client.get_job.return_value = {
            "metadata": {
                "uid": "test-job-uid"
            }
        }
        mock_client.get_workload_by_label.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "test-workload-name"
                    }
                }
            ]
        }
        result = self.runner.invoke(
            patch_job,
            [
                "suspend",
                "--job-name",
                "test-job",
                "--namespace",
                "test-namespace",
            ],
            catch_exceptions=False,
        )

        mock_client.patch_workload.assert_called_once()
        call_args_list = mock_client.patch_workload.call_args_list
        args, kwargs = call_args_list[0]

        self.assertEqual(("test-workload-name", "test-namespace", {'spec': {'active': False}}), args)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    def test_patch_job_unsupported_patch_type(self, mock_discover_accessible_namespace, mock_kubernetes_client):
        mock_client = MagicMock()
        mock_kubernetes_client.return_value = mock_client
        mock_client.get_job.return_value = {
            "metadata": {
                "uid": "test-job-uid"
            }
        }
        mock_client.get_workload_by_label.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "test-workload-name"
                    }
                }
            ]
        }
        result = self.runner.invoke(
            patch_job,
            [
                "unsupported_type",
                "--job-name",
                "test-job",
                "--namespace",
                "test-namespace",
            ],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    def test_patch_job_invalid_number_workloads(self, mock_discover_accessible_namespace, mock_kubernetes_client):
        mock_client = MagicMock()
        mock_kubernetes_client.return_value = mock_client
        mock_client.get_job.return_value = {
            "metadata": {
                "uid": "test-job-uid"
            }
        }
        mock_client.get_workload_by_label.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "test-workload-name-1"
                    }
                },
                {
                    "metadata": {
                        "name": "test-workload-name-2"
                    }
                }
            ]
        }
        result = self.runner.invoke(
            patch_job,
            [
                "suspend",
                "--job-name",
                "test-job",
                "--namespace",
                "test-namespace",
            ],
            catch_exceptions=False,
        )

        self.assertEqual(result.exit_code, 1)

    def test_suppress_standard_output_context(
        self,
    ):
        # Create a mock for subprocess.Popen
        mock_popen = MagicMock()

        # Ensure that the original Popen is restored after exiting the context
        original_popen = subprocess.Popen

        with mock.patch("subprocess.Popen", mock_popen):
            with suppress_standard_output_context():
                # Inside the context, subprocess.Popen should be replaced by the _popen_suppress method
                subprocess.Popen('echo "test"')
                mock_popen.assert_called_once()

                # Check if 'stdout' is redirected to os.devnull
                args, kwargs = mock_popen.call_args
                self.assertIn("stdout", kwargs)
                self.assertEqual(
                    kwargs["stdout"].name,
                    os.devnull,
                )

        # Outside the context, subprocess.Popen should be restored to its original implementation
        self.assertIs(subprocess.Popen, original_popen)

    @mock.patch("click.core.Context")
    def test_no_config_file_argument(self, mock_ctx):
        mock_ctx.params = {}
        validate_only_config_file_argument(mock_ctx)
        # No assertion needed as the function should return without raising an error

    @mock.patch("click.core.Context")
    def test_only_config_file_argument(self, mock_ctx):
        mock_ctx.params = {"config_file": "config.yaml"}
        mock_ctx.get_parameter_source = mock.Mock(
            return_value=click.core.ParameterSource.COMMANDLINE
        )
        validate_only_config_file_argument(mock_ctx)
        # No assertion needed as the function should return without raising an error

    @mock.patch("click.core.Context")
    def test_config_file_with_other_arguments(self, mock_ctx):
        mock_ctx.params = {
            "config_file": "config.yaml",
            "other_arg": "value",
        }
        mock_ctx.get_parameter_source = mock.Mock(
            side_effect=[
                click.core.ParameterSource.COMMANDLINE,
                click.core.ParameterSource.COMMANDLINE,
            ]
        )
        with self.assertRaises(click.BadParameter):
            validate_only_config_file_argument(mock_ctx)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_recipe(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--recipe",
                "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_recipe_and_override_parameters(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        override_params = '''{
            "recipes.run.name": "test-run",
            "recipes.trainer.num_nodes": 1,
            "instance_type": "g5.48xlarge"
        }'''

        result = self.runner.invoke(
            start_job,
            [
                "--recipe",
                "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
                "--override-parameters",
                override_params,
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_recipe_invalid_override_parameters(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=1,           # Simulate a failed command
            stdout='Command failed',  # Simulate standard output
            stderr=''               # Simulate no errors
        )           
        result = self.runner.invoke(
            start_job,
            [
                "--recipe",
                "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
                "--override-parameters",
                "invalid json",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("subprocess.run")
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    @mock.patch("logging.Logger.debug")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.commands.job.JobValidator")
    @mock.patch("boto3.Session")
    def test_start_job_with_recipe_debug_mode(
        self,
        mock_boto3,
        mock_validator_cls,
        mock_kubernetes_client,
        mock_get_console_link,
        mock_debug,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_subprocess_run,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        mock_kubernetes_client.get_current_context_namespace.return_value = "kubeflow"
        mock_get_console_link.return_value = "test-console-link"
        mock_yaml_dump.return_value = None
        mock_subprocess_run.return_value = subprocess.CompletedProcess(
            args=['some_command'],  # Simulate the command arguments
            returncode=0,           # Simulate a successful command
            stdout='Command executed successfully',  # Simulate standard output
            stderr=''               # Simulate no errors
        )
        result = self.runner.invoke(
            start_job,
            [
                "--recipe",
                "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
                "--debug",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    def test_start_job_with_recipe_missing_required_args(self):
        result = self.runner.invoke(
            start_job,
            [
                "--override-parameters",
                "{}",
            ],
        )
        self.assertNotEqual(result.exit_code, 0)
