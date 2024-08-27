import subprocess
import os
import time

import pytest

from hyperpod_cli.utils import setup_logger
from test.integration_tests.abstract_integration_tests import AbstractIntegrationTests

logger = setup_logger(__name__)

class TestHappyCase(AbstractIntegrationTests):
    namespace = "kubeflow"

    @pytest.fixture(scope="class", autouse=True)
    def basic_test(self):
        super().setup()
        yield
        super().tearDown()

    def _execute_test_command(self, command):
        try:
            # Execute the command to update kubeconfig
            return subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to execute command: {command} Exception {e}")

    @pytest.mark.order(1)
    def test_hyperpod_connect_cluster(self):
        command = [
            "hyperpod",
            "connect-cluster",
            "--name",
            super().hyperpod_cli_cluster_name ,
            "--region",
            "us-west-2",
            "--namespace",
            self.namespace
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(2)
    def test_start_job(self):
        config_path = os.path.expanduser('~/HyperpodCLI/src/HyperpodCLI/test/integration_tests/data')
        command = [
            'hyperpod',
            'start-job',
            '--config-path',
            config_path,
            '--config-name',
            'basicJob.yaml'
        ]

        result = self._execute_test_command(command)
        # wait for job to complete creation
        time.sleep(60)
        assert result.returncode == 0
        logger.info(result.stdout)

    @pytest.mark.order(3)
    def test_get_job(self):
        command = [
            "hyperpod",
            "get-job",
            "--name",
            "hyperpod-cli-test"
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test") in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(4)
    def test_list_jobs(self):
        command = [
            "hyperpod",
            "list-jobs"
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        assert ("hyperpod-cli-test") in str(result.stdout)
        logger.info(result.stdout)

    @pytest.mark.order(5)
    def test_list_pods(self):
        command = [
            "hyperpod",
            "list-pods",
            "--name",
            "hyperpod-cli-test"
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
            "--name",
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
            "--name",
            "hyperpod-cli-test"
        ]

        result = self._execute_test_command(command)
        assert result.returncode == 0
        logger.info(result.stdout)
