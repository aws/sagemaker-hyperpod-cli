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
from kubernetes.client import (
    V1Namespace, 
    V1ObjectMeta,
)
from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)
from sagemaker.hyperpod.cli.commands.cluster import (
    DEEP_HEALTH_CHECK_STATUS_LABEL,
    HP_HEALTH_STATUS_LABEL,
    INSTANCE_TYPE_LABEL,
    set_cluster_context,
    list_cluster,
)
from sagemaker.hyperpod.cli.validators.validator import Validator


class ClusterTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_session = MagicMock()
        self.mock_sm_client = MagicMock()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)
        self.mock_validator = MagicMock(spec=Validator)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "my-cluster"],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch("logging.Logger.debug")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            set_cluster_context,
            [
                "--cluster-name",
                "my-cluster",
                "--debug",
            ],
        )
        self.assertEqual(result.exit_code, 0)
        mock_debug.assert_called()

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("boto3.Session")
    @mock.patch("subprocess.run")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.return_value = MagicMock(returncode=0)
        result = self.runner.invoke(
            set_cluster_context,
            [
                "--cluster-name",
                "my-cluster",
                "--region",
                "us-east-1",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
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

        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "my-cluster"],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
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
        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "my-cluster"],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_k8s_client.context_exists.return_value = False
        self.mock_k8s_client.set_context.return_value = None
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=[
                "aws",
                "eks",
                "update-kubeconfig",
            ],
        )
        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "my-cluster"],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator")
    @mock.patch("builtins.open", new_callable=mock_open)
    def test_connect_validator_failure(self, mock_open_test, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = False

        result = self.runner.invoke(
            set_cluster_context,
            ["--cluster-name", "my-cluster"],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters(
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch("logging.Logger.debug")
    def test_get_clusters_debug_mode(
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster, ["--debug"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        json.loads(result.output)
        mock_debug.assert_called()

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters_maximum_number(
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
            _generate_get_clusters_response_over_maximum()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect JSON output
        output = json.loads(result.output)
        self.assertEqual(len(output), 50)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters_no_cluster_summary(
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = {"Key": "Value"}
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)
        # Expect JSON output - should be empty list when no ClusterSummaries
        output = json.loads(result.output)
        self.assertEqual(output, [])

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters_table_output(
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster, ["--output", "table"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)
        # Expect a table format output
        with self.assertRaises(Exception):
            json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "sagemaker.hyperpod.cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_get_clusters_with_deep_health_check_enabled_and_gpu_devices(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {
            "node-name-1": 1,
            "node-name-2": 2,
        }
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        self.assertIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "sagemaker.hyperpod.cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_get_clusters_with_unexpected_health_status(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {
            "node-name-1": 1,
            "node-name-2": 2,
        }
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
            },
            },
            "InstanceGroups": [{"CurrentCount": 2}]
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    @mock.patch(
        "sagemaker.hyperpod.cli.service.list_pods.ListPods.list_pods_and_get_requested_resources_group_by_node_name"
    )
    def test_get_clusters_with_no_status(
        self,
        mock_list_pods: mock.Mock,
        mock_subprocess_run: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_session: mock.Mock,
        mock_load_kube_config: mock.Mock,
    ):
        mock_list_pods.return_value = {
            "node-name-1": 1,
            "node-name-2": 2,
        }
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)

    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator")
    def test_get_clusters_credentials_failure(self, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = False

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator")
    @mock.patch("boto3.Session")
    def test_get_clusters_sm_client_no_region_error(
        self,
        mock_session: mock.Mock,
        mock_validator_cls,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        self.mock_session.client.side_effect = botocore.exceptions.NoRegionError()
        mock_session.return_value = self.mock_session
        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("sagemaker.hyperpod.cli.commands.cluster.ClusterValidator")
    @mock.patch("boto3.Session")
    def test_get_clusters_sm_client_unexpected_error(
        self,
        mock_session: mock.Mock,
        mock_validator_cls,
    ):
        mock_validator = mock_validator_cls.return_value
        mock_validator.validate_aws_credential.return_value = True
        self.mock_session.client.side_effect = Exception("Unexpected error")
        mock_session.return_value = self.mock_session
        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 1)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(
            list_cluster,
            ["--clusters", "cluster-3"],
        )
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)
        self.assertIn("cluster-3", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
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
            },
            "InstanceGroups": [{"CurrentCount": 2}]                },
            }

        self.mock_sm_client.list_clusters.side_effect = Exception("Unexpected error")
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 1)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
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
            },
            },
            "InstanceGroups": [{"CurrentCount": 2}]
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
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
            },
            },
            "InstanceGroups": [{"CurrentCount": 2}]
            }

        self.mock_sm_client.list_clusters.return_value = (
            _generate_get_clusters_response()
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(list_cluster)
        self.assertEqual(result.exit_code, 0)
        # clusters got skipped because exception encounter during processing clusters
        self.assertNotIn("cluster-1", result.output)
        self.assertNotIn("cluster-2", result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters_with_sm_managed_namespace(
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
        self.mock_k8s_client.get_sagemaker_managed_namespace.return_value = V1Namespace(
            metadata=V1ObjectMeta(
                name="test-namespace",
                labels={
                    "sagemaker.amazonaws.com/sagemaker-managed-queue": "true",
                    "sagemaker.amazonaws.com/quota-allocation-id": "test-team",
                },
            ),
        )
        self.mock_k8s_client.get_cluster_queue.return_value = _generate_get_cluster_queue_response()

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
            },
            },
            "InstanceGroups": [{"CurrentCount": 2}]
            }

        self.mock_sm_client.list_clusters.return_value = (
            {
                "ClusterSummaries": [
                    {"ClusterName": "cluster-1"},
                ]
            }
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(
            list_cluster,
            [
                "-n",
                "test-namespace",
            ],
            catch_exceptions=False,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)
        # For instance-type-1
        self.assertIn("test-namespace", result.output)
        self.assertIn('"TotalAcceleratorDevices": 1', result.output)
        self.assertIn('"AvailableAcceleratorDevices": 0', result.output)
        # For instance-type-2
        self.assertIn('"TotalAcceleratorDevices": "N/A"', result.output)
        self.assertIn('"AvailableAcceleratorDevices": "N/A"', result.output)
        # Expect JSON output
        json.loads(result.output)

    @mock.patch("kubernetes.config.load_kube_config")
    @mock.patch("boto3.Session")
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_aws_credential"
    )
    @mock.patch(
        "sagemaker.hyperpod.cli.commands.cluster.ClusterValidator.validate_cluster_and_get_eks_arn"
    )
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("subprocess.run")
    def test_get_clusters_with_not_sm_managed_namespace(
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
        self.mock_k8s_client.get_sagemaker_managed_namespace.return_value = None

        self.mock_sm_client.describe_cluster.return_value = {
            "Orchestrator": {
                "Eks": {
                    "ClusterArn": "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
            },
            },
            "InstanceGroups": [{"CurrentCount": 2}]
        }
        self.mock_sm_client.list_clusters.return_value = (
            {
                "ClusterSummaries": [
                    {"ClusterName": "cluster-1"},
                ]
            }
        )
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        result = self.runner.invoke(
            list_cluster,
            [
                "-n",
                "test-namespace",
            ],
            catch_exceptions=False,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("cluster-1", result.output)

        # For both instance-type-1 and instance-type-2
        self.assertIn("test-namespace", result.output)
        self.assertIn('"TotalAcceleratorDevices": "N/A"', result.output)
        self.assertIn('"AvailableAcceleratorDevices": "N/A"', result.output)
        # Expect JSON output
        json.loads(result.output)

    @mock.patch("subprocess.run")
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    @mock.patch("sagemaker.hyperpod.cli.validators.cluster_validator.ClusterValidator.validate_cluster_and_get_eks_arn")
    @mock.patch("sagemaker.hyperpod.cli.validators.cluster_validator.ClusterValidator.validate_aws_credential")
    @mock.patch("boto3.Session")
    @mock.patch("kubernetes.config.load_kube_config")
    def test_list_clusters_with_zero_instances_shows_zero_nodes(
        self,
        mock_load_kube_config: mock.Mock,
        mock_session: mock.Mock,
        mock_validate_aws_credentials: mock.Mock,
        mock_validate_cluster_and_get_eks_arn: mock.Mock,
        mock_kubernetes_client: mock.Mock,
        mock_subprocess_run: mock.Mock,
    ):
        """Test that clusters with 0 instances are shown with 0 nodes."""
        # Arrange
        mock_validate_aws_credentials.return_value = True
        mock_validate_cluster_and_get_eks_arn.return_value = "arn:aws:eks:us-west-2:123456789012:cluster/cluster-1"
        mock_load_kube_config.return_value = None
        mock_subprocess_run.return_value = None

        # Mock cluster list response
        self.mock_sm_client.list_clusters.return_value = {
            "ClusterSummaries": [
                {"ClusterName": "zero-instance-cluster"}
            ]
        }
        
        # Mock describe_cluster to return cluster with 0 instances
        self.mock_sm_client.describe_cluster.return_value = {
            "ClusterStatus": "Failed",
            "ClusterName": "zero-instance-cluster",
            "InstanceGroups": [
                {"CurrentCount": 0},  # Zero instances
                {"CurrentCount": 0}   # Zero instances
            ]
        }
        
        self.mock_session.client.return_value = self.mock_sm_client
        mock_session.return_value = self.mock_session

        # Act
        result = self.runner.invoke(list_cluster)

        # Assert
        self.assertEqual(result.exit_code, 0)
        self.assertIn("zero-instance-cluster", result.output)
        # Should contain TotalNodes with 0 value
        self.assertIn('"TotalNodes": 0', result.output)


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


def _generate_get_clusters_response():
    return {
        "ClusterSummaries": [
            {"ClusterName": "cluster-1"},
            {"ClusterName": "cluster-2"},
        ]
    }

def _generate_get_cluster_queue_response():
    return {
        "kind": "ClusterQueue",
        "metadata": {
            "name": "test-queue",
        },
        "spec": {
            "resourceGroups": [
                {
                    "coveredResources": ["cpu", "memory", "nvidia.com/gpu"],
                    "flavors": [
                        {
                            "name": "instance-type-1",
                            "resources": [
                                {"name": "cpu", "nominalQuota": 10},
                                {"name": "memory", "nominalQuota": "10Gi"},
                                {"name": "nvidia.com/gpu", "nominalQuota": 1},
                            ]
                        },
                    ]
                },
            ],
        },
        "status": {
            "flavorsUsage": [
                {
                    "name": "instance-type-1",
                    "resources": [
                        {"name": "cpu", "total": 5, "borrowed": 1},
                        {"name": "memory", "total": "4Gi", "borrowed": "0Gi"},
                        {"name": "nvidia.com/gpu", "total": 1, "borrowed": 0}
                    ]
                },
            ]
        }
    }

def _generate_get_clusters_response_over_maximum():
    cluster_list = [{"ClusterName": f"cluster-{i+1}"} for i in range(100)]
    return {"ClusterSummaries": cluster_list}
