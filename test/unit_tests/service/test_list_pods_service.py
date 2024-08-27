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

from kubernetes.client import (
    V1Container,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
    V1PodSpec,
    V1PodStatus,
    V1ResourceRequirements,
)

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.service.list_pods import ListPods

SAMPLE_OUTPUT: V1PodList = V1PodList(
    items=[
        V1Pod(
            metadata=V1ObjectMeta(
                name="test-name", namespace="kubeflow", creation_timestamp="timestamp"
            ),
            spec=V1PodSpec(
                node_name="test-node-name",
                containers=[
                    V1Container(
                        name="test-container",
                        resources=V1ResourceRequirements(requests={"nvidia.com/gpu": "1"}),
                    )
                ],
            ),
        ),
        V1Pod(
            metadata=V1ObjectMeta(name="test-name", namespace="kubeflow"),
            spec=V1PodSpec(
                node_name="test-node-name",
                containers=[
                    V1Container(
                        name="test-container",
                        resources=V1ResourceRequirements(
                            requests={"aws.amazon.com/neurondevice": "1"}
                        ),
                    )
                ],
            ),
            status=V1PodStatus(phase="running")
        ),
    ]
)


class TestListPods(unittest.TestCase):

    def setUp(self):
        self.mock_list_pods = ListPods()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = SAMPLE_OUTPUT
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", False)
        self.assertEqual(2, len(result))

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace_no_pods(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = V1PodList(items=[])
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", False)
        self.assertEqual(0, len(result))

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace_no_pods_pretty(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = V1PodList(items=[])
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", True)
        self.assertNotIn("test-name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace_pods_with_no_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        sample_metadata_none_output: V1PodList = V1PodList(items=[V1Pod(metadata=None)])
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = sample_metadata_none_output
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", False)
        self.assertEqual(0, len(result))

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "kubeflow"
        self.mock_k8s_client.list_pods_with_labels.return_value = SAMPLE_OUTPUT
        result = self.mock_list_pods.list_pods_for_training_job("test-job", None, False)
        self.assertEqual(2, len(result))

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace_pretty(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = SAMPLE_OUTPUT
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", True)
        self.assertIn("test-name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_with_namespace_pretty_without_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        sample_metadata_none_output: V1PodList = V1PodList(items=[V1Pod(metadata=None)])
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_with_labels.return_value = sample_metadata_none_output
        result = self.mock_list_pods.list_pods_for_training_job("test-job", "kubeflow", True)
        self.assertNotIn("test-name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_and_get_requested_resources_group_by_node_name(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_in_all_namespaces_with_labels.return_value = (
            SAMPLE_OUTPUT.items
        )
        result = self.mock_list_pods.list_pods_and_get_requested_resources_group_by_node_name()
        self.assertIn("test-node-name", result)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_pods_and_get_requested_resources_should_skip_if_node_name_is_empty(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_pods_in_all_namespaces_with_labels.return_value = [
            V1Pod(
                spec=V1PodSpec(
                    containers=[
                        V1Container(
                            name="test-container",
                            resources=V1ResourceRequirements(requests={"nvidia.com/gpu": "1"}),
                        )
                    ]
                )
            )
        ]
        result = self.mock_list_pods.list_pods_and_get_requested_resources_group_by_node_name()
        self.assertEqual(len(result), 0)
