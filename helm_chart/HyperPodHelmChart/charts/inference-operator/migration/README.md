# Helm to EKS Addon Migration Script

This script migrates the HyperPod Inference Operator from Helm-based installation to EKS Addon installation.

## Overview

The script takes a cluster name and region as parameters, retrieves the existing Helm installation configuration, and migrates to EKS Addon deployment. It creates new IAM roles for the Inference Operator, ALB Controller, and KEDA Operator. 

Before migrating the Inference Operator, the script ensures required dependencies (S3 CSI driver, FSx CSI driver, cert-manager, and metrics-server) exist. If they don't exist, it deploys them as addons.

After the Inference Operator addon migration completes, the script also migrates S3, FSx, and other dependencies (ALB, KEDA, cert-manager, metrics-server) if they were originally installed via the Inference Operator Helm chart. Use `--skip-dependencies-migration` to skip this step.

## Prerequisites

- AWS CLI configured with appropriate credentials
- kubectl configured with access to your EKS cluster
- Helm installed
- Existing Helm installation of hyperpod-inference-operator

## Usage

```bash
./helm_to_addon.sh [OPTIONS]
```

## Options

- `--auto-approve` - Skip confirmation prompts
- `--step-by-step` - Pause after each major step for review
- `--skip-dependencies-migration` - Skip migration of Helm-installed dependencies to addons
- `--cluster-name NAME` - EKS cluster name (required)
- `--region REGION` - AWS region (required)
- `--helm-namespace NAMESPACE` - Namespace where Helm chart is installed (default: kube-system)
- `--s3-mountpoint-role-arn ARN` - S3 Mountpoint CSI driver IAM role ARN
- `--fsx-role-arn ARN` - FSx CSI driver IAM role ARN

## Example

**Basic migration (migrates dependencies):**
```bash
./helm_to_addon.sh \
  --cluster-name my-cluster \
  --region us-east-1
```

**Auto-approve without prompts:**
```bash
./helm_to_addon.sh \
  --cluster-name my-cluster \
  --region us-east-1 \
  --auto-approve
```

**Skip dependency migration:**
```bash
./helm_to_addon.sh \
  --cluster-name my-cluster \
  --region us-east-1 \
  --skip-dependencies-migration
```

**Provide existing S3 and FSx IAM roles:**
```bash
./helm_to_addon.sh \
  --cluster-name my-cluster \
  --region us-east-1 \
  --s3-mountpoint-role-arn arn:aws:iam::123456789012:role/s3-csi-role \
  --fsx-role-arn arn:aws:iam::123456789012:role/fsx-csi-role
```

## Backup Location

Backups are stored in `/tmp/hyperpod-migration-backup-<timestamp>/`

## Rollback

If migration fails, the script prompts for user confirmation before initiating rollback to restore the previous state.
