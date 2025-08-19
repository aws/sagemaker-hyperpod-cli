(cli_training)=


# Training

Complete reference for SageMaker HyperPod PyTorch training job parameters and configuration options.

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

### Required Parameters

- `--job-name TEXT`: Unique name for the training job (1-63 characters, alphanumeric with hyphens)
- `--image TEXT`: Docker image URI containing your training code

### Optional Parameters

- `--namespace TEXT`: Kubernetes namespace
- `--command ARRAY`: Command to run in the container (array of strings)
- `--args ARRAY`: Arguments for the entry script (array of strings)
- `--environment OBJECT`: Environment variables as key-value pairs
- `--pull-policy TEXT`: Image pull policy (Always, Never, IfNotPresent)
- `--instance-type TEXT`: Instance type for training
- `--node-count INTEGER`: Number of nodes (minimum: 1)
- `--tasks-per-node INTEGER`: Number of tasks per node (minimum: 1)
- `--label-selector OBJECT`: Node label selector as key-value pairs
- `--deep-health-check-passed-nodes-only BOOLEAN`: Schedule pods only on nodes that passed deep health check (default: false)
- `--scheduler-type TEXT`: If specified, training job pod will be dispatched by specified scheduler. If not specified, the pod will be dispatched by default scheduler.
- `--queue-name TEXT`: Queue name for job scheduling (1-63 characters, alphanumeric with hyphens)
- `--priority TEXT`: Priority class for job scheduling
- `--max-retry INTEGER`: Maximum number of job retries (minimum: 0)
- `--volume ARRAY`: List of volume configurations (Refer [Volume Configuration](#volume-configuration) for detailed parameter info)
- `--service-account-name TEXT`: Service account name

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

#### Optional Parameters

- `--namespace, -n TEXT`: Namespace to list jobs from (default: "default")

### hyp describe hyp-pytorch-job

Describe a specific HyperPod PyTorch job.

#### Syntax

```bash
hyp describe hyp-pytorch-job [OPTIONS]
```

#### Required Parameters

- `--job-name TEXT`: Name of the job to describe

#### Optional Parameters

- `--namespace, -n TEXT`: Namespace of the job (default: "default")

### hyp delete hyp-pytorch-job

Delete a HyperPod PyTorch job.

#### Syntax

```bash
hyp delete hyp-pytorch-job [OPTIONS]
```

#### Required Parameters

- `--job-name TEXT`: Name of the job to delete

#### Optional Parameters

- `--namespace, -n TEXT`: Namespace of the job (default: "default")

### hyp list-pods hyp-pytorch-job

List all pods associated with a PyTorch job.

#### Syntax

```bash
hyp list-pods hyp-pytorch-job [OPTIONS]
```

#### Required Parameters

- `--job-name TEXT`: Name of the job to list pods for

#### Optional Parameters

- `--namespace, -n TEXT`: Namespace of the job (default: "default")

### hyp get-logs hyp-pytorch-job

Get logs from a specific pod in a PyTorch job.

#### Syntax

```bash
hyp get-logs hyp-pytorch-job [OPTIONS]
```

#### Required Parameters

- `--job-name TEXT`: Name of the job
- `--pod-name TEXT`: Name of the pod to get logs from

#### Optional Parameters

- `--namespace, -n TEXT`: Namespace of the job (default: "default")
