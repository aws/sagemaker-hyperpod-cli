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
from kubernetes.client import V1SelfSubjectAccessReview
from kubernetes.client import AuthorizationV1Api
from sagemaker.hyperpod.cli.service.self_subject_access_review import SelfSubjectAccessReview


class TestSelfSubjectAccessReview(unittest.TestCase):

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_self_subject_access_review_success(self, mock_kubernetes_client):
        # Mock the Kubernetes API response
        mock_auth_v1_api = MagicMock(spec=AuthorizationV1Api)
        mock_kubernetes_client().get_auth_v1_api.return_value = mock_auth_v1_api
        
        # Create a mock response for create_self_subject_access_review
        mock_response = MagicMock(spec=V1SelfSubjectAccessReview)
        mock_response.status.allowed = True
        mock_auth_v1_api.create_self_subject_access_review.return_value = mock_response

        # Set up resource attributes for the access review
        resource_attributes = {
            "namespace": "test-namespace",
            "verb": "create",
            "resource": "pods"
        }

        # Instantiate the SelfSubjectAccessReview service
        service = SelfSubjectAccessReview()

        # Call the self_subject_access_review method
        response = service.self_subject_access_review(resource_attributes=resource_attributes)

        # Check that the response indicates the action is allowed
        self.assertTrue(response.status.allowed)

        # Assert that the Kubernetes API was called correctly
        mock_auth_v1_api.create_self_subject_access_review.assert_called_once()

        # Capture and inspect the arguments passed in the call
        args, kwargs = mock_auth_v1_api.create_self_subject_access_review.call_args
        self.assertIsInstance(kwargs['body'], V1SelfSubjectAccessReview)
        self.assertEqual(kwargs['body'].spec.resource_attributes['namespace'], 'test-namespace')


if __name__ == "__main__":
    unittest.main()
