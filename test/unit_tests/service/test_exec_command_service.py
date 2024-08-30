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
from unittest import mock
from unittest.mock import MagicMock

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.exec_command import ExecCommand
from hyperpod_cli.service.list_pods import ListPods


class ExecCommandServiceTest(unittest.TestCase):
    def setUp(self):
        self.mock_exec_command = ExecCommand()
        self.mock_list_pods_service = MagicMock(spec=ListPods)
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_exec_with_pod_without_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        self.mock_k8s_client.exec_command_on_pod.return_value = (
            "Fri Aug  9 06:16:05 UTC 2024"
        )
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = [
            "sample-job-master-0"
        ]
        result = self.mock_exec_command.exec_command(
            "sample-job",
            "sample-job-master-0",
            None,
            False,
            (
                "-",
                "date",
            ),
        )
        self.assertIn("Fri Aug  9 06:16:05 UTC 2024", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_exec_with_pod_with_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.exec_command_on_pod.return_value = (
            "Fri Aug  9 06:16:05 UTC 2024"
        )
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = [
            "sample-job-master-0"
        ]
        result = self.mock_exec_command.exec_command(
            "sample-job",
            "sample-job-master-0",
            "kubeflow",
            False,
            (
                "-",
                "date",
            ),
        )
        self.assertIn("Fri Aug  9 06:16:05 UTC 2024", result)

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_exec_with_pod_with_namespace_unknown_pod(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
    ):
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = [
            "sample-job-master-1"
        ]
        with self.assertRaises(RuntimeError):
            self.mock_exec_command.exec_command(
                "sample-job",
                "sample-job-master-0",
                "kubeflow",
                False,
                (
                    "-",
                    "date",
                ),
            )

    def test_exec_with_input_before_dash_raises_exception(
        self,
    ):
        with self.assertRaises(RuntimeError):
            self.mock_exec_command.exec_command(
                "sample-job",
                "sample-job-master-0",
                "kubeflow",
                False,
                (
                    "date",
                    "-",
                    "date",
                ),
            )

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_exec_with_pod_with_namespace_all_pod(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.exec_command_on_pod.return_value = (
            "Fri Aug  9 06:16:05 UTC 2024"
        )
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = [
            "sample-job-master-0"
        ]
        result = self.mock_exec_command.exec_command(
            "sample-job",
            None,
            "kubeflow",
            True,
            (
                "-",
                "date",
            ),
        )
        self.assertIn("Fri Aug  9 06:16:05 UTC 2024", result)
