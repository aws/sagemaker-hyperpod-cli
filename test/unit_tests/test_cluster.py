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
import botocore
import json
import subprocess
import unittest
from unittest import mock
from unittest.mock import MagicMock, mock_open

from click.testing import CliRunner
from kubernetes import client

from hyperpod_cli.clients.kubernetes_client import KubernetesClient
from hyperpod_cli.commands.cluster import (
    DEEP_HEALTH_CHECK_STATUS_LABEL,
    HP_HEALTH_STATUS_LABEL,
    INSTANCE_TYPE_LABEL,
    connect_cluster,
    list_clusters,
)
from hyperpod_cli.validators.validator import Validator


class ClusterTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_session = MagicMock()
        self.mock_sm_client = MagicMock()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)
        self.mock_validator = MagicMock(spec=Validator)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_to_new_cluster_success(
        self,
        mock_open_test,
        mock_validate_aws_credentials: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_session: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(connect_cluster, ["--cluster-name", "my-cluster"])
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch("logging.Logger.debug")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_to_new_cluster_success_debug_mode(
        self,
        mock_open_test,
        mock_validate_aws_credentials: mock.Mock,
        mock_debug: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_session: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            connect_cluster, ["--cluster-name", "my-cluster", "--debug"]
        )
        self.assertEqual(result.exit_code, 0)
        mock_debug.assert_called()

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_with_region_success(
        self,
        mock_open_test,
        mock_validate_aws_credentials: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_session: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            connect_cluster, ["--cluster-name", "my-cluster", "--region", "us-east-1"]
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_describe_cluster_failure(
        self,
        mock_open_test,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
    ):
        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.side_effect = Exception(
            "Failed to describe cluster"
        )

        result = self.runner.invoke(connect_cluster, ["--cluster-name", "my-cluster"])
        self.assertEqual(result.exit_code, 1)

    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_sm_client_no_region_failure(
        self,
        mock_open_test,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
    ):
        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        self.mock_session.client.side_effect = botocore.exceptions.NoRegionError()
        mock_session.return_value = self.mock_session
        result = self.runner.invoke(connect_cluster, ["--cluster-name", "my-cluster"])
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_subprocess_failure(
        self,
        mock_open_test,
        mock_subprocess_run: mock.Mock,
        mock_session: mock.Mock,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_session.return_value = self.mock_session
        self.mock_session.client.return_value = self.mock_sm_client
        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
                }
            }
        }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["aws", "eks", "update-kubeconfig"]
        )
        result = self.runner.invoke(connect_cluster, ["--cluster-name", "my-cluster"])
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.cluster.ClusterValidator")
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_validator_failure(self, mock_open_test, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = False

        result = self.runner.invoke(connect_cluster, ["--cluster-name", "my-cluster"])
        self.assertEqual(result.exit_code, 1)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch("logging.Logger.debug")
    def test_list_clusters_debug_mode(
        self,
        mock_debug: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters, ["--debug"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        json.loads(result.output)
        mock_debug.assert_called()

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_maximum_number(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        eks_cluster_arns = [
            f"arn:aws:eks:us-west-2:123456789012:cluster/cluster-{i}"
            for i in range(100)
        ]
        mock_validate_cluster_and_get_eks_arn.side_effect = eks_cluster_arns

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        sm_cluster_details = [
            {
                "Orchestrator": {
                    "Eks": {
                        "ClusterArn": f"arn:aws:eks:us-west-2:123456789012:cluster/cluster-{i}"
                    }
                }
            }
            for i in range(100)
        ]
        self.mock_sm_client.describe_cluster.side_effect = sm_cluster_details
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response_over_maximum()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        output = json.loads(result.output)
        # Each cluster has 2 instance type, so total output size is 2 * 50 = 100
        self.assertTrue(len(output) == 100)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_no_cluster_summary(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = {"Key": "Value"}
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)
        # Expect JSON output
        json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_table_output(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters, ["--output", "table"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect a table format output
        with self.assertRaises(Exception):
            json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "hyperpod_cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_list_clusters_with_deep_health_check_enabled_and_gpu_devices(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {"node-name-1": 1, "node-name-2": 2}
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_deep_health_check_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "hyperpod_cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_list_clusters_with_unexpected_health_status(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {"node-name-1": 1, "node-name-2": 2}
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list_unexpected_label()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "hyperpod_cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_list_clusters_with_no_status(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {"node-name-1": 1, "node-name-2": 2}
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list_no_status()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)

    @mock.patch("hyperpod_cli.commands.cluster.ClusterValidator")
    def test_list_clusters_credentials_failure(self, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = False

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.cluster.ClusterValidator")
    @mock.patch("boto3.Session")
    def test_list_clusters_sm_client_no_region_error(
        self,
        mock_session: mock.Mock,
        mock_validator_cls,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        self.mock_session.client.side_effect = botocore.exceptions.NoRegionError()
        mock_session.return_value = self.mock_session
        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.cluster.ClusterValidator")
    @mock.patch("boto3.Session")
    def test_list_clusters_sm_client_unexpected_error(
        self,
        mock_session: mock.Mock,
        mock_validator_cls,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        self.mock_session.client.side_effect = Exception("Unexpected error")
        mock_session.return_value = self.mock_session
        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_with_clusters_list(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters, ["--clusters", "cluster-3"])
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)
        self.assertIn("cluster-3", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_failed_list_cluster_error(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
                }
            }
        }
        self.mock_sm_client.list_clusters.side_effect = Exception("Unexpected error")
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 1)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_failed_unexpected_error(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.side_effect = Exception(
            "Unexpected error"
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = (
            "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
        )

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "hyperpod_cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("hyperpod_cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_list_clusters_skipped_not_eks_clusters(
        self,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        self.mock_k8s_client.list_node_with_temp_config.return_value = (
            _generate_nodes_list()
        )
        mock_kubernetes_client.return_value = self.mock_k8s_client

        mock_validate_aws_credentials.validate_aws_credential.return_value = None
        mock_validate_cluster_and_get_eks_arn.return_value = None

        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-3"
                }
            }
        }
        self.mock_sm_client.list_clusters.return_value = (
            _generate_list_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_clusters)
        self.assertEqual(result.exit_code, 0)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)


def _generate_nodes_list():
    return [
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-1",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Schedulable",
                    INSTANCE_TYPE_LABEL: "instance-type-1",
                },
            ),
        ),
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-2",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Unschedulable",
                    INSTANCE_TYPE_LABEL: "instance-type-2",
                },
            ),
        ),
    ]


def _generate_deep_health_check_nodes_list():
    return [
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-1",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Schedulable",
                    INSTANCE_TYPE_LABEL: "ml.p4d.24xlarge",
                    DEEP_HEALTH_CHECK_STATUS_LABEL: "Passed",
                },
            ),
            status=client.V1NodeStatus(allocatable={"nvidia.com/gpu": 24}),
        ),
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-2",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Schedulable",
                    DEEP_HEALTH_CHECK_STATUS_LABEL: "Passed",
                    INSTANCE_TYPE_LABEL: "ml.trn1.32xlarge",
                },
            ),
            status=client.V1NodeStatus(allocatable={"aws.amazon.com/neurondevice": 16}),
        ),
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-3",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Unschedulable",
                    INSTANCE_TYPE_LABEL: "ml.trn1.32xlarge",
                },
            ),
            status=client.V1NodeStatus(allocatable={"aws.amazon.com/neurondevice": 16}),
        ),
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-3",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Schedulable",
                    INSTANCE_TYPE_LABEL: "ml.trn1.32xlarge",
                },
            ),
        ),
    ]


def _generate_nodes_list_unexpected_label():
    return [
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-1",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Unexpected",
                    INSTANCE_TYPE_LABEL: "instance-type-1",
                },
            ),
        ),
    ]


def _generate_nodes_list_no_status():
    return [
        client.V1Node(
            metadata=client.V1ObjectMeta(
                name="node-name-1",
                labels={
                    HP_HEALTH_STATUS_LABEL: "Schedulable",
                    INSTANCE_TYPE_LABEL: "instance-type-1",
                },
            ),
        ),
    ]


def _generate_list_clusters_response():
    return {
        "ClusterSummaries": [{"ClusterName": "cluster-1"}, {"ClusterName": "cluster-2"}]
    }


def _generate_list_clusters_response_over_maximum():
    cluster_list = [{"ClusterName": f"cluster-{i+1}"} for i in range(100)]
    return {"ClusterSummaries": cluster_list}
