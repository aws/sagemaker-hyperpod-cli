(getting_started)=

# Getting Started

This guide will help you get started with the SageMaker HyperPod CLI and SDK to perform basic operations.

## Cluster Management

### List Available Clusters

List all available SageMaker HyperPod clusters in your account:

**CLI**
```bash
hyp list-cluster [--region <region>] [--namespace <namespace>] [--output <json|table>]
```

**SDK**
```python
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager

clusters = HyperPodManager.list_clusters(region='us-east-2')
print(clusters)
```

**Parameters:**
- `region` (string) - Optional. The AWS region where the SageMaker HyperPod and EKS clusters are located. If not specified, uses the region from your current AWS account credentials.
- `namespace` (string) - Optional. The namespace to check quota with. Only SageMaker managed namespaces are supported.
- `output` (enum) - Optional. The output format: `table` or `json` (default).

### Connect to a Cluster

Configure your local kubectl environment to interact with a specific SageMaker HyperPod cluster and namespace:

**CLI**
```bash
hyp set-cluster-context --cluster-name <cluster-name> [--namespace <namespace>]
```

**SDK**
```python
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager

HyperPodManager.set_context('<hyperpod-cluster-name>', region='us-east-2')
```

**Parameters:**
- `cluster-name` (string) - Required. The SageMaker HyperPod cluster name to configure with.
- `namespace` (string) - Optional. The namespace to connect to. If not specified, the CLI will automatically discover accessible namespaces.

### Get Current Cluster Context

View information about the currently configured cluster context:

**CLI**
```bash
hyp get-cluster-context
```

**SDK**
```python
from sagemaker.hyperpod.hyperpod_manager import HyperPodManager

# Get current context information
context = HyperPodManager.get_context()
print(context)
```

## Job Management

### List Pods for a Training Job

View all pods associated with a specific training job:

**CLI**
```bash
hyp list-pods hyp-pytorch-job --job-name <job-name>
```

**SDK**
```python
# List all pods created for this job
pytorch_job.list_pods()
```

**Parameters:**
- `job-name` (string) - Required. The name of the job to list pods for.

### Access Pod Logs

View logs for a specific pod within a training job:

**CLI**
```bash
hyp get-logs hyp-pytorch-job --pod-name <pod-name> --job-name <job-name>
```

**SDK**
```python
# Check the logs from pod0
pytorch_job.get_logs_from_pod("demo-pod-0")
```

**Parameters:**
- `job-name` (string) - Required. The name of the job to get logs for.
- `pod-name` (string) - Required. The name of the pod to get logs from.

## Next Steps

After setting up your environment and connecting to a cluster, you can:

- Create and manage PyTorch training jobs
- Deploy and manage inference endpoints
- Monitor cluster resources and job performance

For more detailed information on specific commands, use the `--help` flag:

```bash
hyp <command> --help
```