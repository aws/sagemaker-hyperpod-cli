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
"""
`hyp migrate` — capture a HyperPod Slurm cluster's identity + Slurm state and
reproduce it on an equivalent cluster in a different AZ/Region.

Wraps the vendored migration Ansible playbooks (snapshot / converge / validate)
and drives them over the SSM `aws_ssm` connection plugin against a runtime-
generated inventory built from `list-cluster-nodes`. See the module README for
the full architecture.

Note: this migrates identity (users, groups, pinned UID/GID, ~/.ssh perms) and
Slurm configuration + accounting *configuration* (accounts/users/associations/
QOS). Bulk datasets on /fsx remain the customer's responsibility via their FSx
Data Repository Associations; historical job records are out of scope.
"""
import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

import boto3
import click

from sagemaker.hyperpod.cli.utils import setup_logger

logger = setup_logger(__name__)

CONTROLLER_GROUP_HINTS = ("controller", "head", "login")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _ansible_root() -> Path:
    """Locate the vendored ansible assets shipped with the package."""
    # Assets live in the sibling `migrate` package: cli/migrate/ansible.
    root = Path(__file__).resolve().parent.parent / "migrate" / "ansible"
    if not root.is_dir():
        raise click.ClickException(
            f"Bundled ansible assets not found at {root}. "
            "The package may be installed incorrectly."
        )
    return root


def _require_tooling() -> None:
    """Fail early with a clear message if runtime prerequisites are missing."""
    missing = []
    if shutil.which("ansible-playbook") is None:
        missing.append("ansible-core (provides ansible-playbook)")
    if shutil.which("session-manager-plugin") is None:
        missing.append("session-manager-plugin (AWS Session Manager plugin)")
    if missing:
        raise click.ClickException(
            "Missing required tooling for `hyp migrate`:\n  - "
            + "\n  - ".join(missing)
            + "\n\nInstall with:\n"
            "  pip install 'sagemaker-hyperpod[migrate]'\n"
            "  ansible-galaxy collection install amazon.aws community.aws ansible.posix\n"
            "  # plus the AWS Session Manager plugin"
        )


def _resolve_cluster(cluster_name: str, region: str):
    sm = boto3.client("sagemaker", region_name=region)
    desc = sm.describe_cluster(ClusterName=cluster_name)
    cluster_id = desc["ClusterArn"].rsplit("/", 1)[-1]
    nodes = sm.list_cluster_nodes(ClusterName=cluster_name).get(
        "ClusterNodeSummaries", []
    )
    return cluster_id, nodes


def _build_inventory(
    cluster_name: str,
    region: str,
    groups: Optional[str],
    transport_bucket: str,
    out_path: Path,
) -> int:
    """Generate an Ansible INI inventory targeting the controller over aws_ssm.

    Returns the number of controller hosts resolved.
    """
    cluster_id, nodes = _resolve_cluster(cluster_name, region)
    wanted = {g.strip() for g in (groups or "").split(",") if g.strip()}

    controllers: List[str] = []
    bucket = transport_bucket.replace("s3://", "").split("/")[0]
    for n in nodes:
        if n.get("InstanceStatus", {}).get("Status") != "Running":
            continue
        group = n["InstanceGroupName"]
        if wanted and group not in wanted:
            continue
        low = group.lower()
        if wanted or any(k in low for k in CONTROLLER_GROUP_HINTS):
            iid = n["InstanceId"]
            target = f"sagemaker-cluster:{cluster_id}_{group}-{iid}"
            controllers.append(
                f"{group}-{iid} ansible_host={target} "
                f"ansible_connection=community.aws.aws_ssm "
                f"ansible_aws_ssm_region={region} "
                f"ansible_aws_ssm_instance_id={target} "
                f"ansible_aws_ssm_bucket_name={bucket}"
            )

    if not controllers:
        raise click.ClickException(
            f"No running controller/login nodes found for cluster '{cluster_name}'. "
            "Pass --groups to target specific instance groups."
        )

    out_path.write_text(
        "[controller]\n"
        + "\n".join(controllers)
        + "\n\n[all:vars]\nansible_python_interpreter=/usr/bin/python3\n"
    )
    return len(controllers)


def _run_playbook(
    playbook: str,
    inventory: Path,
    extra_vars: dict,
    debug: bool,
) -> None:
    root = _ansible_root()
    cmd = [
        "ansible-playbook",
        str(root / "playbooks" / playbook),
        "-i",
        str(inventory),
    ]
    for k, v in extra_vars.items():
        cmd += ["-e", f"{k}={v}"]
    if debug:
        cmd.append("-vvv")

    env = dict(os.environ)
    env.setdefault("ANSIBLE_HOST_KEY_CHECKING", "False")
    # Run with the vendored ansible.cfg as CWD so roles_path resolves.
    logger.info("Running: %s", " ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(root), env=env)
    if proc.returncode != 0:
        raise click.ClickException(
            f"Ansible playbook '{playbook}' failed (exit {proc.returncode}). "
            "Re-run with --debug for detail."
        )


def _default_run_id() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")


def _describe_training_plan(plan_arn: str, region: str) -> dict:
    """Resolve a training plan's reserved capacity: instance type, AZ, count.

    Training-plan capacity is AZ-pinned; the target cluster subnet MUST be
    placed in the plan's reserved AZ or the capacity will not attach.
    """
    sm = boto3.client("sagemaker", region_name=region)
    name = plan_arn.rsplit("/", 1)[-1]
    tp = sm.describe_training_plan(TrainingPlanName=name)
    caps = tp.get("ReservedCapacitySummaries", [])
    if not caps:
        raise click.ClickException(
            f"Training plan '{name}' has no reserved capacity summaries."
        )
    cap = caps[0]
    return {
        "arn": tp["TrainingPlanArn"],
        "status": tp.get("Status"),
        "instance_type": cap.get("InstanceType"),
        "availability_zone": cap.get("AvailabilityZone"),
        "availability_zone_id": cap.get("AvailabilityZoneId"),
        "total_instances": cap.get("TotalInstanceCount"),
        "available_instances": tp.get("AvailableInstanceCount"),
    }


def _build_cluster_config(
    bucket: str,
    exec_role_arn: str,
    plan_arn: Optional[str],
    worker_instance: str,
    worker_count: int,
    ondemand_instance: str,
) -> list:
    """Build a HyperPod instance-group config.

    The worker group binds the training-plan capacity (TrainingPlanArn is a
    per-instance-group field); controller and login run on-demand, since a plan
    typically reserves only the accelerated worker instances.
    """
    uri = f"s3://{bucket.replace('s3://', '').split('/')[0]}/LifecycleScripts/base-config/"
    lcs = {"SourceS3Uri": uri, "OnCreate": "on_create.sh"}

    def group(name, instance, count, on_plan=False):
        g = {
            "InstanceGroupName": name,
            "InstanceType": instance,
            "InstanceCount": count,
            "LifeCycleConfig": lcs,
            "ExecutionRole": exec_role_arn,
            "ThreadsPerCore": 1,
        }
        if on_plan and plan_arn:
            g["TrainingPlanArn"] = plan_arn
        return g

    return [
        group("controller-machine", ondemand_instance, 1),
        group("login-group", ondemand_instance, 1),
        group("worker-group", worker_instance, worker_count, on_plan=bool(plan_arn)),
    ]


# --------------------------------------------------------------------------- #
# Command group
# --------------------------------------------------------------------------- #
@click.group("migrate")
def migrate():
    """Migrate a HyperPod Slurm cluster to a new AZ/Region.

    Captures user identity, ~/.ssh, and Slurm configuration from a SOURCE
    cluster into a versioned S3 manifest, then reproduces that state on a
    TARGET cluster with pinned numeric UID/GID and a fail-closed validation
    gate. Storage: the target FSx/OpenZFS filesystems are created and /home is
    restored; bulk /fsx datasets are re-attached by the customer via FSx DRA.

    Typical flow:

    \b
      hyp migrate snapshot  --cluster SRC --region us-east-2 --bucket s3://sagemaker-...-artifacts --run-id RUN
      hyp migrate plan      --plan-arn <target-training-plan> --region us-west-1
      hyp migrate provision --bucket s3://sagemaker-...-tgt --execution-role-arn <role> --plan-arn <plan> --region us-west-1
      hyp migrate converge  --cluster TGT --region us-west-1 --bucket s3://sagemaker-...-artifacts --run-id RUN
      hyp migrate validate  --cluster TGT --region us-west-1 --bucket s3://sagemaker-...-artifacts --run-id RUN

    Training plans: capacity is AZ-pinned and bound per instance group. The
    worker group draws from the plan (TrainingPlanArn); controller/login run
    on-demand. Cross-Region migrations require copying the manifest to a
    sagemaker-* bucket in the target Region before converge.
    """
    pass


def _common_options(f):
    f = click.option("--cluster", "cluster_name", required=True,
                     help="HyperPod cluster name.")(f)
    f = click.option("--region", required=True, help="AWS region of the cluster.")(f)
    f = click.option("--bucket", required=True,
                     help="S3 artifact bucket for the manifest + SSM transport "
                          "(must be named sagemaker-*).")(f)
    f = click.option("--run-id", default=None,
                     help="Migration run id (shared across snapshot/converge/"
                          "validate). Defaults to a UTC timestamp for snapshot.")(f)
    f = click.option("--groups", default=None,
                     help="Comma-separated instance groups to target "
                          "(default: auto-detect controller/login).")(f)
    f = click.option("--debug", is_flag=True, help="Enable verbose Ansible output.")(f)
    return f


@migrate.command("snapshot")
@_common_options
def snapshot(cluster_name, region, bucket, run_id, groups, debug):
    """Capture identity + Slurm state from the SOURCE cluster (read-only).

    Writes users/groups/ssh_inventory/identity_model/shape and the Slurm config
    + accounting-configuration dump to s3://<bucket>/<run-id>/. Nothing on the
    source is modified.
    """
    _require_tooling()
    run_id = run_id or _default_run_id()
    inv = _ansible_root() / "inventory.snapshot.ini"
    count = _build_inventory(cluster_name, region, groups, bucket, inv)
    logger.info("Resolved %d controller node(s) for '%s'.", count, cluster_name)
    _run_playbook(
        "snapshot.yml",
        inv,
        {"hpm_bucket": bucket, "hpm_run_id": run_id},
        debug,
    )
    click.echo(f"\nSnapshot complete. Artifacts: {bucket.rstrip('/')}/{run_id}/")
    click.echo(f"Use --run-id {run_id} for the converge/validate steps.")


@migrate.command("converge")
@_common_options
def converge(cluster_name, region, bucket, run_id, groups, debug):
    """Reproduce the snapshot on the TARGET cluster (pins UID/GID, ssh, Slurm).

    Reads the manifest from s3://<bucket>/<run-id>/ and recreates groups/users
    with their exact numeric IDs, enforces ~/.ssh permissions, and applies the
    Slurm configuration. Idempotent.
    """
    if not run_id:
        raise click.ClickException("--run-id is required for converge (use the id from snapshot).")
    _require_tooling()
    inv = _ansible_root() / "inventory.converge.ini"
    count = _build_inventory(cluster_name, region, groups, bucket, inv)
    logger.info("Resolved %d controller node(s) for '%s'.", count, cluster_name)
    _run_playbook(
        "converge.yml",
        inv,
        {"hpm_bucket": bucket, "hpm_run_id": run_id},
        debug,
    )
    click.echo("\nConverge complete. Run `hyp migrate validate` before cutover.")


@migrate.command("validate")
@_common_options
def validate(cluster_name, region, bucket, run_id, groups, debug):
    """Fail-closed gate: assert TARGET identity + ~/.ssh perms match the source.

    Any mismatch fails the command and should block cutover.
    """
    if not run_id:
        raise click.ClickException("--run-id is required for validate (use the id from snapshot).")
    _require_tooling()
    inv = _ansible_root() / "inventory.validate.ini"
    _build_inventory(cluster_name, region, groups, bucket, inv)
    _run_playbook(
        "validate.yml",
        inv,
        {"hpm_bucket": bucket, "hpm_run_id": run_id},
        debug,
    )
    click.echo("\nValidation passed — identity matches source. Safe to proceed to cutover.")


@migrate.command("plan")
@click.option("--plan-arn", required=True, help="Target training-plan ARN.")
@click.option("--region", required=True, help="Region of the training plan.")
def plan(plan_arn, region):
    """Inspect a target training plan (instance type, reserved AZ, capacity).

    Training-plan capacity is AZ-pinned: the target cluster subnet MUST be in the
    plan's reserved AZ. Use the reported AZ when provisioning target networking.
    """
    info = _describe_training_plan(plan_arn, region)
    click.echo(json.dumps(info, indent=2))
    click.echo(
        f"\nPlace the target cluster subnet in AZ '{info['availability_zone']}' "
        f"({info['availability_zone_id']}). Worker instance: {info['instance_type']}, "
        f"{info['available_instances']} available."
    )


@migrate.command("provision")
@click.option("--bucket", required=True,
              help="Target LCS/artifact bucket (sagemaker-*).")
@click.option("--execution-role-arn", required=True,
              help="SageMaker cluster execution role ARN (needs EC2/VPC+ENI and "
                   "artifact-bucket read/write).")
@click.option("--plan-arn", default=None,
              help="Training-plan ARN to bind to the worker group (optional; "
                   "omit for on-demand-only clusters).")
@click.option("--region", required=True, help="Target region.")
@click.option("--worker-instance", default="ml.p5.48xlarge", show_default=True)
@click.option("--worker-count", type=int, default=1, show_default=True)
@click.option("--ondemand-instance", default="ml.m5.xlarge", show_default=True,
              help="Instance type for controller/login (on-demand).")
@click.option("--out", default="cluster-config.json", show_default=True,
              help="Where to write the generated instance-group config.")
def provision(bucket, execution_role_arn, plan_arn, region, worker_instance,
              worker_count, ondemand_instance, out):
    """Generate the target cluster instance-group config (training-plan aware).

    Emits a CreateCluster --instance-groups document in which the worker group
    binds the training plan (TrainingPlanArn) and controller/login run
    on-demand. When --plan-arn is given, the command also prints the plan's
    reserved AZ so the cluster subnet can be placed correctly.
    """
    if plan_arn:
        info = _describe_training_plan(plan_arn, region)
        if info["instance_type"] and info["instance_type"] != worker_instance:
            logger.warning(
                "Plan reserves %s but --worker-instance is %s; using the plan's type.",
                info["instance_type"], worker_instance,
            )
            worker_instance = info["instance_type"]
        click.echo(
            f"Training plan capacity: {worker_instance} in AZ "
            f"{info['availability_zone']} ({info['availability_zone_id']}). "
            f"Ensure the target subnet is in this AZ."
        )

    config = _build_cluster_config(
        bucket, execution_role_arn, plan_arn,
        worker_instance, worker_count, ondemand_instance,
    )
    Path(out).write_text(json.dumps(config, indent=2))
    click.echo(f"\nWrote instance-group config to {out}.")
    click.echo(
        "Create the cluster with:\n"
        f"  aws sagemaker create-cluster --cluster-name <NAME> "
        f"--instance-groups file://{out} --vpc-config file://<vpc-config.json> "
        f"--region {region}"
    )
