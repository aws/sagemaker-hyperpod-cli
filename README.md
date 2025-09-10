
# SageMaker HyperPod command-line interface

The Amazon SageMaker HyperPod command-line interface (HyperPod CLI) is a tool that helps manage training jobs on the SageMaker HyperPod clusters orchestrated by Amazon EKS.

This documentation serves as a reference for the available HyperPod CLI commands. For a comprehensive user guide, see [Orchestrating SageMaker HyperPod clusters with Amazon EKS](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-eks.html) in the *Amazon SageMaker Developer Guide*.

Note: Old `hyperpod`CLI V2 has been moved to `release_v2` branch. Please refer [release_v2 branch](https://github.com/aws/sagemaker-hyperpod-cli/tree/release_v2) for usage.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Platform Support](#platform-support)
- [ML Framework Support](#ml-framework-support)
- [Installation](#installation)
- [Usage](#usage)
  - [Getting Clusters](#getting-cluster-information)
  - [Connecting to a Cluster](#connecting-to-a-cluster)
  - [Getting Cluster Context](#getting-cluster-context)
  - [Listing Pods](#listing-pods)
  - [Accessing Logs](#accessing-logs)
  - [CLI](#cli)
    - [Cluster Management](#cluster-management)
    - [Training](#training)
    - [Inference](#inference)
  - [SDK](#sdk)
    - [Cluster Management](#cluster-management-sdk)
    - [Training](#training-sdk)
    - [Inference](#inference-sdk)
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
  - You can follow [inference operator doc](https://github.com/aws/sagemaker-hyperpod-cli/tree/master/helm_chart/HyperPodHelmChart/charts/inference-operator) to install it.

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

- [Getting Clusters](#getting-cluster-information)
- [Connecting to a Cluster](#connecting-to-a-cluster)
- [Getting Cluster Context](#getting-cluster-context)
- [Listing Pods](#listing-pods)
- [Accessing Logs](#accessing-logs)
- [CLI](#cli)
  - [Cluster Management](#cluster-management)
  - [Training](#training)
  - [Inference](#inference)
- [SDK](#sdk)
  - [Cluster Management](#cluster-management-sdk)
  - [Training](#training-sdk)
  - [Inference](#inference-sdk)


### Getting Cluster information

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

### Connecting to a Cluster

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

### Getting Cluster Context

Get all the context related to the current set Cluster

```bash
hyp get-cluster-context
```

| Option | Type | Description |
|--------|------|-------------|
| `--debug` | Optional | Enable debug mode for detailed logging. |

### Listing Pods

This command lists all the pods associated with a specific training job.

```bash
hyp list-pods hyp-pytorch-job --job-name <job-name>
```

* `job-name` (string) - Required. The name of the job to list pods for.

### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```bash
hyp get-logs hyp-pytorch-job --pod-name <pod-name> --job-name <job-name>
```

| Option | Type | Description |
|--------|------|-------------|
| `--job-name <job-name>` | Required | The name of the job to get the log for. |
| `--pod-name <pod-name>` | Required | The name of the pod to get the log from. |
| `--namespace <namespace>` | Optional | The namespace of the job. Defaults to 'default'. |
| `--container <container>` | Optional | The container name to get logs from. |


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
hyp create
```

**Note**: The region is determined from your AWS configuration or can be specified during the init experience.

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

#### Creating a Training Job 

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

Key required parameters explained:

    --job-name: Unique identifier for your training job

    --image: Docker image containing your training environment

### Inference 

#### Creating a JumpstartModel Endpoint

Pre-trained Jumpstart models can be gotten from https://sagemaker.readthedocs.io/en/v2.82.0/doc_utils/jumpstart.html and fed into the call for creating the endpoint

```bash
hyp create hyp-jumpstart-endpoint \
    --version 1.0 \
    --model-id jumpstart-model-id\
    --instance-type ml.g5.8xlarge \
    --endpoint-name endpoint-jumpstart
```


#### Invoke a JumpstartModel Endpoint

```bash
hyp invoke hyp-custom-endpoint \
    --endpoint-name endpoint-jumpstart \
    --body '{"inputs":"What is the capital of USA?"}'
```

**Note**: Both JumpStart and custom endpoints use the same invoke command.

#### Managing an Endpoint 

```bash
hyp list hyp-jumpstart-endpoint
hyp describe hyp-jumpstart-endpoint --name endpoint-jumpstart
```

#### Creating a Custom Inference Endpoint 

```bash
hyp create hyp-custom-endpoint \
    --version 1.0 \
    --endpoint-name my-custom-endpoint \
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

#### Invoke a Custom Inference Endpoint 

```bash
hyp invoke hyp-custom-endpoint \
    --endpoint-name endpoint-custom-pytorch \
    --body '{"inputs":"What is the capital of USA?"}'
```

#### Deleting an Endpoint

```bash
hyp delete hyp-jumpstart-endpoint --name endpoint-jumpstart
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



### Inference SDK

#### Creating a JumpstartModel Endpoint

Pre-trained Jumpstart models can be gotten from https://sagemaker.readthedocs.io/en/v2.82.0/doc_utils/jumpstart.html and fed into the call for creating the endpoint

```
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


#### Invoke a JumpstartModel Endpoint

```
data = '{"inputs":"What is the capital of USA?"}'
response = js_endpoint.invoke(body=data).body.read()
print(response)
```


#### Creating a Custom Inference Endpoint (with S3)

```
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

#### Invoke a Custom Inference Endpoint 

```
data = '{"inputs":"What is the capital of USA?"}'
response = custom_endpoint.invoke(body=data).body.read()
print(response)
```

#### Managing an Endpoint 

```
endpoint_list = HPEndpoint.list()
print(endpoint_list[0])

print(custom_endpoint.get_operator_logs(since_hours=0.5))

```

#### Deleting an Endpoint 

```
custom_endpoint.delete()

```

#### Observability - Getting Monitoring Information
```python
from sagemaker.hyperpod.observability.utils import get_monitoring_config
monitor_config = get_monitoring_config()
```

## Disclaimer 

* This CLI and SDK requires access to the user's file system to set and get context and function properly. 
It needs to read configuration files such as kubeconfig to establish the necessary environment settings.


## Working behind a proxy server ?
* Follow these steps from [here](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-proxy.html) to set up HTTP proxy connections

