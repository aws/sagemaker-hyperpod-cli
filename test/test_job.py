import unittest
from unittest import mock
from unittest.mock import MagicMock

from click.testing import CliRunner

from hyperpod_cli.commands.job import cancel_job, get_job, list_jobs, list_pods, start_job
from hyperpod_cli.service.cancel_training_job import CancelTrainingJob
from hyperpod_cli.service.describe_training_job import DescribeTrainingJob
from hyperpod_cli.service.list_pods import ListPods
from hyperpod_cli.service.list_training_jobs import ListTrainingJobs


class JobTest(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.mock_cancel_job = MagicMock(spec=CancelTrainingJob)
        self.mock_describe_job = MagicMock(spec=DescribeTrainingJob)
        self.mock_list_jobs = MagicMock(spec=ListTrainingJobs)
        self.list_pods = MagicMock(spec=ListPods)

    @mock.patch("hyperpod_cli.service.describe_training_job.DescribeTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.describe_training_job.DescribeTrainingJob.describe_training_job"
    )
    def test_describe_job_happy_case(
        self,
        mock_describe_training_job_service_and_describe_job: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_describe_job
        mock_describe_training_job_service_and_describe_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(get_job, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    @mock.patch("hyperpod_cli.service.describe_training_job.DescribeTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.describe_training_job.DescribeTrainingJob.describe_training_job"
    )
    def test_describe_job_happy_case_with_namespace(
        self,
        mock_describe_training_job_service_and_describe_job: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_describe_job
        mock_describe_training_job_service_and_describe_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(
            get_job, ["--name", "example-job", "--namespace", "kubeflow"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    @mock.patch("hyperpod_cli.service.describe_training_job.DescribeTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.describe_training_job.DescribeTrainingJob.describe_training_job"
    )
    def test_describe_job_happy_case_with_namespace_and_verbose(
        self,
        mock_describe_training_job_service_and_describe_job: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_describe_job
        mock_describe_training_job_service_and_describe_job.return_value = {"Name": "example-job"}
        result = self.runner.invoke(
            get_job, ["--name", "example-job", "--namespace", "kubeflow", "--verbose"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("example-job", result.output)

    def test_describe_job_error_missing_name_option(self):
        result = self.runner.invoke(get_job, ["example-job"])
        self.assertIn("Missing option '--name'", result.output)

    @mock.patch("hyperpod_cli.service.describe_training_job.DescribeTrainingJob")
    @mock.patch(
        "hyperpod_cli.service.describe_training_job.DescribeTrainingJob.describe_training_job"
    )
    def test_describe_job_when_subprocess_command_gives_exception(
        self,
        mock_describe_training_job_service_and_describe_job: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_describe_job
        mock_describe_training_job_service_and_describe_job.side_effect = Exception("Boom!")
        result = self.runner.invoke(get_job, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to describe training job", result.output
        )

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_happy_case(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.return_value = {"jobs": []}
        result = self.runner.invoke(list_jobs)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_happy_case_with_namespace(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.return_value = {"jobs": []}
        result = self.runner.invoke(list_jobs, ["--namespace", "kubeflow"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_happy_case_with_all_namespace(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.return_value = {"jobs": []}
        result = self.runner.invoke(list_jobs, ["-A"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_happy_case_with_all_namespace_and_selector(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.return_value = {"jobs": []}
        result = self.runner.invoke(list_jobs, ["-A", "-l", "test=test"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("jobs", result.output)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_happy_case_with_bad_field(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.return_value = "{}"
        result = self.runner.invoke(list_jobs, ["--name", "kubeflow"])
        self.assertEqual(result.exit_code, 2)

    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs")
    @mock.patch("hyperpod_cli.service.list_training_jobs.ListTrainingJobs.list_training_jobs")
    def test_list_job_when_subprocess_command_gives_exception(
        self,
        mock_describe_training_job_service_and_list_jobs: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.mock_list_jobs
        mock_describe_training_job_service_and_list_jobs.side_effect = Exception("Boom!")
        result = self.runner.invoke(list_jobs)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Unexpected error happens when trying to list training job", result.output)

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_happy_case(
        self,
        mock_describe_training_job_service_and_list_pods: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.list_pods
        mock_describe_training_job_service_and_list_pods.return_value = "{}"
        result = self.runner.invoke(list_pods, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_happy_case_with_namespace(
        self,
        mock_describe_training_job_service_and_list_pods: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.list_pods
        mock_describe_training_job_service_and_list_pods.return_value = "{}"
        result = self.runner.invoke(list_pods, ["--name", "example-job", "--namespace", "kubeflow"])
        self.assertEqual(result.exit_code, 0)

    def test_list_pods_error_missing_name_option(self):
        result = self.runner.invoke(list_pods, ["example-job"])
        self.assertEqual(2, result.exit_code)
        self.assertIn("Missing option '--name'", result.output)

    @mock.patch("hyperpod_cli.service.list_pods.ListPods")
    @mock.patch("hyperpod_cli.service.list_pods.ListPods.list_pods_for_training_job")
    def test_list_pods_when_subprocess_command_gives_exception(
        self,
        mock_describe_training_job_service_and_list_pods: mock.Mock,
        mock_describe_training_job_service: mock.Mock,
    ):
        mock_describe_training_job_service.return_value = self.list_pods
        mock_describe_training_job_service_and_list_pods.side_effect = Exception("Boom!")
        result = self.runner.invoke(list_pods, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn(
            "Unexpected error happens when trying to list pods for training job", result.output
        )

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job")
    def test_cancel_job_happy_case(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.return_value = "{}"
        result = self.runner.invoke(cancel_job, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('{}\n', result.output)

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job")
    def test_cancel_job_happy_case_with_namespace(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.return_value = "{}"
        result = self.runner.invoke(
            cancel_job, ["--name", "example-job", "--namespace", "kubeflow"]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn('{}\n', result.output)

    def test_cancel_job_error_missing_name_option(self):
        result = self.runner.invoke(cancel_job, ["example-job"])
        self.assertIn("Missing option '--name'", result.output)

    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob")
    @mock.patch("hyperpod_cli.service.cancel_training_job.CancelTrainingJob.cancel_training_job")
    def test_cancel_job_when_subprocess_command_gives_exception(
        self,
        mock_cancel_training_job_service_and_cancel_job: mock.Mock,
        mock_cancel_training_job_service: mock.Mock,
    ):
        mock_cancel_training_job_service.return_value = self.mock_cancel_job
        mock_cancel_training_job_service_and_cancel_job.side_effect = Exception("Boom!")
        result = self.runner.invoke(cancel_job, ["--name", "example-job"])
        self.assertEqual(result.exit_code, 1)
        self.assertIn("Unexpected error happens when trying to cancel training job", result.output)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_gpu(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.g5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_custom_label_selection(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                '{"key1": "value1", "key2": "value2"}',
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    def test_submit_job_with_cli_args_label_selection_not_json_str(self, mock_yaml_dump, mock_file):
        mock_yaml_dump.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                "{NonJsonStr",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    def test_submit_job_with_cli_args_label_selection_invalid_values(
        self, mock_yaml_dump, mock_file
    ):
        mock_yaml_dump.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--label-selector",
                '{"key1": "value1", "key2": {"key3": "value2"}}',
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("os.path.exists", return_value=True)
    def test_submit_job_with_config_file(
        self, mock_exists, mock_main, mock_compose, mock_initialize_config_dir
    ):
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job, ["--config-name", "valid.config", "--config-path", "/path/to/config"]
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("yaml.safe_load")
    def test_submit_job_with_cli_args_invalid_template(
        self,
        mock_yaml_load,
    ):
        mock_yaml_load.return_value = {"invalid": "dict"}
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("os.path.exists", return_value=False)
    def test_submit_job_with_invalid_config_file_path(self, mock_exists):
        result = self.runner.invoke(
            start_job, ["--config-name", "invalid.yaml", "--config-path", "/path/to/config"]
        )
        self.assertNotEqual(result.exit_code, 0)

    @mock.patch("os.path.exists")
    @mock.patch("os.path.join")
    def test_submit_job_with_invalid_config_file(
        self,
        mock_join,
        mock_exists,
    ):
        mock_join.return_value = "/path/to/config/invalid.yaml"
        mock_exists.side_effect = lambda path: path != "/path/to/config/invalid.yaml"
        result = self.runner.invoke(
            start_job, ["--config-name", "test_job.py", "--config-path", "/path/to/config"]
        )
        self.assertNotEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    def test_submit_job_with_cli_args_command_failed(
        self, mock_yaml_dump, mock_file, mock_main, mock_compose, mock_initialize_config_dir
    ):
        mock_yaml_dump.return_value = None
        mock_main.side_effect = Exception("submit job error")
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
            ],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch(
        "hyperpod_cli.validators.job_validator.JobValidator.validate_submit_job_args",
        return_value=False,
    )
    def test_submit_job_with_invalid_args(self, mock_validate):
        result = self.runner.invoke(
            start_job,
            ["--name", "test-job", "--instance-type", "invalid-type", "--image", "invalid-image"],
        )
        self.assertEqual(result.exit_code, 1)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_auto_resume_enabled(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--auto-resume",
                "True",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_deep_health_check_passed_nodes_only(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--deep-health-check-passed-nodes-only",
                "True",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_with_kueue(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--queue-name",
                "test-priority-queue",
                "--priority",
                "high-priority",
            ],
        )
        self.assertEqual(result.exit_code, 0)

    @mock.patch("hyperpod_cli.commands.job.initialize_config_dir")
    @mock.patch("hyperpod_cli.commands.job.compose")
    @mock.patch("hyperpod_cli.commands.job.customer_launcher")
    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("yaml.dump")
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.remove", return_value=None)
    def test_submit_job_with_cli_args_with_kueue_invalid(
        self,
        mock_remove,
        mock_exists,
        mock_yaml_dump,
        mock_file,
        mock_main,
        mock_compose,
        mock_initialize_config_dir,
    ):
        mock_yaml_dump.return_value = None
        mock_main.return_value = None
        mock_compose.return_value = None
        mock_initialize_config_dir.return_value.__enter__.return_value = None
        result = self.runner.invoke(
            start_job,
            [
                "--name",
                "test-job",
                "--instance-type",
                "ml.c5.xlarge",
                "--image",
                "pytorch:1.9.0-cuda11.1-cudnn8-runtime",
                "--node-count",
                "2",
                "--queue-name",
                "test-priority-queue",
            ],
        )
        self.assertEqual(result.exit_code, 1)
