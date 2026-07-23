#!/usr/bin/env python3
"""
gen_inventory.py — build an Ansible inventory for a HyperPod cluster reachable
only over SSM Session Manager.

HyperPod nodes are not SSM-managed instances, so we cannot use a normal dynamic
inventory keyed on instance IDs. Instead each node is reachable via the special
Session target:  sagemaker-cluster:<CLUSTER_ID>_<GROUP>-<INSTANCE_ID>

We emit an INI inventory where each host uses the community.aws.aws_ssm
connection plugin with that target as ansible_host.

Usage:
  gen_inventory.py --cluster NAME --region REGION [--group G1,G2] \
      [--bucket s3://...] > inventory.generated.ini
"""
import argparse
import json
import subprocess
import sys


def aws(region, *args):
    out = subprocess.check_output(
        ["aws", "--region", region, "--output", "json", *args]
    )
    return json.loads(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--region", required=True)
    ap.add_argument("--group", default="", help="comma-separated instance groups")
    ap.add_argument("--bucket", default="", help="s3 bucket for aws_ssm transport")
    args = ap.parse_args()

    desc = aws(args.region, "sagemaker", "describe-cluster",
               "--cluster-name", args.cluster)
    cluster_arn = desc["ClusterArn"]
    cluster_id = cluster_arn.rsplit("/", 1)[-1]

    nodes = aws(args.region, "sagemaker", "list-cluster-nodes",
                "--cluster-name", args.cluster).get("ClusterNodeSummaries", [])

    wanted = {g.strip() for g in args.group.split(",") if g.strip()}

    lines = []
    lines.append("[controller]")
    controllers = []
    workers = []
    for n in nodes:
        if n.get("InstanceStatus", {}).get("Status") != "Running":
            continue
        group = n["InstanceGroupName"]
        if wanted and group not in wanted:
            continue
        iid = n["InstanceId"]
        target = f"sagemaker-cluster:{cluster_id}_{group}-{iid}"
        host = f"{group}-{iid}"
        entry = (
            f"{host} ansible_host={target} "
            f"ansible_connection=community.aws.aws_ssm "
            f"ansible_aws_ssm_region={args.region} "
            f"ansible_aws_ssm_instance_id={target}"
        )
        if args.bucket:
            b = args.bucket.replace("s3://", "")
            entry += f" ansible_aws_ssm_bucket_name={b}"
        # Heuristic: controller/head/login groups host identity + slurm state.
        low = group.lower()
        if any(k in low for k in ("controller", "head", "login")):
            controllers.append(entry)
        else:
            workers.append(entry)

    if not controllers and not workers:
        sys.stderr.write("ERROR: no running nodes matched.\n")
        sys.exit(1)

    # If nothing matched the controller heuristic, treat all matched as controller
    # (caller likely passed --group controller-machine explicitly).
    if not controllers:
        controllers = workers
        workers = []

    out = ["[controller]", *controllers, "", "[workers]", *workers, "",
           "[all:vars]",
           "ansible_python_interpreter=/usr/bin/python3"]
    print("\n".join(out))


if __name__ == "__main__":
    main()
