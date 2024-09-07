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

from hyperpod_cli.clients.kubernetes_client import (
    KubernetesClient,
)
from hyperpod_cli.service.cancel_training_job import (
    CancelTrainingJob,
)

from kubernetes.client.rest import ApiException


class CancelTrainingJobTest(unittest.TestCase):
    def setUp(self):
        self.mock_cancel_training_job = CancelTrainingJob()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("subprocess.run")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_cancel_training_job_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.delete_training_job.return_value = {"status": "Success"}
        result = self.mock_cancel_training_job.cancel_training_job(
            "sample-job", "namespace"
        )
        self.assertIsNone(result)
        mock_subprocess_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_cancel_training_job_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.delete_training_job.return_value = {"status": "Success"}
        result = self.mock_cancel_training_job.cancel_training_job("sample-job", None)
        self.assertIsNone(result)
        mock_subprocess_run.assert_called_once()

    @mock.patch("subprocess.run")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_cancel_training_job_api_exception(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.delete_training_job.side_effect = ApiException(
            status="Failed", reason="unexpected"
        )
        with self.assertRaises(RuntimeError):
            self.mock_cancel_training_job.cancel_training_job("sample-job", None)
        mock_subprocess_run.assert_not_called()
