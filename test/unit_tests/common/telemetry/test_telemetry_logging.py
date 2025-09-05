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
from unittest.mock import patch, MagicMock
import pytest

from hyperpod_cli.telemetry.telemetry_logging import (
    _extract_telemetry_data,
    _construct_url,
    get_region_and_account_from_current_context,
    _hyperpod_telemetry_emitter,
)
from hyperpod_cli.telemetry.constants import Feature, Status


class TestTelemetryLogging(unittest.TestCase):

    def test_extract_telemetry_data_start_job_cli(self):
        """Test telemetry data extraction for start_job_cli"""
        result = _extract_telemetry_data(
            "start_job_cli",
            recipe="training/llama/hf_llama3_8b_seq8k_gpu_p5x16_pretrain",
            instance_type="ml.p5.48xlarge",
            node_count=2,
            config_file="/path/to/config.yaml",
            auto_resume=True,
            max_retry=3
        )
        
        self.assertIn("recipe_type=training", result)
        self.assertIn("model_family=llama", result)
        self.assertIn("config_approach=yaml", result)
        self.assertIn("instance_type=ml.p5.48xlarge", result)
        self.assertIn("node_count=2", result)
        self.assertIn("auto_resume=True", result)
        self.assertIn("max_retry=3", result)

    def test_extract_telemetry_data_start_job_cli_no_config_file(self):
        """Test telemetry data extraction for start_job_cli without config file"""
        result = _extract_telemetry_data(
            "start_job_cli",
            recipe="fine-tuning/llama/hf_llama3_70b_seq8k_gpu_lora",
            instance_type="ml.g5.2xlarge"
        )
        
        self.assertIn("recipe_type=fine-tuning", result)
        self.assertIn("model_family=llama", result)
        self.assertIn("config_approach=cli", result)

    def test_extract_telemetry_data_get_clusters_cli(self):
        """Test telemetry data extraction for get_clusters_cli"""
        result = _extract_telemetry_data(
            "get_clusters_cli",
            clusters="cluster1,cluster2,cluster3",
            namespace=["ns1", "ns2"]
        )
        
        self.assertIn("clusters_filter_provided=true", result)
        self.assertIn("clusters_count=3", result)
        self.assertIn("namespace_provided=true", result)
        self.assertIn("namespace_count=2", result)

    def test_extract_telemetry_data_list_jobs_cli(self):
        """Test telemetry data extraction for list_jobs_cli"""
        result = _extract_telemetry_data(
            "list_jobs_cli",
            job_name="test-job",
            namespace="test-ns",
            all_namespaces=True,
            selector="app=test"
        )
        
        self.assertIn("job_name_provided=true", result)
        self.assertIn("namespace_provided=true", result)
        self.assertIn("all_namespaces=true", result)
        self.assertIn("label_selector_provided=true", result)

    def test_extract_telemetry_data_get_log_cli(self):
        """Test telemetry data extraction for get_log_cli"""
        result = _extract_telemetry_data(
            "get_log_cli",
            job_name="test-job",
            pod="test-pod",
            namespace="test-ns"
        )
        
        self.assertIn("job_name_provided=true", result)
        self.assertIn("pod_name_provided=true", result)
        self.assertIn("namespace_provided=true", result)

    def test_extract_telemetry_data_patch_job_cli(self):
        """Test telemetry data extraction for patch_job_cli"""
        result = _extract_telemetry_data(
            "patch_job_cli",
            patch_type="suspend",
            job_name="test-job",
            namespace="test-ns"
        )
        
        self.assertIn("patch_type=suspend", result)
        self.assertIn("job_name_provided=true", result)
        self.assertIn("namespace_provided=true", result)

    def test_extract_telemetry_data_connect_cluster_cli(self):
        """Test telemetry data extraction for connect_cluster_cli"""
        result = _extract_telemetry_data(
            "connect_cluster_cli",
            cluster_name="test-cluster",
            namespace="test-ns"
        )
        
        self.assertIn("cluster_name_provided=true", result)
        self.assertIn("namespace_provided=true", result)

    def test_extract_telemetry_data_unknown_function(self):
        """Test telemetry data extraction for unknown function"""
        result = _extract_telemetry_data("unknown_function")
        self.assertEqual(result, "")

    def test_construct_url(self):
        """Test URL construction for telemetry"""
        url = _construct_url(
            accountId="123456789012",
            region="us-west-2",
            status="1",
            feature="10",
            failure_reason=None,
            failure_type=None,
            extra_info="test=value"
        )
        
        expected_base = "https://sm-pysdk-t-us-west-2.s3.us-west-2.amazonaws.com/telemetry?"
        self.assertTrue(url.startswith(expected_base))
        self.assertIn("x-accountId=123456789012", url)
        self.assertIn("x-status=1", url)
        self.assertIn("x-feature=10", url)
        self.assertIn("x-extra=test=value", url)

    def test_construct_url_with_failure(self):
        """Test URL construction with failure information"""
        url = _construct_url(
            accountId="123456789012",
            region="us-east-1",
            status="0",
            feature="10",
            failure_reason="Test error",
            failure_type="ValueError",
            extra_info="test=value"
        )
        
        self.assertIn("x-failureReason=Test error", url)
        self.assertIn("x-failureType=ValueError", url)

    @patch('hyperpod_cli.telemetry.telemetry_logging.subprocess.run')
    def test_get_region_and_account_from_current_context_success(self, mock_run):
        """Test successful extraction of region and account from kubectl context"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "arn:aws:eks:us-west-2:123456789012:cluster/test-cluster"
        
        region, account = get_region_and_account_from_current_context()
        
        self.assertEqual(region, "us-west-2")
        self.assertEqual(account, "123456789012")

    @patch('hyperpod_cli.telemetry.telemetry_logging.subprocess.run')
    def test_get_region_and_account_from_current_context_failure(self, mock_run):
        """Test fallback when kubectl context extraction fails"""
        mock_run.return_value.returncode = 1
        
        region, account = get_region_and_account_from_current_context()
        
        self.assertEqual(region, "us-west-2")  # DEFAULT_AWS_REGION
        self.assertEqual(account, "unknown")

    @patch('hyperpod_cli.telemetry.telemetry_logging.subprocess.run')
    def test_get_region_and_account_exception(self, mock_run):
        """Test exception handling in context extraction"""
        mock_run.side_effect = Exception("Command failed")
        
        region, account = get_region_and_account_from_current_context()
        
        self.assertEqual(region, "us-west-2")  # DEFAULT_AWS_REGION
        self.assertEqual(account, "unknown")

    @patch('hyperpod_cli.telemetry.telemetry_logging._send_telemetry_request')
    def test_telemetry_decorator_success(self, mock_send):
        """Test telemetry decorator on successful function execution"""
        @_hyperpod_telemetry_emitter(Feature.HYPERPOD_V2, "test_function")
        def test_func(arg1, arg2=None):
            return "success"
        
        result = test_func("value1", arg2="value2")
        
        self.assertEqual(result, "success")
        mock_send.assert_called_once()
        # Verify success status was sent
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], 1)  # SUCCESS status

    @patch('hyperpod_cli.telemetry.telemetry_logging._send_telemetry_request')
    def test_telemetry_decorator_failure(self, mock_send):
        """Test telemetry decorator on function failure"""
        @_hyperpod_telemetry_emitter(Feature.HYPERPOD_V2, "test_function")
        def test_func():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            test_func()
        
        mock_send.assert_called_once()
        # Verify failure status was sent
        args, kwargs = mock_send.call_args
        self.assertEqual(args[0], 0)  # FAILURE status
        self.assertEqual(args[3], "Test error")  # failure_reason
        self.assertEqual(args[4], "ValueError")  # failure_type

    def test_recipe_parsing_sequence_length(self):
        """Test recipe parsing for sequence length extraction"""
        result = _extract_telemetry_data(
            "start_job_cli",
            recipe="training/llama/hf_llama3_8b_seq16k_gpu_p5x16_pretrain"
        )
        
        self.assertIn("sequence_length=16k", result)

    def test_recipe_parsing_gpu_type(self):
        """Test recipe parsing for GPU type extraction"""
        result = _extract_telemetry_data(
            "start_job_cli",
            recipe="training/llama/hf_llama3_8b_seq8k_trn1x4_pretrain"
        )
        
        self.assertIn("gpu_type=trn1x4", result)

    def test_recipe_parsing_model_size(self):
        """Test recipe parsing for model size extraction"""
        result = _extract_telemetry_data(
            "start_job_cli",
            recipe="training/llama/hf_llama3_70b_seq8k_gpu_p5x32_pretrain"
        )
        
        self.assertIn("model_size=70b", result)

    def test_advanced_job_parameters(self):
        """Test extraction of advanced job parameters"""
        result = _extract_telemetry_data(
            "start_job_cli",
            job_kind="kubeflow/PyTorchJob",
            pull_policy="Always",
            restart_policy="OnFailure",
            queue_name="test-queue",
            priority="high",
            deep_health_check_passed_nodes_only=True,
            tasks_per_node=8,
            persistent_volume_claims="pvc1:/data",
            volumes="vol1:/host:/container",
            pre_script="echo start",
            post_script="echo end"
        )
        
        self.assertIn("job_kind=kubeflow/PyTorchJob", result)
        self.assertIn("pull_policy=Always", result)
        self.assertIn("restart_policy=OnFailure", result)
        self.assertIn("queue_name_provided=true", result)
        self.assertIn("priority_provided=true", result)
        self.assertIn("deep_health_check=true", result)
        self.assertIn("tasks_per_node=8", result)
        self.assertIn("pvc_used=true", result)
        self.assertIn("volumes_used=true", result)
        self.assertIn("pre_script_used=true", result)
        self.assertIn("post_script_used=true", result)


if __name__ == '__main__':
    unittest.main()