(cli_training)=


# Training

Complete reference for SageMaker HyperPod PyTorch training job parameters and configuration options.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

* [Create PyTorch Job](#hyp-create-hyp-pytorch-job)
* [List Jobs](#hyp-list-hyp-pytorch-job)
* [Describe Job](#hyp-describe-hyp-pytorch-job)
* [Delete Job](#hyp-delete-hyp-pytorch-job)
* [List Pods](#hyp-list-pods-hyp-pytorch-job)
* [Get Logs](#hyp-get-logs-hyp-pytorch-job)


## hyp create hyp-pytorch-job

Create distributed PyTorch training jobs on SageMaker HyperPod clusters.

### Syntax

```bash
hyp create hyp-pytorch-job [OPTIONS]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--job-name` | TEXT | Yes | Unique name for the training job (1-63 characters, alphanumeric with hyphens) |
| `--image` | TEXT | Yes | Docker image URI containing your training code |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--command` | ARRAY | No | Command to run in the container (array of strings) |
| `--args` | ARRAY | No | Arguments for the entry script (array of strings) |
| `--environment` | OBJECT | No | Environment variables as key-value pairs |
| `--pull-policy` | TEXT | No | Image pull policy (Always, Never, IfNotPresent) |
| `--instance-type` | TEXT | No | Instance type for training |
| `--node-count` | INTEGER | No | Number of nodes (minimum: 1) |
| `--tasks-per-node` | INTEGER | No | Number of tasks per node (minimum: 1) |
| `--label-selector` | OBJECT | No | Node label selector as key-value pairs |
| `--deep-health-check-passed-nodes-only` | BOOLEAN | No | Schedule pods only on nodes that passed deep health check (default: false) |
| `--scheduler-type` | TEXT | No | Scheduler type |
| `--queue-name` | TEXT | No | Queue name for job scheduling (1-63 characters, alphanumeric with hyphens) |
| `--priority` | TEXT | No | Priority class for job scheduling |
| `--max-retry` | INTEGER | No | Maximum number of job retries (minimum: 0) |
| `--volume` | ARRAY | No | List of volume configurations (Refer [Volume Configuration](#volume-configuration) for detailed parameter info) |
| `--service-account-name` | TEXT | No | Service account name |
| `--accelerators` | INTEGER | No | Number of accelerators a.k.a GPUs or Trainium Chips |
| `--vcpu` | FLOAT | No | Number of vCPUs |
| `--memory` | FLOAT | No | Amount of memory in GiB |
| `--accelerators-limit` | INTEGER | No | Limit for the number of accelerators a.k.a GPUs or Trainium Chips |
| `--vcpu-limit` | FLOAT | No | Limit for the number of vCPUs |
| `--memory-limit` | FLOAT | No | Limit for the amount of memory in GiB |
| `--preferred-topology` | TEXT | No | Preferred topology annotation for scheduling |
| `--required-topology` | TEXT | No | Required topology annotation for scheduling |
| `--debug` | FLAG | No | Enable debug mode (default: false) |

### Volume Configuration

The `--volume` parameter supports mounting different types of storage to your training containers.

### Volume Syntax

```bash
--volume name=<volume_name>,type=<volume_type>,mount_path=<mount_path>[,additional_options]
```

### Volume Types

**hostPath Volume**
```bash
--volume name=model-data,type=hostPath,mount_path=/data,path=/host/data
```

**Persistent Volume Claim (PVC)**
```bash
--volume name=training-output,type=pvc,mount_path=/output,claim_name=training-pvc,read_only=false
```

### Volume Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | TEXT | Yes | Volume name |
| `type` | TEXT | Yes | Volume type (`hostPath` or `pvc`) |
| `mount_path` | TEXT | Yes | Mount path in container |
| `path` | TEXT | For hostPath | Host path for hostPath volumes |
| `claim_name` | TEXT | For pvc | PVC claim name for pvc volumes |
| `read_only` | BOOLEAN | No | Read-only flag for pvc volumes |

## Training Job Management Commands

Commands for managing PyTorch training jobs.

### hyp list hyp-pytorch-job

List all HyperPod PyTorch jobs in a namespace.

#### Syntax

```bash
hyp list hyp-pytorch-job [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace, -n` | TEXT | No | Namespace to list jobs from (default: "default") |

### hyp describe hyp-pytorch-job

Describe a specific HyperPod PyTorch job.

#### Syntax

```bash
hyp describe hyp-pytorch-job [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--job-name` | TEXT | Yes | Name of the job to describe |
| `--namespace, -n` | TEXT | No | Namespace of the job (default: "default") |

### hyp delete hyp-pytorch-job

Delete a HyperPod PyTorch job.

#### Syntax

```bash
hyp delete hyp-pytorch-job [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--job-name` | TEXT | Yes | Name of the job to delete |
| `--namespace, -n` | TEXT | No | Namespace of the job (default: "default") |

### hyp list-pods hyp-pytorch-job

List all pods associated with a PyTorch job.

#### Syntax

```bash
hyp list-pods hyp-pytorch-job [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--job-name` | TEXT | Yes | Name of the job to list pods for |
| `--namespace, -n` | TEXT | No | Namespace of the job (default: "default") |

### hyp get-logs hyp-pytorch-job

Get logs from a specific pod in a PyTorch job.

#### Syntax

```bash
hyp get-logs hyp-pytorch-job [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--job-name` | TEXT | Yes | Name of the job |
| `--pod-name` | TEXT | Yes | Name of the pod to get logs from |
| `--namespace, -n` | TEXT | No | Namespace of the job (default: "default") |
