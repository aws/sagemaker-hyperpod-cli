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

from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)
from kubernetes.client import V1ResourceAttributes
from sagemaker.hyperpod.cli.service.list_training_jobs import (
    ListTrainingJobs,
)

from kubernetes.client.rest import ApiException
from tabulate import tabulate

SAMPLE_OUTPUT = {
    "items": [
        {
            "metadata": {
                "name": "test-name",
                "namespace": "test-namespace",
            },
            "status": {
                "startTime": "test-time",
                "conditions": [
                    {
                        "type": "Succeeded",
                        "lastTransitionTime": "2023-08-27T22:47:57Z",
                    }
                ],
            },
            "spec": {
                "pytorchReplicaSpecs": {
                    "Worker": {
                        "template": {
                            "metadata": {
                                "labels": {
                                    "kueue.x-k8s.io/priority-class": "priority-1"
                                }
                            }
                        }
                    }
                }
            }
        },
        {
            "metadata": {
                "name": "test-name1",
                "namespace": "test-namespace1",
            },
            "status": {
                "startTime": "test-time1",
                "conditions": [
                    {
                        "type": "Created",
                        "lastTransitionTime": "2023-08-27T22:47:57Z",
                    },
                    {
                        "type": "Running",
                        "lastTransitionTime": "2024-08-27T22:47:57Z",
                    },
                ],
            },
            "spec": {
                "pytorchReplicaSpecs": {
                    "Worker": {
                        "template": {
                            "spec": {
                                "priorityClassName": "priority-2"
                            }
                        }
                    }
                }
            }
        },
        {
            "metadata": {
                "name": "test-name2",
                "namespace": "test-namespace1",
            },
            "status": {
                "startTime": "test-time1",
                "conditions": [
                    {
                        "type": "Created",
                        "lastTransitionTime": "2024-08-27T22:47:57Z",
                    }
                ],
            },
            "spec": {
                "pytorchReplicaSpecs": {
                    "Worker": {
                        "template": {
                            "spec": {
                                "priorityClassName": "priority-3",
                            },
                            "metadata": {
                                "labels": {
                                    "kueue.x-k8s.io/priority-class": "priority-4"
                                }
                            }
                        }
                    }
                }
            }
        },
    ]
}
INVALID_OUTPUT = {
    "items": [
        {
            "status": {
                "startTime": "test-time",
                "conditions": [{"type": "Succeeded"}],
            },
        }
    ]
}
OUTPUT_WITHOUT_STATUS = {
    "items": [
        {
            "metadata": {
                "name": "test-name",
                "namespace": "test-namespace",
            },
        }
    ]
}


class ListTrainingJobsTest(unittest.TestCase):
    def setUp(self):
        self.mock_list_training_jobs = ListTrainingJobs()
        self.mock_k8s_client = MagicMock(spec=KubernetesClient)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_with_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(
            "namespace", None, None, None
        )
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)
        self.assertIn("Running", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)
        self.assertIn("Running", result)

    @mock.patch("sagemaker.hyperpod.cli.service.discover_namespaces.DiscoverNamespaces.discover_accessible_namespace")
    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_with_namespace_auto_discover(
        self,
        mock_kubernetes_client: mock.Mock,
        mock_discover_accessible_namespace: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        mock_discover_accessible_namespace.return_value = "discovered-namespace"
        self.mock_k8s_client.get_current_context_namespace.return_value = None
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None, None)
        mock_discover_accessible_namespace.assert_called_once_with(
            V1ResourceAttributes(
                verb="list",
                group="kubeflow.org",
                resource="pytorchjobs",
            )
        )
        self.mock_k8s_client.list_training_jobs.assert_called_once_with(
            namespace="discovered-namespace",
            label_selector=None,
        )

        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)
        self.assertIn("priority-1", result)
        self.assertIn("priority-2", result)
        self.assertIn("priority-4", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_without_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.get_current_context_namespace.return_value = "namespace"
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, None, None, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = SAMPLE_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None, None)
        self.assertIn("test-name", result)
        self.assertIn("test-name1", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_api_exception(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.side_effect = ApiException(
            status="Failed", reason="unexpected"
        )
        with self.assertRaises(RuntimeError):
            self.mock_list_training_jobs.list_training_jobs(None, True, None, None)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_no_jobs(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = {"items": []}
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None, None)
        self.assertNotIn("test-name", result)
        self.assertNotIn("test-name1", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_metadata(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = INVALID_OUTPUT
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None, None)
        self.assertNotIn("name", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_all_namespace_missing_status(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.list_namespaces.return_value = ["namespace"]
        self.mock_k8s_client.list_training_jobs.return_value = OUTPUT_WITHOUT_STATUS
        result = self.mock_list_training_jobs.list_training_jobs(None, True, None, None)
        self.assertNotIn("State: null", result)

    @mock.patch("sagemaker.hyperpod.cli.clients.kubernetes_client.KubernetesClient.__new__")
    def test_list_training_jobs_namespace_not_exist(
        self,
        mock_kubernetes_client: mock.Mock,
    ):
        mock_kubernetes_client.return_value = self.mock_k8s_client
        self.mock_k8s_client.check_if_namespace_exists.return_value = False
        with self.assertRaises(ValueError):
            self.mock_list_training_jobs.list_training_jobs("abcdef", False, None, None)

    def test_generate_table_with_no_priority_header_and_values(self):
        list_training_jobs = ListTrainingJobs()
        output_jobs = {
            "jobs": [
                {
                    "Name": "job1",
                    "Namespace": "namespace1",
                    "CreationTime": "2023-01-01T00:00:00Z",
                    "State": "Running"
                }
            ]
        }
        priority_header_required = False

        result = list_training_jobs._generate_table(output_jobs, priority_header_required)

        expected_headers = ["Name", "Namespace", "CreationTime", "State"]
        expected_jobs = [["job1", "namespace1", "2023-01-01T00:00:00Z", "Running"]]
        expected_result = tabulate(expected_jobs, headers=expected_headers, tablefmt="presto")

        assert result == expected_result

    def test_generate_table_with_priority_header_and_priority_values(self):
        list_training_jobs = ListTrainingJobs()
        output_jobs = {
            "jobs": [
                {
                    "Name": "job1",
                    "Namespace": "namespace1",
                    "CreationTime": "2023-01-01T00:00:00Z",
                    "State": "Running",
                    "priority": "high"
                },
                {
                    "Name": "job2",
                    "Namespace": "namespace2",
                    "CreationTime": "2023-01-02T00:00:00Z",
                    "State": "Completed",
                    "priority": "low"
                }
            ]
        }
        priority_header_required = True

        result = list_training_jobs._generate_table(output_jobs, priority_header_required)

        expected_headers = ["Name", "Namespace", "CreationTime", "State", "Priority"]
        expected_jobs = [
            ["job1", "namespace1", "2023-01-01T00:00:00Z", "Running", "high"],
            ["job2", "namespace2", "2023-01-02T00:00:00Z", "Completed", "low"]
        ]
        expected_result = tabulate(expected_jobs, headers=expected_headers, tablefmt="presto")

        assert result == expected_result

    def test_generate_table_with_priority_header_but_no_priority_value(self):
        list_training_jobs = ListTrainingJobs()
        output_jobs = {
            "jobs": [
                {
                    "Name": "job1",
                    "Namespace": "namespace1",
                    "CreationTime": "2023-01-01T00:00:00Z",
                    "State": "Running"
                }
            ]
        }
        priority_header_required = True

        result = list_training_jobs._generate_table(output_jobs, priority_header_required)

        expected_headers = ["Name", "Namespace", "CreationTime", "State", "Priority"]
        expected_jobs = [["job1", "namespace1", "2023-01-01T00:00:00Z", "Running", "NA"]]
        expected_result = tabulate(expected_jobs, headers=expected_headers, tablefmt="presto")

        assert result == expected_result

    def test_generate_table_empty_jobs(self):
        list_training_jobs = ListTrainingJobs()
        output_jobs = {"jobs": []}
        priority_header_required = False

        result = list_training_jobs._generate_table(output_jobs, priority_header_required)

        expected_headers = ["Name", "Namespace", "CreationTime", "State"]
        expected_result = tabulate([], headers=expected_headers, tablefmt="presto")

        assert result == expected_result
