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
from kubernetes.client.rest import ApiException
from sagemaker.hyperpod.cli.service.discover_namespaces import DiscoverNamespaces
from concurrent.futures import Future
from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)

class TestDiscoverNamespaces(unittest.TestCase):

    def setUp(self):
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.get_current_context_namespace")
    def test_discover_accessible_sm_managed_namespace_explicit(
        self, 
        mock_get_current_context_namespace, 
    ):
        # Mock that the current context namespace is set
        mock_get_current_context_namespace.return_value = "explicit-namespace"

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()

        # Call discover_accessible_sm_managed_namespace with a resource attributes template
        result = discover_ns.discover_accessible_namespace(resource_attributes_template={})

        # Assert that the explicitly set namespace is returned
        self.assertEqual(result, "explicit-namespace")

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("sagemaker.hyperpod.cli.service.get_namespaces.GetNamespaces.get_sagemaker_managed_namespaces")
    @mock.patch("sagemaker.hyperpod.cli.service.discover_namespaces.DiscoverNamespaces.get_namespaces_by_checking_access_permission")
    def test_discover_accessible_sm_managed_namespace_success(
        self, 
        mock_get_namespaces_by_checking_access_permission, 
        mock_get_sagemaker_managed_namespaces,
        mock_kubernetes_client,
    ):
        # Mock clients
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = None
        
        # Mock that no explicit namespace is set in the context
        mock_get_sagemaker_managed_namespaces.return_value = ["namespace1"]
        mock_get_namespaces_by_checking_access_permission.return_value = ["namespace1"]

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()

        # Call discover_accessible_sm_managed_namespace with a resource attributes template
        result = discover_ns.discover_accessible_namespace(resource_attributes_template={})

        # Assert that the discovered namespace is returned
        self.assertEqual(result, "namespace1")

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("sagemaker.hyperpod.cli.service.get_namespaces.GetNamespaces.get_sagemaker_managed_namespaces")
    @mock.patch("sagemaker.hyperpod.cli.service.discover_namespaces.DiscoverNamespaces.get_namespaces_by_checking_access_permission")
    @mock.patch("sys.exit")
    def test_discover_accessible_sm_managed_namespace_no_accessible(
        self, 
        mock_exit, 
        mock_get_namespaces_by_checking_access_permission, 
        mock_get_sagemaker_managed_namespaces,
        mock_kubernetes_client,
    ):
        # Mock clients
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = None
        
        # Mock that no namespaces are accessible
        mock_get_sagemaker_managed_namespaces.return_value = ["namespace1"]
        mock_get_namespaces_by_checking_access_permission.return_value = []
        # Instead of exit, throw a SystemExit exception
        mock_exit.side_effect = SystemExit

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()
        
        # Ensure SystemExit is raised
        with self.assertRaises(SystemExit):
            discover_ns.discover_accessible_namespace(resource_attributes_template={})

        # Assert sys.exit is called with status code 1
        mock_exit.assert_called_once_with(1)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("sagemaker.hyperpod.cli.service.get_namespaces.GetNamespaces.get_sagemaker_managed_namespaces")
    @mock.patch("sagemaker.hyperpod.cli.service.discover_namespaces.DiscoverNamespaces.get_namespaces_by_checking_access_permission")
    @mock.patch("sys.exit")
    def test_discover_accessible_sm_managed_namespace_multiple_accessible(
        self, 
        mock_exit, 
        mock_get_namespaces_by_checking_access_permission, 
        mock_get_sagemaker_managed_namespaces,
        mock_kubernetes_client,
    ):
        # Mock clients
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = None

        # Mock that multiple namespaces are accessible
        mock_get_sagemaker_managed_namespaces.return_value = ["namespace1", "namespace2"]
        mock_get_namespaces_by_checking_access_permission.return_value = ["namespace1", "namespace2"]
        # Instead of exit, throw a SystemExit exception
        mock_exit.side_effect = SystemExit

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()

        # Ensure SystemExit is raised
        with self.assertRaises(SystemExit):
            discover_ns.discover_accessible_namespace(resource_attributes_template={})

        # Assert sys.exit is called with status code 1 for multiple namespaces
        mock_exit.assert_called_once_with(1)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("sagemaker.hyperpod.cli.service.get_namespaces.GetNamespaces.get_sagemaker_managed_namespaces")
    @mock.patch("sys.exit")
    def test_discover_accessible_sm_managed_namespace_api_exception(
        self, 
        mock_exit, 
        mock_get_sagemaker_managed_namespaces,
        mock_kubernetes_client,
    ):
        # Mock clients
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = None

        # Simulate a 403 Forbidden ApiException
        mock_get_sagemaker_managed_namespaces.side_effect = ApiException(status=403)
        # Instead of exit, throw a SystemExit exception
        mock_exit.side_effect = SystemExit

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()

         # Ensure SystemExit is raised
        with self.assertRaises(SystemExit):
            discover_ns.discover_accessible_namespace(resource_attributes_template={})

        # Assert sys.exit is called with status code 1
        mock_exit.assert_called_once_with(1)

    @mock.patch("sagemaker.hyperpod.cli.service.self_subject_access_review.SelfSubjectAccessReview.self_subject_access_review")
    def test_get_namespaces_by_checking_access_permission(
        self, 
        mock_self_subject_access_review,
    ):
        # Mock the SelfSubjectAccessReview response
        mock_future = Future()
        mock_response = MagicMock()
        mock_response.status.allowed = True
        mock_response.spec.resource_attributes = MagicMock(namespace="namespace1")
        mock_future.set_result(mock_response)

        mock_self_subject_access_review.return_value = mock_future.result()

        # Mock the resource attributes object
        resource_attributes_template = MagicMock()
        resource_attributes_template.namespace = None

        # Instantiate the DiscoverNamespaces class
        discover_ns = DiscoverNamespaces()

        # Call get_namespaces_by_checking_access_permission
        namespaces = discover_ns.get_namespaces_by_checking_access_permission(
            namespaces=["namespace1"],
            resource_attributes_template=resource_attributes_template,
            max_workers=1
        )

        # Assert that the namespace is correctly identified as accessible
        self.assertEqual(namespaces, ["namespace1"])


if __name__ == "__main__":
    unittest.main()
