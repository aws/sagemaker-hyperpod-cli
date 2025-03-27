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
from hyperpod_cli.service.get_logs import GetLogs
from hyperpod_cli.service.list_pods import (
    ListPods,
)

from kubernetes.client.rest import ApiException


class TestGetLogs(unittest.TestCase):
    def setUp(self):
        self.mock_get_logs = GetLogs()
        self.mock_list_pods_service = MagicMock(spec=ListPods)
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_with_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        result = self.mock_get_logs.get_training_job_logs(
            "sample-job", "test-pod", "kubeflow"
        )
        self.assertIn("test logs", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_without_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        result = self.mock_get_logs.get_training_job_logs(
            "sample-job", "test-pod", None
        )
        self.assertIn("test logs", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_pod_not_found_for_job(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        with self.assertRaises(RuntimeError):
            self.mock_get_logs.get_training_job_logs("sample-job", "test-pod1", None)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_without_namespace_api_exception(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.side_effect = ApiException(
            status="Failed", reason="unexpected"
        )
        with self.assertRaises(RuntimeError):
            self.mock_get_logs.get_training_job_logs("sample-job", "test-pod", None)

    @mock.patch("hyperpod_cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_get_logs_auto_discover_namespace(
        self,
        mock_list_training_job_pods_service_with_list_pods: mock.Mock,
        mock_list_training_job_pods_service: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_discover_accessible_namespace: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_list_training_job_pods_service.return_value = self.mock_list_pods_service
        self.mock_k8s_client.get_current_context_namespace.return_value = None
        mock_discover_accessible_namespace.return_value = "discovered-namespace"
        mock_list_training_job_pods_service_with_list_pods.return_value = ["test-pod"]
        self.mock_k8s_client.get_logs_for_pod.return_value = "test logs"
        result = self.mock_get_logs.get_training_job_logs(
            "sample-job", "test-pod", None
        )
        self.assertIn("test logs", result)

    def test_get_log_url(
        self,
    ):
        eks_cluster_name = 'eks_cluster_name'
        region = 'us-west-2'
        node_name = 'node_name'
        pod_name = 'pod_name'
        namespace = 'namespace'
        container_name = 'container_name'
        container_id = 'container_id'
        result_url = self.mock_get_logs.get_log_url(eks_cluster_name, region, node_name, pod_name, namespace, container_name, container_id)

        self.assertEqual(
            result_url,
            'https://us-west-2.console.aws.amazon.com/cloudwatch/home?region=us-west-2#logsV2:log-groups/log-group/$252Faws$252Fcontainerinsights$252Feks_cluster_name$252Fapplication/log-events/node_name-application.var.log.containers.pod_name_namespace_container_name-container_id.log'
        )
