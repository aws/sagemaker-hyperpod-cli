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
import os
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

import yaml
from kubernetes import client
from kubernetes.client import (
    V1ListMeta,
    V1Namespace,
    V1NamespaceList,
    V1Node,
    V1NodeList,
    V1ObjectMeta,
    V1Pod,
    V1PodList,
)
from kubernetes.config import KUBE_CONFIG_DEFAULT_LOCATION

from hyperpod_cli.clients.kubernetes_client import KubernetesClient

KUBECONFIG_DATA = {
    "contexts": [
        {
            "name": "context1",
            "context": {
                "cluster": "cluster-1",
                "user": "user-1",
            },
        },
        {
            "name": "context2",
            "context": {
                "cluster": "cluster-2",
                "user": "user-2",
            },
        },
    ],
    "current-context": {"context": {"namespace": "kubeflow"}},
}

namespaces: V1NamespaceList = V1NamespaceList(
    items=[
        V1Namespace(metadata=V1ObjectMeta(name="test")),
        V1Namespace(metadata=V1ObjectMeta(name="test1")),
    ]
)

namespaces_no_metadata: V1NamespaceList = V1NamespaceList(
    items=[V1Namespace(metadata=None)]
)

pods_with_next_token: V1PodList = V1PodList(
    metadata=V1ListMeta(
        _continue="next",
    ),
    items=[
        V1Pod(
            metadata=V1ObjectMeta(
                name="test-name", namespace="kubeflow", creation_timestamp="timestamp"
            )
        )
    ],
)

pods_no_next_token: V1PodList = V1PodList(
    metadata=V1ListMeta(
        _continue=None,
    ),
    items=[
        V1Pod(
            metadata=V1ObjectMeta(
                name="test-name", namespace="kubeflow", creation_timestamp="timestamp"
            )
        )
    ],
)

nodes_with_next_token: V1NodeList = V1NodeList(
    metadata=V1ListMeta(
        _continue="next",
    ),
    items=[
        V1Node(
            metadata=V1ObjectMeta(
                name="test-name", namespace="kubeflow", creation_timestamp="timestamp"
            )
        )
    ],
)

nodes_no_next_token: V1NodeList = V1NodeList(
    metadata=V1ListMeta(
        _continue=None,
    ),
    items=[
        V1Node(
            metadata=V1ObjectMeta(
                name="test-name", namespace="kubeflow", creation_timestamp="timestamp"
            )
        )
    ],
)


class TestKubernetesClient(unittest.TestCase):
    @patch("kubernetes.config.load_kube_config")
    def test_singleton_instance(self, mock_load_kube_config):
        mock_load_kube_config.return_value = None
        client1 = KubernetesClient()
        client2 = KubernetesClient()
        self.assertIs(client1, client2)

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    @patch(
        "builtins.open", new_callable=mock_open, read_data=yaml.dump(KUBECONFIG_DATA)
    )
    def test_set_context_success(
        self,
        mock_open_file: Mock,
        mock_safe_load: Mock,
        mock_safe_dump: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_safe_load.return_value = KUBECONFIG_DATA
        mock_safe_dump.return_value = None
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        test_client = KubernetesClient()
        test_client.set_context("context2", "default")
        mock_open_file.assert_called_with(
            os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION), "w"
        )

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    @patch(
        "builtins.open", new_callable=mock_open, read_data=yaml.dump(KUBECONFIG_DATA)
    )
    def test_set_context_failure(
        self,
        mock_open_file: Mock,
        mock_safe_load: Mock,
        mock_safe_dump: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_safe_load.return_value = KUBECONFIG_DATA
        mock_safe_dump.return_value = None
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        test_client = KubernetesClient()
        with self.assertRaises(ValueError):
            test_client.set_context("invalid-context", "default")

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("yaml.safe_dump")
    @patch("yaml.safe_load")
    @patch(
        "builtins.open", new_callable=mock_open, read_data=yaml.dump(KUBECONFIG_DATA)
    )
    def test_set_context_success_other_namespace(
        self,
        mock_open_file: Mock,
        mock_safe_load: Mock,
        mock_safe_dump: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_safe_load.return_value = KUBECONFIG_DATA
        mock_safe_dump.return_value = None
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        test_client = KubernetesClient()
        test_client.set_context("context2", "kubeflow")
        mock_open_file.assert_called_with(
            os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION), "w"
        )

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("kubernetes.config.list_kube_config_contexts")
    def test_context_exists_success(
        self,
        mock_list_kube_config_contexts: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        mock_list_kube_config_contexts.return_value = (
            KUBECONFIG_DATA["contexts"],
            None,
        )
        test_client = KubernetesClient()
        self.assertTrue(test_client.context_exists("context1"))

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("kubernetes.config.list_kube_config_contexts")
    def test_context_not_exists_succeeded(
        self,
        mock_list_kube_config_contexts: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        mock_list_kube_config_contexts.return_value = (
            KUBECONFIG_DATA["contexts"],
            None,
        )
        test_client = KubernetesClient()
        self.assertFalse(test_client.context_exists("invalid-context"))

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    @patch("kubernetes.config.list_kube_config_contexts")
    def test_context_exists_error(
        self,
        mock_list_kube_config_contexts: Mock,
        mock_kube_config: Mock,
        mock_client: Mock,
    ):
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        mock_list_kube_config_contexts.side_effect = Exception(
            "Failed to list kube config contexts"
        )
        test_client = KubernetesClient()
        with self.assertRaises(RuntimeError):
            test_client.context_exists("context1")

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    def test_get_core_v1_api(self, mock_kube_config: Mock, mock_client: Mock):
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        test_client = KubernetesClient()
        test_client._kube_client = mock_client
        core_v1_api = test_client.get_core_v1_api()
        self.assertIsInstance(core_v1_api, client.CoreV1Api)

    @patch("kubernetes.client.ApiClient")
    @patch("kubernetes.config.load_kube_config")
    def test_get_apps_v1_api(self, mock_kube_config: Mock, mock_client: Mock):
        mock_kube_config.return_value = None
        mock_client.return_value = MagicMock()
        test_client = KubernetesClient()
        test_client._kube_client = mock_client
        apps_v1_api = test_client.get_apps_v1_api()
        self.assertIsInstance(apps_v1_api, client.AppsV1Api)

    @patch("kubernetes.config.load_kube_config")
    def test_get_core_v1_api_error(
        self,
        mock_kube_config: Mock,
    ):
        mock_kube_config.return_value = None
        test_client = KubernetesClient()
        test_client._kube_client = None
        with self.assertRaises(RuntimeError):
            test_client.get_core_v1_api()

    @patch("kubernetes.config.load_kube_config")
    def test_get_apps_v1_api_error(
        self,
        mock_kube_config: Mock,
    ):
        mock_kube_config.return_value = None
        test_client = KubernetesClient()
        test_client._kube_client = None
        with self.assertRaises(RuntimeError):
            test_client.get_apps_v1_api()

    @patch("kubernetes.config.load_kube_config")
    @patch("kubernetes.client.CoreV1Api.list_node", return_value=nodes_no_next_token)
    def test_list_node_with_temp_config_no_next_token(
        self,
        mock_core_client: Mock,
        mock_kube_config: Mock,
    ):
        mock_kube_config.return_value = None
        test_client = KubernetesClient()
        test_client.list_node_with_temp_config("temp-file", "temp-label")

    @patch("kubernetes.config.load_kube_config")
    @patch(
        "kubernetes.client.CoreV1Api.list_node",
        side_effect=[nodes_with_next_token, nodes_no_next_token],
    )
    def test_list_node_with_temp_config_no_next_token_with_pagination(
        self,
        mock_core_client: Mock,
        mock_kube_config: Mock,
    ):
        mock_kube_config.return_value = None
        test_client = KubernetesClient()
        test_client.list_node_with_temp_config("temp-file", "temp-label")

    @patch("kubernetes.client.CustomObjectsApi")
    def test_delete_training_job_with_namepsace(
        self,
        mock_custom_client: Mock,
    ):
        mock_custom_client.delete_namespaced_custom_object.return_value = "{}"
        test_client = KubernetesClient()
        test_client.delete_training_job("training_job_name", "default")

    @patch(
        "kubernetes.client.CustomObjectsApi",
        return_value=Mock(get_namespaced_custom_object=Mock(return_value="{}")),
    )
    def test_get_job_with_namepsace(
        self,
        mock_custom_client: Mock,
    ):
        test_client = KubernetesClient()
        result = test_client.get_job("training_job_name", "default")
        self.assertEqual("{}", result)

    @patch("kubernetes.config.list_kube_config_contexts")
    def test_get_current_context_namespace(
        self,
        mock_kube_config: Mock,
    ):
        mock_kube_config.return_value = (
            KUBECONFIG_DATA["contexts"],
            KUBECONFIG_DATA["current-context"],
        )
        test_client = KubernetesClient()
        result = test_client.get_current_context_namespace()
        self.assertEqual("kubeflow", result)

    @patch(
        "kubernetes.client.CoreV1Api",
        return_value=Mock(list_namespace=Mock(return_value=namespaces)),
    )
    def test_list_namespace(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.list_namespaces()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "test")

    @patch(
        "kubernetes.client.CoreV1Api",
        return_value=Mock(list_namespace=Mock(return_value=namespaces_no_metadata)),
    )
    def test_list_namespace_items_with_no_metadata(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.list_namespaces()
        self.assertEqual(len(result), 0)

    @patch(
        "kubernetes.client.CoreV1Api",
        return_value=Mock(list_namespaced_pod=Mock(return_value=V1PodList(items=[]))),
    )
    def test_list_pods_with_labels(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.list_pods_with_labels("kubeflow", "test:test")
        self.assertEqual(0, len(result.items))

    @patch(
        "kubernetes.client.CoreV1Api",
        return_value=Mock(read_namespaced_pod_log=Mock(return_value="test log")),
    )
    def test_logs_for_pods(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.get_logs_for_pod("test", "kubeflow")
        self.assertIn("test log", result)

    @patch(
        "kubernetes.client.CustomObjectsApi",
        return_value=Mock(
            list_namespaced_custom_object=Mock(
                return_value={"items": ["test", "test1"]}
            )
        ),
    )
    def test_list_training_job(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.list_training_jobs("kubeflow", "test:test")
        self.assertEqual(2, len(result.get("items")))

    @patch(
        "kubernetes.client.CoreV1Api",
        return_value=Mock(
            list_pod_for_all_namespaces=Mock(return_value=pods_no_next_token)
        ),
    )
    def test_list_pods_in_all_namespaces_with_labels(self, mock_core_client: Mock):
        test_client = KubernetesClient()
        result = test_client.list_pods_in_all_namespaces_with_labels("kubeflow")
        self.assertEqual(1, len(result))

    @patch(
        "kubernetes.client.CoreV1Api.list_pod_for_all_namespaces",
        side_effect=[pods_with_next_token, pods_no_next_token],
    )
    def test_list_pods_in_all_namespaces_with_labels_with_pagination(
        self, mock_method: Mock
    ):
        test_client = KubernetesClient()
        result = test_client.list_pods_in_all_namespaces_with_labels("kubeflow")
        self.assertEqual(2, len(result))
