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
import signal
import time
import unittest
from unittest import mock
from unittest.mock import MagicMock

from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.cluster import set_cluster_context


class ClusterTimeoutTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_session = MagicMock()
        self.mock_sm_client = MagicMock()

    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.logger")
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential")
    def test_set_cluster_context_timeout_triggered(
        self,
        mock_validate_aws_credentials,
        mock_subprocess_run,
        mock_session,
        mock_kubernetes_client,
        mock_logger,
    ):
        """Test that timeout error message is displayed when timeout occurs"""
        mock_validate_aws_credentials.return_value = True
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        
        # Mock describe_cluster to raise TimeoutError
        self.mock_sm_client.describe_cluster.side_effect = TimeoutError("Operation timed out after 300 seconds")
        
        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "test-cluster"],
        )
        
        self.assertEqual(result.exit_code, 1)
        # Verify the timeout error message was logged
        mock_logger.error.assert_called_with("Timed out - Please check credentials, setup configurations  and try again")

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential")
    def test_set_cluster_context_success(
        self,
        mock_validate_aws_credentials,
        mock_subprocess_run,
        mock_session,
        mock_kubernetes_client,
    ):
        """Test that operation completes successfully without timeout"""
        mock_validate_aws_credentials.return_value = True
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/test-cluster"
                }
            }
        }
        
        mock_k8s_client = MagicMock()
        mock_kubernetes_client.return_value = mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        
        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "test-cluster"],
        )
        
        self.assertEqual(result.exit_code, 0)