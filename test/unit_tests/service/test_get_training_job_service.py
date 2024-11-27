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
from kubernetes.client import V1ResourceAttributes

from hyperpod_cli.service.get_training_job import (
    GetTrainingJob,
)

from kubernetes.client.rest import ApiException


SAMPLE_HYPERPOD_CLUSTER_URL = "https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/cluster-management/cluster_name"


class GetTrainingJobTest(unittest.TestCase):
    def setUp(self):
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)
        self.mock_get_training_job = GetTrainingJob()

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_get_training_job.get_training_job(
            "sample-job", "namespace", None
        )
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_get_training_job.get_training_job("sample-job", None, None)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_namespace_auto_discover(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
        mock_discover_accessible_namespace: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        mock_discover_accessible_namespace.return_value = "discovered-namespace"

        self.mock_k8s_client.get_current_context_namespace.return_value = None
        self.mock_k8s_client.get_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_get_training_job.get_training_job("sample-job", None, None)
        # Ensure that we are using correct resource attributes for auto-discover
        mock_discover_accessible_namespace.assert_called_once_with(
            V1ResourceAttributes(
                verb="get",
                group="kubeflow.org",
                resource="pytorchjobs",
            )
        )
        self.mock_k8s_client.get_job.assert_called_once_with(
            job_name="sample-job",
            namespace="discovered-namespace",
        )
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_verbose(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = {
            "metadata": {"name": "pytorch-simple"}
        }
        result = self.mock_get_training_job.get_training_job("sample-job", None, True)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_verbose_with_no_output(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = None
        result = self.mock_get_training_job.get_training_job("sample-job", None, True)
        self.assertIn("", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_without_verbose_with_no_output(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = None
        result = self.mock_get_training_job.get_training_job("sample-job", None, False)
        self.assertIn("", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_without_verbose_without_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = {"status": "test_status"}
        result = self.mock_get_training_job.get_training_job("sample-job", None, False)
        self.assertIn("test_status", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_verbose_with_values(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = {
            "metadata": {"name": "pytorch-simple"},
            "kind": "test_kind",
            "apiVersion": "test_apiVersion",
            "spec": "test_spec",
            "status": "test_status",
        }
        result = self.mock_get_training_job.get_training_job("sample-job", None, True)
        self.assertIn("pytorch-simple", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_verbose_without_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.return_value = {
            "kind": "test_kind",
            "apiVersion": "test_apiVersion",
            "spec": "test_spec",
            "status": "test_status",
        }
        result = self.mock_get_training_job.get_training_job("sample-job", None, True)
        self.assertIn("test_status", result)

    @mock.patch("hyperpod_cli.utils.get_cluster_console_url")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_training_job_with_verbose_without_metadata_api_exception(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_current_hyperpod_context: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_current_hyperpod_context.return_value = SAMPLE_HYPERPOD_CLUSTER_URL
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.get_job.side_effect = ApiException(
            status="Failed", reason="unexpected"
        )
        with self.assertRaises(RuntimeError):
            self.mock_get_training_job.get_training_job("sample-job", None, True)
