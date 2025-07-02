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

from sagemaker.hyperpod.cli.clients.kubernetes_client import KubernetesClient
from sagemaker.hyperpod.cli.service.get_namespaces import GetNamespaces


class TestGetNamespaces(unittest.TestCase):
    
    def setUp(self):
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)
        self.mock_get_namespaces = GetNamespaces()

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_namespaces_success(self, mock_kubernetes_client):
        mock_core_v1_api = MagicMock()
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_core_v1_api.return_value = mock_core_v1_api

        mock_namespace_list = MagicMock()
        mock_namespace1 = MagicMock()
        mock_namespace1.metadata.name = "namespace1"
        
        mock_namespace2 = MagicMock()
        mock_namespace2.metadata.name = "namespace2"
        mock_namespace_list.items = [mock_namespace1, mock_namespace2]

        mock_namespace_list.metadata._continue = None
        mock_core_v1_api.list_namespace.return_value = mock_namespace_list

        namespaces = self.mock_get_namespaces.get_namespaces()

        self.assertEqual(namespaces, ["namespace1", "namespace2"])

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_namespaces_pagination(self, mock_kubernetes_client):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_core_v1_api = MagicMock()
        self.mock_k8s_client.get_core_v1_api.return_value = mock_core_v1_api

        # First response with a continue token
        first_response = MagicMock()
        mock_namespace1 = MagicMock()
        mock_namespace1.metadata.name = "namespace1"
        first_response.items = [mock_namespace1]
        first_response.metadata._continue = "next-token"

        # Second response without a continue token
        second_response = MagicMock()
        mock_namespace2 = MagicMock()
        mock_namespace2.metadata.name = "namespace2"
        second_response.items = [mock_namespace2]
        second_response.metadata._continue = None

        mock_core_v1_api.list_namespace.side_effect = [
            first_response, second_response
        ]

        namespaces = self.mock_get_namespaces.get_namespaces()
        self.assertEqual(namespaces, ["namespace1", "namespace2"])
        self.assertEqual(mock_core_v1_api.list_namespace.call_count, 2)


    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_get_sagemaker_managed_namespaces(self, mock_kubernetes_client):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_core_v1_api = MagicMock()
        self.mock_k8s_client.get_core_v1_api.return_value = mock_core_v1_api

        first_response = MagicMock()
        mock_namespace1 = MagicMock()
        mock_namespace1.metadata.name = "namespace1"
        first_response.items = [mock_namespace1]
        first_response.metadata._continue = None

        mock_core_v1_api.list_namespace.side_effect = [
            first_response
        ]

        namespaces = self.mock_get_namespaces.get_sagemaker_managed_namespaces()
        self.assertEqual(namespaces, ["namespace1"])
        mock_core_v1_api.list_namespace.assert_called_once_with(
            limit=200, 
            label_selector="sagemaker.amazonaws.com/sagemaker-managed-queue=true"
        )


if __name__ == "__main__":
    unittest.main()
