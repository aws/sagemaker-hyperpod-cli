
# SageMaker HyperPod command-line interface

The Amazon SageMaker HyperPod command-line interface (HyperPod CLI) is a tool that helps manage clusters, training jobs, and inference endpoints on the SageMaker HyperPod clusters orchestrated by Amazon EKS.

This documentation serves as a reference for the available HyperPod CLI commands. For a comprehensive user guide, see [Orchestrating SageMaker HyperPod clusters with Amazon EKS](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html) in the *Amazon SageMaker Developer Guide*.

Note: Old `hyperpod`CLI V2 has been moved to `release_v2` branch. Please refer [release_v2 branch](https://github.com/aws/sagemaker-hyperpod-cli/tree/release_v2) for usage.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Platform Support](#platform-support)
- [ML Framework Support](#ml-framework-support)
- [Installation](#installation)
- [Usage](#usage)
    - [Getting Started](#getting-started)
    - [CLI](#cli)
        - [Cluster Management](#cluster-management)
        - [Training](#training)
        - [Inference](#inference)
            - [Jumpstart Endpoint](#jumpstart-endpoint-creation)
            - [Custom Endpoint](#custom-endpoint-creation)
        - [Space](#space)
    - [SDK](#sdk)
        - [Cluster Management](#cluster-management-sdk)
        - [Training](#training-sdk)
        - [Inference](#inference-sdk)
        - [Space](#space-sdk)
- [Examples](#examples)
  

## Overview

The SageMaker HyperPod CLI is a tool that helps create training jobs and inference endpoint deployments to the Amazon SageMaker HyperPod clusters orchestrated by Amazon EKS. It provides a set of commands for managing the full lifecycle of jobs, including create, describe, list, and delete operations, as well as accessing pod and operator logs where applicable. The CLI is designed to abstract away the complexity of working directly with Kubernetes for these core actions of managing jobs on SageMaker HyperPod clusters orchestrated by Amazon EKS.

## Prerequisites

### Region Configuration

**Important**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.

### Prerequisites for Training

- HyperPod CLI currently supports starting PyTorchJobs. To start a job, you need to install Training Operator first. 
  - You can follow [pytorch operator doc](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html) to install it.

### Prerequisites for Inference 

- HyperPod CLI supports creating Inference Endpoints through jumpstart and through custom Endpoint config 
  - You can follow [inference operator doc](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-model-deployment-setup.html) to install it.

## Platform Support

SageMaker HyperPod CLI currently supports Linux and MacOS platforms. Windows platform is not supported now.

## ML Framework Support

SageMaker HyperPod CLI currently supports start training job with:
- PyTorch ML Framework. Version requirements: PyTorch >= 1.10

## Installation

1. Make sure that your local python version is 3.8, 3.9, 3.10 or 3.11.

2. Install the sagemaker-hyperpod-cli package.

    ```bash
    pip install sagemaker-hyperpod
    ```

3. Verify if the installation succeeded by running the following command.

    ```bash
    hyp --help
    ```

## Usage

The HyperPod CLI provides the following commands:

- [Getting Started](#getting-started)
- [CLI](#cli)
  - [Cluster Management](#cluster-management)
  - [Training](#training)
  - [Inference](#inference)
    - [Jumpstart Endpoint](#jumpstart-endpoint-creation)
    - [Custom Endpoint](#custom-endpoint-creation)
- [SDK](#sdk)
  - [Cluster Management](#cluster-management-sdk)
  - [Training](#training-sdk)
  - [Inference](#inference-sdk)


### Getting Started

#### Getting Cluster information

This command lists the available SageMaker HyperPod clusters and their capacity information.

```bash
hyp list-cluster
```

| Option | Type | Description |
|--------|------|-------------|
| `--region <region>` | Optional | The region that the SageMaker HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials. |
| `--namespace <namespace>` | Optional | The namespace that users want to check the quota with. Only the SageMaker managed namespaces are supported. |
| `--output <json\|table>` | Optional | The output format. Available values are `table` and `json`. The default value is `json`. |
| `--debug` | Optional | Enable debug mode for detailed logging. |

#### Connecting to a Cluster

This command configures the local Kubectl environment to interact with the specified SageMaker HyperPod cluster and namespace.

```bash
hyp set-cluster-context --cluster-name <cluster-name>
```

| Option | Type | Description |
|--------|------|-------------|
| `--cluster-name <cluster-name>` | Required | The SageMaker HyperPod cluster name to configure with. |
| `--namespace <namespace>` | Optional | The namespace that you want to connect to. If not specified, Hyperpod cli commands will auto discover the accessible namespace. |
| `--region <region>` | Optional | The AWS region where the HyperPod cluster resides. |
| `--debug` | Optional | Enable debug mode for detailed logging. |

#### Getting Cluster Context

Get all the context related to the current set Cluster

```bash
hyp get-cluster-context
```

| Option | Type | Description |
|--------|------|-------------|
| `--debug` | Optional | Enable debug mode for detailed logging. |


## CLI

### Cluster Management 

**Important**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.

**Cluster stack names must be unique within each AWS region.** If you attempt to create a cluster stack with a name that already exists in the same region, the deployment will fail.

#### Initialize Cluster Configuration

Initialize a new cluster configuration in the current directory:

```bash
hyp init cluster-stack
```

**Important**: The `resource_name_prefix` parameter in the generated `config.yaml` file serves as the primary identifier for all AWS resources created during deployment. Each deployment must use a unique resource name prefix to avoid conflicts. This prefix is automatically appended with a unique identifier during cluster creation to ensure resource uniqueness.

#### Configure Cluster Parameters

Configure cluster parameters interactively or via command line:

```bash
hyp configure --resource-name-prefix my-cluster --stage prod
```

#### Validate Configuration

Validate the configuration file syntax:

```bash
hyp validate
```

#### Create Cluster Stack

Create the cluster stack using the configured parameters:

```bash
hyp create --region <region>
```

**Note**: The region flag is optional. If not provided, the command will use the default region from your AWS credentials configuration.

#### List Cluster Stacks

```bash
hyp list cluster-stack
```

| Option | Type | Description |
|--------|------|-------------|
| `--region <region>` | Optional | The AWS region to list stacks from. |
| `--status "['CREATE_COMPLETE', 'UPDATE_COMPLETE']"` | Optional | Filter by stack status. |
| `--debug` | Optional | Enable debug mode for detailed logging. |

#### Describe Cluster Stack

```bash
hyp describe cluster-stack <stack-name>
```

| Option | Type | Description |
|--------|------|-------------|
| `--region <region>` | Optional | The AWS region where the stack exists. |
| `--debug` | Optional | Enable debug mode for detailed logging. |

#### Delete Cluster Stack

Delete a HyperPod cluster stack. Removes the specified CloudFormation stack and all associated AWS resources. This operation cannot be undone.

```bash
 hyp delete cluster-stack <stack-name>
```

| Option | Type | Description |
|--------|------|-------------|
| `--region <region>` | Required | The AWS region where the stack exists. |
| `--retain-resources  S3Bucket-TrainingData,EFSFileSystem-Models` | Optional | Comma-separated list of logical resource IDs to retain during deletion (only works on DELETE_FAILED stacks). Resource names are shown in failed deletion output, or use AWS CLI: `aws cloudformation list-stack-resources STACK_NAME --region REGION`. |
| `--debug` | Optional | Enable debug mode for detailed logging. |


#### Update Existing Cluster

```bash
hyp update cluster --cluster-name my-cluster \
    --instance-groups '[{"InstanceCount":2,"InstanceGroupName":"worker-nodes","InstanceType":"ml.m5.large"}]' \
    --node-recovery Automatic
```

#### Reset Configuration

Reset configuration to default values:

```bash
hyp reset
```

### Training 

#### **Option 1**: Create Pytorch job through init experience

#### Initialize Pytorch Job Configuration

Initialize a new pytorch job configuration in the current directory:

```bash
hyp init hyp-pytorch-job
```

#### Configure Pytorch Job Parameters

Configure pytorch job parameters interactively or via command line:

```bash
hyp configure --job-name my-pytorch-job
```

#### Validate Configuration

Validate the configuration file syntax:

```bash
hyp validate
```

#### Create Pytorch Job

Create the pytorch job using the configured parameters:

```bash
hyp create
```


#### **Option 2**: Create Pytorch job through create command

```bash
hyp create hyp-pytorch-job \
    --version 1.0 \
    --job-name test-pytorch-job \
    --image pytorch/pytorch:latest \
    --command '[python, train.py]' \
    --args '[--epochs=10, --batch-size=32]' \
    --environment '{"PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:32"}' \
    --pull-policy "IfNotPresent" \
    --instance-type ml.p4d.24xlarge \
    --tasks-per-node 8 \
    --label-selector '{"accelerator": "nvidia", "network": "efa"}' \
    --deep-health-check-passed-nodes-only true \
    --scheduler-type "kueue" \
    --queue-name "training-queue" \
    --priority "high" \
    --max-retry 3 \
    --accelerators 8 \
    --vcpu 96.0 \
    --memory 1152.0 \
    --accelerators-limit 8 \
    --vcpu-limit 96.0 \
    --memory-limit 1152.0 \
    --preferred-topology "topology.kubernetes.io/zone=us-west-2a" \
    --volume name=model-data,type=hostPath,mount_path=/data,path=/data \
    --volume name=training-output,type=pvc,mount_path=/data2,claim_name=my-pvc,read_only=false
```

**Example with accelerator parititons:**

```bash
hyp create hyp-pytorch-job \
    --version 1.1 \
    --job-name test-pytorch-job \
    --image pytorch/pytorch:latest \
    --command '[python, train.py]' \
    --args '[--epochs=10, --batch-size=32]' \
    --environment '{"PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:32"}' \
    --pull-policy "IfNotPresent" \
    --instance-type ml.p4d.24xlarge \
    --tasks-per-node 8 \
    --label-selector '{"accelerator": "nvidia", "network": "efa"}' \
    --deep-health-check-passed-nodes-only true \
    --scheduler-type "kueue" \
    --queue-name "training-queue" \
    --priority "high" \
    --max-retry 3 \
    --accelerator-partition-type "mig-1g.5gb" \
    --accelerator-partition-count 2 \
    --accelerator-partition-limit 4 \
    --vcpu 96.0 \
    --memory 1152.0 \
    --vcpu-limit 96.0 \
    --memory-limit 1152.0 \
    --preferred-topology "topology.kubernetes.io/zone=us-west-2a" \
    --volume name=model-data,type=hostPath,mount_path=/data,path=/data \
    --volume name=training-output,type=pvc,mount_path=/data2,claim_name=my-pvc,read_only=false
```

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
| `--accelerator-partition-type` | TEXT | No | Type of accelerator partition (e.g., mig-1g.5gb, mig-2g.10gb, mig-3g.20gb, mig-4g.20gb, mig-7g.40gb) |
| `--accelerator-partition-count` | INTEGER | No | Number of accelerator partitions to request (minimum: 1) |
| `--accelerator-partition-limit` | INTEGER | No | Limit for the number of accelerator partitions (minimum: 1) |
| `--preferred-topology` | TEXT | No | Preferred topology annotation for scheduling |
| `--required-topology` | TEXT | No | Required topology annotation for scheduling |
| `--debug` | FLAG | No | Enable debug mode (default: false) |

#### List Available Accelerator Partition Types

This command lists the available accelerator partition types on the cluster for a specific instance type.

```bash
hyp list-accelerator-partition-type --instance-type <instance-type>
```

#### List Training Jobs

```bash
hyp list hyp-pytorch-job
```

#### Describe a Training Job

```bash
hyp describe hyp-pytorch-job --job-name <job-name>
````

#### Listing Pods

This command lists all the pods associated with a specific training job.

```bash
hyp list-pods hyp-pytorch-job --job-name <job-name>
```

* `job-name` (string) - Required. The name of the job to list pods for.

#### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```bash
hyp get-logs hyp-pytorch-job --pod-name <pod-name> --job-name <job-name>
```

| Parameter | Required | Description |
|--------|------|-------------|
| `--job-name` | Yes | The name of the job to get the log for. |
| `--pod-name` | Yes | The name of the pod to get the log from. |
| `--namespace` | No | The namespace of the job. Defaults to 'default'. |
| `--container` | No | The container name to get logs from. |

#### Get Operator Logs

```bash
hyp get-operator-logs hyp-pytorch-job --since-hours 0.5
```

#### Delete a Training Job

```bash
hyp delete hyp-pytorch-job --job-name <job-name>
```

### Inference 

### Jumpstart Endpoint Creation

#### **Option 1**: Create jumpstart endpoint through init experience

#### Initialize Jumpstart Endpoint Configuration

Initialize a new jumpstart endpoint configuration in the current directory:

```bash
hyp init hyp-jumpstart-endpoint
```

#### Configure Jumpstart Endpoint Parameters

Configure jumpstart endpoint parameters interactively or via command line:

```bash
hyp configure --endpoint-name my-jumpstart-endpoint
```

#### Validate Configuration

Validate the configuration file syntax:

```bash
hyp validate
```

#### Create Jumpstart Endpoint

Create the jumpstart endpoint using the configured parameters:

```bash
hyp create
```


#### **Option 2**: Create jumpstart endpoint through create command
Pre-trained Jumpstart models can be gotten from https://sagemaker.readthedocs.io/en/v2.82.0/doc_utils/jumpstart.html and fed into the call for creating the endpoint

```bash
hyp create hyp-jumpstart-endpoint \
    --version 1.0 \
    --model-id jumpstart-model-id\
    --instance-type ml.g5.8xlarge \
    --endpoint-name endpoint-jumpstart
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--model-id` | TEXT | Yes | JumpStart model identifier (1-63 characters, alphanumeric with hyphens) |
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--metadata-name` | TEXT | No | Name of the jumpstart endpoint object |
| `--accept-eula` | BOOLEAN | No | Whether model terms of use have been accepted (default: false) |
| `--model-version` | TEXT | No | Semantic version of the model (e.g., "1.0.0", 5-14 characters) |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI to write the TLS certificate (optional) |
| `--debug` | FLAG | No | Enable debug mode (default: false) |


#### Invoke a JumpstartModel Endpoint

```bash
hyp invoke hyp-jumpstart-endpoint \
    --endpoint-name endpoint-jumpstart \
    --body '{"inputs":"What is the capital of USA?"}'
```


#### Managing an Endpoint 

```bash
hyp list hyp-jumpstart-endpoint
hyp describe hyp-jumpstart-endpoint --name endpoint-jumpstart
```

#### List Pods

```bash
hyp list-pods hyp-jumpstart-endpoint
```

#### Get Logs

```bash
hyp get-logs hyp-jumpstart-endpoint --pod-name <pod-name>
```

#### Get Operator Logs

```bash
hyp get-operator-logs hyp-jumpstart-endpoint --since-hours 0.5
```

#### Deleting an Endpoint

```bash
hyp delete hyp-jumpstart-endpoint --name endpoint-jumpstart
```


### Custom Endpoint Creation
#### **Option 1**: Create custom endpoint through init experience

#### Initialize Custom Endpoint Configuration

Initialize a new custom endpoint configuration in the current directory:

```bash
hyp init hyp-custom-endpoint
```

#### Configure Custom Endpoint Parameters

Configure custom endpoint parameters interactively or via command line:

```bash
hyp configure --endpoint-name my-custom-endpoint
```

#### Validate Configuration

Validate the configuration file syntax:

```bash
hyp validate
```

#### Create Custom Endpoint

Create the custom endpoint using the configured parameters:

```bash
hyp create
```


#### **Option 2**: Create custom endpoint through create command
```bash
hyp create hyp-custom-endpoint \
    --version 1.0 \
    --endpoint-name endpoint-custom \
    --model-name my-pytorch-model \
    --model-source-type s3 \
    --model-location my-pytorch-training \
    --model-volume-mount-name test-volume \
    --s3-bucket-name your-bucket \
    --s3-region us-east-1 \
    --instance-type ml.g5.8xlarge \
    --image-uri 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-inference:latest \
    --container-port 8080
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--model-name` | TEXT | Yes | Name of model to create on SageMaker (1-63 characters, alphanumeric with hyphens) |
| `--model-source-type` | TEXT | Yes | Model source type ("s3" or "fsx") |
| `--image-uri` | TEXT | Yes | Docker image URI for inference |
| `--container-port` | INTEGER | Yes | Port on which model server listens (1-65535) |
| `--model-volume-mount-name` | TEXT | Yes | Name of the model volume mount |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--metadata-name` | TEXT | No | Name of the custom endpoint object |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--env` | OBJECT | No | Environment variables as key-value pairs |
| `--metrics-enabled` | BOOLEAN | No | Enable metrics collection (default: false) |
| `--model-version` | TEXT | No | Version of the model (semantic version format) |
| `--model-location` | TEXT | No | Specific model data location |
| `--prefetch-enabled` | BOOLEAN | No | Whether to pre-fetch model data (default: false) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI for TLS certificate output |
| `--fsx-dns-name` | TEXT | No | FSx File System DNS Name |
| `--fsx-file-system-id` | TEXT | No | FSx File System ID |
| `--fsx-mount-name` | TEXT | No | FSx File System Mount Name |
| `--s3-bucket-name` | TEXT | No | S3 bucket location |
| `--s3-region` | TEXT | No | S3 bucket region |
| `--model-volume-mount-path` | TEXT | No | Path inside container for model volume (default: "/opt/ml/model") |
| `--resources-limits` | OBJECT | No | Resource limits for the worker |
| `--resources-requests` | OBJECT | No | Resource requests for the worker |
| `--dimensions` | OBJECT | No | CloudWatch Metric dimensions as key-value pairs |
| `--metric-collection-period` | INTEGER | No | Period for CloudWatch query (default: 300) |
| `--metric-collection-start-time` | INTEGER | No | StartTime for CloudWatch query (default: 300) |
| `--metric-name` | TEXT | No | Metric name to query for CloudWatch trigger |
| `--metric-stat` | TEXT | No | Statistics metric for CloudWatch (default: "Average") |
| `--metric-type` | TEXT | No | Type of metric for HPA ("Value" or "Average", default: "Average") |
| `--min-value` | NUMBER | No | Minimum metric value for empty CloudWatch response (default: 0) |
| `--cloud-watch-trigger-name` | TEXT | No | Name for the CloudWatch trigger |
| `--cloud-watch-trigger-namespace` | TEXT | No | AWS CloudWatch namespace for the metric |
| `--target-value` | NUMBER | No | Target value for the CloudWatch metric |
| `--use-cached-metrics` | BOOLEAN | No | Enable caching of metric values (default: true) |
| `--invocation-endpoint` | TEXT | No | Invocation endpoint path (default: "invocations") |
| `--debug` | FLAG | No | Enable debug mode (default: false) |


#### Invoke a Custom Inference Endpoint 

```bash
hyp invoke hyp-custom-endpoint \
    --endpoint-name endpoint-custom-pytorch \
    --body '{"inputs":"What is the capital of USA?"}'
```

#### Managing an Endpoint 

```bash
hyp list hyp-custom-endpoint
hyp describe hyp-custom-endpoint --name endpoint-custom
```

#### List Pods

```bash
hyp list-pods hyp-custom-endpoint
```

#### Get Logs

```bash
hyp get-logs hyp-custom-endpoint --pod-name <pod-name>
```

#### Get Operator Logs

```bash
hyp get-operator-logs hyp-custom-endpoint --since-hours 0.5
```

#### Deleting an Endpoint

```bash
hyp delete hyp-custom-endpoint --name endpoint-custom
```

### Space

#### Create a Space

```bash
hyp create hyp-space \
    --name myspace \
    --namespace default \
    --display-name "My Space"
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Space name |
| `--display-name` | TEXT | Yes | Display Name of the space |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--image` | TEXT | No | Image specifies the container image to use |
| `--desired-status` | TEXT | No | DesiredStatus specifies the desired operational status |
| `--ownership-type` | TEXT | No | OwnershipType specifies who can modify the space. 'Public' means anyone with RBAC permissions can update/delete the space. 'OwnerOnly' means only the creator can update/delete the space. |
| `--node-selector` | TEXT | No | NodeSelector specifies node selection constraints for the space pod (JSON string) |
| `--affinity` | TEXT | No | Affinity specifies node affinity and anti-affinity rules for the space pod (JSON string) |
| `--tolerations` | TEXT | No | Tolerations specifies tolerations for the space pod to schedule on nodes with matching taints (JSON string) |
| `--lifecycle` | TEXT | No | Lifecycle specifies actions that the management system should take in response to container lifecycle events (JSON string) |
| `--app-type` | TEXT | No | AppType specifies the application type for this workspace |
| `--service-account-name` | TEXT | No | ServiceAccountName specifies the name of the ServiceAccount to use for the workspace pod |
| `--idle-shutdown` | TEXT | No | Idle shutdown configuration. Format: --idle-shutdown enabled=<bool>,idleTimeoutInMinutes=<int>,detection=<JSON string> |
| `--template-ref` | TEXT | No | TemplateRef references a WorkspaceTemplate to use as base configuration. Format: --template-ref name=<name>,namespace=<namespace> |
| `--container-config` | TEXT | No | Container configuration. Format: --container-config command=<cmd>,args=<arg1;arg2> |
| `--storage` | TEXT | No | Storage configuration. Format: --storage storageClassName=<class>,size=<size>,mountPath=<path> |
| `--volume` | TEXT | No | Volume configuration. Format: --volume name=<name>,mountPath=<path>,persistentVolumeClaimName=<pvc_name>. Use multiple --volume flags for multiple volumes. |
| `--accelerator-partition-count` | TEXT | No | Fractional GPU partition count, e.g. '1' |
| `--accelerator-partition-type` | TEXT | No | Fractional GPU partition type, e.g. 'mig-3g.20gb' |
| `--gpu-limit` | TEXT | No | GPU resource limit, e.g. '1' |
| `--gpu` | TEXT | No | GPU resource request, e.g. '1' |
| `--memory-limit` | TEXT | No | Memory resource limit, e.g. '2Gi' |
| `--memory` | TEXT | No | Memory resource request, e.g. '2Gi' |
| `--cpu-limit` | TEXT | No | CPU resource limit, e.g. '500m' |
| `--cpu` | TEXT | No | CPU resource request, e.g. '500m' |

#### List Spaces

```bash
hyp list hyp-space
```

#### Describe a Space

```bash
hyp describe hyp-space --name myspace
```

#### Update a Space

```bash
hyp update hyp-space \
    --name myspace \
    --display-name "Updated Space Name"
```

#### Start/Stop a Space

```bash
hyp start hyp-space --name myspace
hyp stop hyp-space --name myspace
```

#### Get Logs

```bash
hyp get-logs hyp-space --name myspace
```

#### Delete a Space

```bash
hyp delete hyp-space --name myspace
```

#### Space Template Management

Create reusable space templates:

```bash
hyp create hyp-space-template --file template.yaml
hyp list hyp-space-template
hyp describe hyp-space-template --name <template-name>
hyp update hyp-space-template --name <template-name> --file updated-template.yaml
hyp delete hyp-space-template --name <template-name>
```

#### Space Access

Create remote access to spaces:

```bash
hyp create hyp-space-access --name myspace --connection-type vscode-remote
hyp create hyp-space-access --name myspace --connection-type web-ui
```

## SDK 

Along with the CLI, we also have SDKs available that can perform the cluster management, training and inference functionalities that the CLI performs

### Cluster Management SDK

#### Creating a Cluster Stack

```python
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

# Initialize cluster stack configuration
cluster_stack = HpClusterStack(
    stage="prod",
    resource_name_prefix="my-hyperpod",
    hyperpod_cluster_name="my-hyperpod-cluster",
    eks_cluster_name="my-hyperpod-eks",
    
    # Infrastructure components
    create_vpc_stack=True,
    create_eks_cluster_stack=True,
    create_hyperpod_cluster_stack=True,
    
    # Network configuration
    vpc_cidr="10.192.0.0/16",
    availability_zone_ids=["use2-az1", "use2-az2"],
    
    # Instance group configuration
    instance_group_settings=[
        {
            "InstanceCount": 1,
            "InstanceGroupName": "controller-group",
            "InstanceType": "ml.t3.medium",
            "TargetAvailabilityZoneId": "use2-az2"
        }
    ]
)

# Create the cluster stack
response = cluster_stack.create(region="us-east-2")
```

#### Listing Cluster Stacks

```python
# List all cluster stacks
stacks = HpClusterStack.list(region="us-east-2")
print(f"Found {len(stacks['StackSummaries'])} stacks")
```

#### Describing a Cluster Stack

```python
# Describe a specific cluster stack
stack_info = HpClusterStack.describe("my-stack-name", region="us-east-2")
print(f"Stack status: {stack_info['Stacks'][0]['StackStatus']}")
```

#### Monitoring Cluster Status

```python
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack

stack = HpClusterStack()
response = stack.create(region="us-west-2")
status = stack.get_status(region="us-west-2")
print(status)
```

#### Deleting a Cluster Stack

```python
# Delete with custom logger
import logging
logger = logging.getLogger(__name__)
HpClusterStack.delete("my-stack-name", region="us-west-2", logger=logger)

# Delete with retained resources (only works on DELETE_FAILED stacks)
HpClusterStack.delete("my-stack-name", retain_resources=["S3Bucket", "EFSFileSystem"])

```

### Training SDK

#### Creating a Training Job 

```python
from sagemaker.hyperpod.training.hyperpod_pytorch_job import HyperPodPytorchJob
from sagemaker.hyperpod.training.config.hyperpod_pytorch_job_unified_config import (
    ReplicaSpec, Template, Spec, Containers, Resources, RunPolicy
)
from sagemaker.hyperpod.common.config.metadata import Metadata

# Define job specifications
nproc_per_node = "1"  # Number of processes per node
replica_specs = 
[
    ReplicaSpec
    (
        name = "pod",  # Replica name
        template = Template
        (
            spec = Spec
            (
                containers =
                [
                    Containers
                    (
                        # Container name
                        name="container-name",  
                        
                        # Training image
                        image="123456789012.dkr.ecr.us-west-2.amazonaws.com/my-training-image:latest",  
                        
                        # Always pull image
                        image_pull_policy="Always",  
                        resources=Resources\
                        (
                            # No GPUs requested
                            requests={"nvidia.com/gpu": "0"},  
                            # No GPU limit
                            limits={"nvidia.com/gpu": "0"},   
                        ),
                        # Command to run
                        command=["python", "train.py"],  
                        # Script arguments
                        args=["--epochs", "10", "--batch-size", "32"],  
                    )
                ]
            )
        ),
    )
]
# Keep pods after completion
run_policy = RunPolicy(clean_pod_policy="None")  

# Create and start the PyTorch job
pytorch_job = HyperPodPytorchJob
(
    # Job name
    metadata = Metadata(name="demo"),  
    # Processes per node
    nproc_per_node = nproc_per_node,   
    # Replica specifications
    replica_specs = replica_specs,     
    # Run policy
    run_policy = run_policy,           
)
# Launch the job
pytorch_job.create()  
```    

#### List Training Jobs
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob
import yaml

# List all PyTorch jobs
jobs = HyperPodPytorchJob.list()
print(yaml.dump(jobs))
```

#### Describe a Training Job
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job")

print(job)
```

#### List Pods for a Training Job
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# List Pods for an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job")
print(job.list_pods())
```

#### Get Logs from a Pod
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get pod logs for a job
job = HyperPodPytorchJob.get(name="my-pytorch-job")
print(job.get_logs_from_pod("pod-name"))
```

#### Get Training Operator Logs
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get training operator logs
job = HyperPodPytorchJob.get(name="my-pytorch-job")
print(job.get_operator_logs(since_hours=0.1))
```

#### Delete a Training Job
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job")

# Delete the job
job.delete()
```

### Inference SDK

#### Creating a JumpstartModel Endpoint

Pre-trained Jumpstart models can be gotten from https://sagemaker.readthedocs.io/en/v2.82.0/doc_utils/jumpstart.html and fed into the call for creating the endpoint

```python
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import Model, Server, SageMakerEndpoint, TlsConfig
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

model=Model(
    model_id='deepseek-llm-r1-distill-qwen-1-5b'
)
server=Server(
    instance_type='ml.g5.8xlarge',
)
endpoint_name=SageMakerEndpoint(name='<my-endpoint-name>')

js_endpoint=HPJumpStartEndpoint(
    model=model,
    server=server,
    sage_maker_endpoint=endpoint_name
)

js_endpoint.create()
```

#### Creating a Custom Inference Endpoint (with S3)

```python
from sagemaker.hyperpod.inference.config.hp_endpoint_config import CloudWatchTrigger, Dimensions, AutoScalingSpec, Metrics, S3Storage, ModelSourceConfig, TlsConfig, EnvironmentVariables, ModelInvocationPort, ModelVolumeMount, Resources, Worker
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

model_source_config = ModelSourceConfig(
    model_source_type='s3',
    model_location="<my-model-folder-in-s3>",
    s3_storage=S3Storage(
        bucket_name='<my-model-artifacts-bucket>',
        region='us-east-2',
    ),
)

environment_variables = [
    EnvironmentVariables(name="HF_MODEL_ID", value="/opt/ml/model"),
    EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
    EnvironmentVariables(name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"),
    EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
    EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
]

worker = Worker(
    image='763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0',
    model_volume_mount=ModelVolumeMount(
        name='model-weights',
    ),
    model_invocation_port=ModelInvocationPort(container_port=8080),
    resources=Resources(
            requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
            limits={"nvidia.com/gpu": 1}
    ),
    environment_variables=environment_variables,
)

tls_config=TlsConfig(tls_certificate_output_s3_uri='s3://<my-tls-bucket-name>')

custom_endpoint = HPEndpoint(
    endpoint_name='<my-endpoint-name>',
    instance_type='ml.g5.8xlarge',
    model_name='deepseek15b-test-model-name',  
    tls_config=tls_config,
    model_source_config=model_source_config,
    worker=worker,
)

custom_endpoint.create()
```


#### List Endpoints

```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# List JumpStart endpoints
jumpstart_endpoints = HPJumpStartEndpoint.list()
print(jumpstart_endpoints)

# List custom endpoints
custom_endpoints = HPEndpoint.list()
print(custom_endpoints)
```

#### Describe an Endpoint
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Get JumpStart endpoint details
jumpstart_endpoint = HPJumpStartEndpoint.get(name="js-endpoint-name", namespace="test")
print(jumpstart_endpoint)

# Get custom endpoint details
custom_endpoint = HPEndpoint.get(name="endpoint-custom")
print(custom_endpoint)

```

#### Invoke an Endpoint
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

data = '{"inputs":"What is the capital of USA?"}'
jumpstart_endpoint = HPJumpStartEndpoint.get(name="endpoint-jumpstart")
response = jumpstart_endpoint.invoke(body=data).body.read()
print(response)

custom_endpoint = HPEndpoint.get(name="endpoint-custom")
response = custom_endpoint.invoke(body=data).body.read()
print(response)
```

#### List Pods
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# List pods 
js_pods = HPJumpStartEndpoint.list_pods()
print(js_pods)

c_pods = HPEndpoint.list_pods()
print(c_pods)
```

#### Get Logs
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Get logs from pod 
js_logs = HPJumpStartEndpoint.get_logs(pod=<pod-name>)
print(js_logs)

c_logs = HPEndpoint.get_logs(pod=<pod-name>)
print(c_logs)
```

#### Get Operator Logs
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Invoke JumpStart endpoint
print(HPJumpStartEndpoint.get_operator_logs(since_hours=0.1))

# Invoke custom endpoint
print(HPEndpoint.get_operator_logs(since_hours=0.1))
```

#### Delete an Endpoint
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Delete JumpStart endpoint
jumpstart_endpoint = HPJumpStartEndpoint.get(name="endpoint-jumpstart")
jumpstart_endpoint.delete()

# Delete custom endpoint
custom_endpoint = HPEndpoint.get(name="endpoint-custom")
custom_endpoint.delete()
```


#### Observability - Getting Monitoring Information
```python
from sagemaker.hyperpod.observability.utils import get_monitoring_config
monitor_config = get_monitoring_config()
```

### Space SDK

#### Creating a Space

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from hyperpod_space_template.v1_0.model import SpaceConfig

# Create space configuration
space_config = SpaceConfig(
    name="myspace",
    namespace="default",
    display_name="My Space",
)

# Create and start the space
space = HPSpace(config=space_config)
space.create()
```

#### List Spaces

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# List all spaces in default namespace
spaces = HPSpace.list()
for space in spaces:
    print(f"Space: {space.config.name}, Status: {space.status}")

# List spaces in specific namespace
spaces = HPSpace.list(namespace="your-namespace")
```

#### Get a Space

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get specific space
space = HPSpace.get(name="myspace", namespace="default")
print(f"Space name: {space.config.name}")
print(f"Display name: {space.config.display_name}")
```

#### Update a Space

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Update space configuration
space.update(
    display_name="Updated Space Name",
)
```

#### Start/Stop a Space

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Start the space
space.start()

# Stop the space
space.stop()
```

#### Get Space Logs

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get space and retrieve logs
space = HPSpace.get(name="myspace")

# Get logs from default pod and container
logs = space.get_logs()
print(logs)
```

#### List Space Pods

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get space and list associated pods
space = HPSpace.get(name="myspace")
pods = space.list_pods()
for pod in pods:
    print(f"Pod: {pod}")
```

#### Create Space Access

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Create VS Code remote access
vscode_access = space.create_space_access(connection_type="vscode-remote")
print(f"VS Code URL: {vscode_access['SpaceConnectionUrl']}")

# Create web UI access
web_access = space.create_space_access(connection_type="web-ui")
print(f"Web UI URL: {web_access['SpaceConnectionUrl']}")
```

#### Delete a Space

```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Delete the space
space.delete()
```

#### Space Template Management

```python
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate

# Create space template from YAML file
template = HPSpaceTemplate(file_path="template.yaml")
template.create()

# List all space templates
templates = HPSpaceTemplate.list()
for template in templates:
    print(f"Template: {template.name}")

# Get specific space template
template = HPSpaceTemplate.get(name="my-template")
print(template.to_yaml())

# Update space template
template.update(file_path="updated-template.yaml")

# Delete space template
template.delete()
```

## Examples
#### Cluster Management Example Notebooks

[CLI Cluster Management Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/cluster_management/cluster_creation_init_experience.ipynb)

[SDK Cluster Management Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/cluster_management/cluster_creation_sdk_experience.ipynb)

#### Training Example Notebooks

[CLI Training Init Experience Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-init-experience.ipynb)

[CLI Training Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-e2e-cli.ipynb)

[SDK Training Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/SDK/training_sdk_example.ipynb)

#### Inference Example Notebooks

##### CLI
[CLI Inference Jumpstart Model Init Experience Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-init-experience.ipynb)

[CLI Inference JumpStart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-e2e-cli.ipynb)

[CLI Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-fsx-model-e2e-cli.ipynb)

[CLI Inference S3 Model Init Experience Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-init-experience.ipynb)

[CLI Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-e2e-cli.ipynb)

##### SDK

[SDK Inference JumpStart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-jumpstart-e2e.ipynb)

[SDK Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-fsx-model-e2e.ipynb)

[SDK Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-s3-model-e2e.ipynb)


## Disclaimer 

* This CLI and SDK requires access to the user's file system to set and get context and function properly. 
It needs to read configuration files such as kubeconfig to establish the necessary environment settings.


## Working behind a proxy server ?
* Follow these steps from [here](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-proxy.html) to set up HTTP proxy connections

