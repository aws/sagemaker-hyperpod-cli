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
"""Unit tests for `hyp migrate` (snapshot / converge / validate)."""
from unittest import mock

import pytest
from click.testing import CliRunner

from sagemaker.hyperpod.cli.commands.migrate import (
    migrate,
    _ansible_root,
    _build_inventory,
    _build_cluster_config,
)


@pytest.fixture
def runner():
    return CliRunner()


def test_migrate_group_has_expected_subcommands(runner):
    result = runner.invoke(migrate, ["--help"])
    assert result.exit_code == 0
    for sub in ("snapshot", "converge", "validate", "plan", "provision"):
        assert sub in result.output


def test_cluster_config_binds_plan_to_worker_only():
    cfg = _build_cluster_config(
        bucket="s3://sagemaker-bkt",
        exec_role_arn="arn:aws:iam::1:role/r",
        plan_arn="arn:aws:sagemaker:us-west-1:1:training-plan/p",
        worker_instance="ml.p5.48xlarge",
        worker_count=1,
        ondemand_instance="ml.m5.xlarge",
    )
    by_name = {g["InstanceGroupName"]: g for g in cfg}
    # worker bound to the plan
    assert by_name["worker-group"]["TrainingPlanArn"].endswith("training-plan/p")
    assert by_name["worker-group"]["InstanceType"] == "ml.p5.48xlarge"
    # controller/login on-demand, NOT on the plan
    assert "TrainingPlanArn" not in by_name["controller-machine"]
    assert "TrainingPlanArn" not in by_name["login-group"]
    assert by_name["controller-machine"]["InstanceType"] == "ml.m5.xlarge"


def test_cluster_config_no_plan_is_ondemand_only():
    cfg = _build_cluster_config(
        bucket="s3://sagemaker-bkt", exec_role_arn="arn:aws:iam::1:role/r",
        plan_arn=None, worker_instance="ml.m5.xlarge", worker_count=1,
        ondemand_instance="ml.m5.xlarge",
    )
    assert all("TrainingPlanArn" not in g for g in cfg)


def test_provision_writes_config(runner, tmp_path):
    out = tmp_path / "cfg.json"
    result = runner.invoke(
        migrate,
        ["provision", "--bucket", "s3://sagemaker-bkt",
         "--execution-role-arn", "arn:aws:iam::1:role/r",
         "--region", "us-west-1", "--out", str(out)],
    )
    assert result.exit_code == 0, result.output
    import json as _json
    cfg = _json.loads(out.read_text())
    assert {g["InstanceGroupName"] for g in cfg} == {
        "controller-machine", "login-group", "worker-group"}


@pytest.mark.parametrize("sub", ["snapshot", "converge", "validate"])
def test_subcommand_help_renders(runner, sub):
    result = runner.invoke(migrate, [sub, "--help"])
    assert result.exit_code == 0
    assert "--cluster" in result.output
    assert "--bucket" in result.output


def test_vendored_ansible_assets_present():
    root = _ansible_root()
    assert (root / "playbooks" / "snapshot.yml").is_file()
    assert (root / "playbooks" / "converge.yml").is_file()
    assert (root / "playbooks" / "validate.yml").is_file()
    assert (root / "roles" / "identity_apply").is_dir()
    assert (root / "ansible.cfg").is_file()


def test_converge_requires_run_id(runner):
    with mock.patch(
        "sagemaker.hyperpod.cli.commands.migrate._require_tooling"
    ):
        result = runner.invoke(
            migrate,
            ["converge", "--cluster", "c", "--region", "us-east-1",
             "--bucket", "s3://sagemaker-x"],
        )
    assert result.exit_code != 0
    assert "run-id" in result.output.lower()


def test_build_inventory_targets_controller(tmp_path):
    nodes = [
        {"InstanceGroupName": "controller-machine", "InstanceId": "i-1",
         "InstanceStatus": {"Status": "Running"}},
        {"InstanceGroupName": "worker-group", "InstanceId": "i-2",
         "InstanceStatus": {"Status": "Running"}},
    ]
    with mock.patch(
        "sagemaker.hyperpod.cli.commands.migrate._resolve_cluster",
        return_value=("clabc123", nodes),
    ):
        out = tmp_path / "inv.ini"
        count = _build_inventory("src", "us-east-1", None,
                                 "s3://sagemaker-bkt", out)
    text = out.read_text()
    assert count == 1
    assert "sagemaker-cluster:clabc123_controller-machine-i-1" in text
    assert "worker-group-i-2" not in text
    assert "community.aws.aws_ssm" in text
    assert "ansible_aws_ssm_bucket_name=sagemaker-bkt" in text


def test_build_inventory_errors_when_no_controller(tmp_path):
    nodes = [
        {"InstanceGroupName": "worker-group", "InstanceId": "i-2",
         "InstanceStatus": {"Status": "Running"}},
    ]
    import click
    with mock.patch(
        "sagemaker.hyperpod.cli.commands.migrate._resolve_cluster",
        return_value=("clabc123", nodes),
    ):
        with pytest.raises(click.ClickException):
            _build_inventory("src", "us-east-1", None,
                             "s3://sagemaker-bkt", tmp_path / "inv.ini")
