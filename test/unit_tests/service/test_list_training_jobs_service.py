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
from hyperpod_cli.service.list_training_jobs import (
    ListTrainingJobs,
)

from kubernetes.client.rest import ApiException

SAMPLE_OUTPUT = {
    "items": [
        {
            "metadata": {
                "name": "test-name",
                "namespace": "test-namespace",
            },
            "status": {
                "startTime": "test-time",
                "conditions": [
                    {
                        "type": "Succeeded",
                        "lastTransitionTime": "2023-08-27T22:47:57Z",
                    }
                ],
            },
        },
        {
            "metadata": {
                "name": "test-name1",
                "namespace": "test-namespace1",
            },
            "status": {
                "startTime": "test-time1",
                "conditions": [
                    {
                        "type": "Running",
                        "lastTransitionTime": "2024-08-27T22:47:57Z",
                    },
                    {
                        "type": "Created",
                        "lastTransitionTime": "2023-08-27T22:47:57Z",
                    },
                ],
            },
        },
        {
            "metadata": {
                "name": "test-name2",
                "namespace": "test-namespace1",
            },
            "status": {
                "startTime": "test-time1",
                "conditions": [
                    {
                        "type": "Created",
                        "lastTransitionTime": "2024-08-27T22:47:57Z",
                    }
                ],
            },
        },
    ]
}
INVALID_OUTPUT = {
    "items": [
        {
            "status": {
                "startTime": "test-time",
                "conditions": [{"type": "Succeeded"}],
            },
        }
    ]
}
OUTPUT_WITHOUT_STATUS = {
    "items": [
        {
            "metadata": {
                "name": "test-name",
                "namespace": "test-namespace",
            },
        }
    ]
}


class ListTrainingJobsTest(unittest.TestCase):
    def setUp(self):
        self.mock_list_training_jobs = ListTrainingJobs()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(
            "namespace", None, None
        )
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_api_exception(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.side_effect = ApiException(
            status="Failed", reason="unexpected"
        )
        with self.assertRaises(RuntimeError):
            self.mock_list_training_jobs.list_training_jobs(None, True, None)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = INVALID_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_status(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = OUTPUT_WITHOUT_STATUS
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None)
        self.assertNotIn("State: null", result)
