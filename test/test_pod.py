import unittest
from unittest import mock
from unittest.mock import MagicMock

import click
from click.testing import CliRunner

from hyperpod_cli.commands.pod import exec, get_log
from hyperpod_cli.service.exec_command import ExecCommand
from hyperpod_cli.service.get_logs import GetLogs


class PodTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_get_job_log = MagicMock(spec=GetLogs)
        self.mock_exec_command = MagicMock(spec=ExecCommand)

    @mock.patch("hyperpod_cli.service.get_logs.GetLogs")
    @mock.patch("hyperpod_cli.service.get_logs.GetLogs.get_training_job_logs")
    def test_get_logs_happy_case(
        self,
        mock_get_logs_service_and_get_logs: mock.Mock,
        mock_get_logs_service: mock.Mock,
    ):
        mock_get_logs_service.return_value = self.mock_get_job_log
        mock_get_logs_service_and_get_logs.return_value = "{}"
        result = self.runner.invoke(get_log, ["--name", "example-job", "--pod", "pod-name"])
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.get_logs.GetLogs")
    @mock.patch("hyperpod_cli.service.get_logs.GetLogs.get_training_job_logs")
    def test_describe_job_happy_case_with_namespace(
        self,
        mock_get_logs_service_and_get_logs: mock.Mock,
        mock_get_logs_service: mock.Mock,
    ):
        mock_get_logs_service.return_value = self.mock_get_job_log
        mock_get_logs_service_and_get_logs.return_value = "{}"
        result = self.runner.invoke(
            get_log, ["--name", "example-job", "--pod", "pod-name", "--namespace", "kubeflow"]
        )
        self.assertEqual(result.exit_code, 0)

    def test_describe_job_error_missing_name_option(self):
        result = self.runner.invoke(get_log, ["example-job", "--pod", "pod-name"])
        self.assertIn("Missing option '--name'", result.output)
        self.assertEqual(2, result.exit_code)

    def test_describe_job_error_missing_pod_option(self):
        result = self.runner.invoke(
            get_log,
            [
                "--name",
                "example-job",
                "pod-name",
            ],
        )
        self.assertIn("Missing option '--pod'", result.output)
        self.assertEqual(2, result.exit_code)

    @mock.patch("hyperpod_cli.service.get_logs.GetLogs")
    @mock.patch("hyperpod_cli.service.get_logs.GetLogs.get_training_job_logs")
    def test_describe_job_when_subprocess_command_gives_exception(
        self,
        mock_get_logs_service_and_get_logs: mock.Mock,
        mock_get_logs_service: mock.Mock,
    ):
        mock_get_logs_service.return_value = self.mock_get_job_log
        mock_get_logs_service_and_get_logs.side_effect = Exception("Boom!")
        result = self.runner.invoke(
            get_log,
            [
                "--name",
                "example-job",
                "--pod",
                "pod-name",
            ],
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to get logs for training job", result.output
        )

    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand")
    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand.exec_command")
    def test_exec_command_happy_case(
        self,
        mock_exec_command_service_and_exec_command: mock.Mock,
        mock_exec_command_service: mock.Mock,
    ):
        mock_exec_command_service.return_value = self.mock_exec_command
        mock_exec_command_service_and_exec_command.return_value = "{}"
        result = self.runner.invoke(
            exec, ["--name", "example-job", "--pod", "pod-name", "-", "date"]
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand")
    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand.exec_command")
    def test_exec_command_all_pods(
        self,
        mock_exec_command_service_and_exec_command: mock.Mock,
        mock_exec_command_service: mock.Mock,
    ):
        mock_exec_command_service.return_value = self.mock_exec_command
        mock_exec_command_service_and_exec_command.return_value = "{}"
        result = self.runner.invoke(exec, ["--name", "example-job", "--all-pods", "-", "date"])
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand")
    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand.exec_command")
    def test_exec_command_all_pods_with_namespace(
        self,
        mock_exec_command_service_and_exec_command: mock.Mock,
        mock_exec_command_service: mock.Mock,
    ):
        mock_exec_command_service.return_value = self.mock_exec_command
        mock_exec_command_service_and_exec_command.return_value = "{}"
        result = self.runner.invoke(
            exec, ["--name", "example-job", "--all-pods", "--namespace", "kubeflow", "-", "date"]
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand")
    @mock.patch("hyperpod_cli.service.exec_command.ExecCommand.exec_command")
    def test_exec_command_all_pods_throw_Exception(
        self,
        mock_exec_command_service_and_exec_command: mock.Mock,
        mock_exec_command_service: mock.Mock,
    ):
        mock_exec_command_service.return_value = self.mock_exec_command
        mock_exec_command_service_and_exec_command.side_effect = RuntimeError
        result = self.runner.invoke(
            exec, ["--name", "example-job", "--all-pods", "--namespace", "kubeflow", "-", "date"]
        )
        self.assertEqual(result.exit_code, 1)

    def test_exec_command_all_pods_and_pod_exception(self):
        result = self.runner.invoke(
            exec, ["--name", "example-job", "--all-pods", "--pod", "test_pod", "-", "date"]
        )
        self.assertIn(
            "With job-name name must specify only one option --pod or --all-pods", result.output
        )
        self.assertEqual(result.exit_code, 1)

    def test_exec_command_without_all_pods_and_pod(self):
        result = self.runner.invoke(exec, ["--name", "example-job", "-", "date"])
        self.assertIn("With job-name name must specify option --pod or --all-pods", result.output)
        self.assertEqual(result.exit_code, 1)

    def test_exec_command_missing_name(self):
        result = self.runner.invoke(exec, ["--namespace", "example-job", "-", "date"])
        self.assertIn("Missing option '--name'", result.output)
        self.assertEqual(result.exit_code, 2)
