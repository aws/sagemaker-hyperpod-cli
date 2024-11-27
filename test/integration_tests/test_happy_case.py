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
import subprocess
import os
import time

import pytest

from hyperpod_cli.utils import setup_logger
from test.integration_tests.abstract_integration_tests import (
    AbstractIntegrationTests,
)

logger = setup_logger(__name__)


class TestHappyCase(AbstractIntegrationTests):

    @pytest.fixture(scope="class", autouse=True)
    def basic_test(self):
        super().setup()
        yield
        super().tearDown()

    def _execute_test_command(self, command):
        try:
            # Execute the command to update kubeconfig
            return subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to execute command: {command} Exception {e}")

    @pytest.mark.order(1)
    def test_hyperpod_connect_cluster(self):
        command = [
            "hyperpod",
            "connect-cluster",
            "--cluster-name",
            super().hyperpod_cli_cluster_name,
            "--region",
            "us-west-2",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(2)
    def test_start_job(self):
        config_path = os.path.expanduser("./test/integration_tests/data/basicJob.yaml")
        command = [
            "hyperpod",
            "start-job",
            "--config-file",
            config_path,
        ]

        result = self._execute_test_command(command)
        # wait for job to complete creation
        time.sleep(240)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(2)
    def test_start_job_with_quota(self):
        config_path = os.path.expanduser("./test/integration_tests/data/basicJobWithQuota.yaml")
        command = [
            "hyperpod",
            "start-job",
            "--config-file",
            config_path,
        ]

        result = self._execute_test_command(command)
        # wait for job to complete creation
        time.sleep(240)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(3)
    def test_get_job(self):
        command = [
            "hyperpod",
            "get-job",
            "--job-name",
            "hyperpod-cli-test",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test") in str(result.stdout)
        logger.info(result.stdout)
    
    @pytest.mark.order(3)
    def test_get_job_with_quota(self):
        command = [
            "hyperpod",
            "get-job",
            "--job-name",
            "hyperpod-cli-test-with-quota",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test-with-quota") in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(4)
    def test_list_jobs(self):
        command = ["hyperpod", "list-jobs"]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test") in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(5)
    def test_list_pods(self):
        command = [
            "hyperpod",
            "list-pods",
            "--job-name",
            "hyperpod-cli-test",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test") in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(6)
    def test_get_logs(self):
        command = [
            "hyperpod",
            "get-log",
            "--job-name",
            "hyperpod-cli-test",
            "--pod",
            "hyperpod-cli-test-worker-0",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(7)
    def test_cancel_job(self):
        command = [
            "hyperpod",
            "cancel-job",
            "--job-name",
            "hyperpod-cli-test",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)
    
    @pytest.mark.order(7)
    def test_cancel_job_with_quota(self):
        command = [
            "hyperpod",
            "cancel-job",
            "--job-name",
            "hyperpod-cli-test-with-quota",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(8)
    def test_start_job_with_recipe(self):
        command = [
            "hyperpod",
            "start-job",
            "--recipe",
            "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
        ]

        result = self._execute_test_command(command)
        # wait for job to complete creation
        time.sleep(240)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(9)
    def test_start_job_with_recipe_and_override_parameters(self):
        override_params = '''{
            "recipes.run.name": "test-recipe-run",
            "recipes.trainer.num_nodes": 1,
            "instance_type": "g5.48xlarge"
        }'''

        command = [
            "hyperpod",
            "start-job",
            "--recipe",
            "fine-tuning/llama/hf_llama3_8b_seq8192_gpu",
            "--override-parameters",
            override_params,
        ]

        result = self._execute_test_command(command)
        # wait for job to complete creation
        time.sleep(240)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(10)
    def test_get_job_with_recipe(self):
        command = [
            "hyperpod",
            "get-job",
            "--job-name",
            "test-recipe-run",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)
        assert "test-recipe-run" in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(11)
    def test_list_pods_with_recipe(self):
        command = [
            "hyperpod",
            "list-pods",
            "--job-name",
            "test-recipe-run",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert "test-recipe-run" in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(12)
    def test_cancel_job_with_recipe(self):
        command = [
            "hyperpod",
            "cancel-job",
            "--job-name",
            "test-recipe-run",
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)
