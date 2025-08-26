
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
  - [CLI](#cli-)
    - [Training](#training-)
    - [Inference](#inference-)
  - [SDK](#sdk-)
    - [Training](#training-sdk)
    - [Inference](#inference-sdk)
  

## Overview

The SageMaker HyperPod CLI is a tool that helps create training jobs and inference endpoint deployments to the Amazon SageMaker HyperPod clusters orchestrated by Amazon EKS. It provides a set of commands for managing the full lifecycle of jobs, including create, describe, list, and delete operations, as well as accessing pod and operator logs where applicable. The CLI is designed to abstract away the complexity of working directly with Kubernetes for these core actions of managing jobs on SageMaker HyperPod clusters orchestrated by Amazon EKS.

## Prerequisites for Training

- HyperPod CLI currently supports starting PyTorchJobs. To start a job, you need to install Training Operator first. 
  - You can follow [pytorch operator doc](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html) to install it.

## Prerequisites for Inference 

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

    ```
    pip install sagemaker-hyperpod
    ```

3. Verify if the installation succeeded by running the following command.

    ```
    hyp --help
    ```

## Usage

The HyperPod CLI provides the following commands:

- [Getting Clusters](#getting-cluster-information)
- [Connecting to a Cluster](#connecting-to-a-cluster)
- [Getting Cluster Context](#getting-cluster-context)
- [Listing Pods](#listing-pods)
- [Accessing Logs](#accessing-logs)
- [CLI](#cli-)
  - [Training](#training-)
  - [Inference](#inference-)
- [SDK](#sdk-)
  - [Training](#training-sdk)
  - [Inference](#inference-sdk)


### Getting Cluster information

This command lists the available SageMaker HyperPod clusters and their capacity information.

```
hyp list-cluster [--region <region>]  [--namespace <namespace>] [--output <json|table>]
```

* `region` (string) - Optional. The region that the SageMaker HyperPod and EKS clusters are located. If not specified, it will be set to the region from the current AWS account credentials.
* `namespace` (string) - Optional. The namespace that users want to check the quota with. Only the SageMaker managed namespaces are supported.
* `output` (enum) - Optional. The output format. Available values are `table` and `json`. The default value is `json`.

### Connecting to a Cluster

This command configures the local Kubectl environment to interact with the specified SageMaker HyperPod cluster and namespace.

```
hyp set-cluster-context --cluster-name <cluster-name> [--namespace <namespace>]
```

* `cluster-name` (string) - Required. The SageMaker HyperPod cluster name to configure with.
* `namespace` (string) - Optional. The namespace that you want to connect to. If not specified, Hyperpod cli commands will auto discover the accessible namespace.

### Getting Cluster Context

Get all the context related to the current set Cluster

```
hyp get-cluster-context
```

### Listing Pods

This command lists all the pods associated with a specific training job.

```
hyp list-pods hyp-pytorch-job --job-name <job-name>
```

* `job-name` (string) - Required. The name of the job to list pods for.

### Accessing Logs

This command retrieves the logs for a specific pod within a training job.

```
hyp get-logs hyp-pytorch-job --pod-name <pod-name> --job-name <job-name>
```

* `job-name` (string) - Required. The name of the job to get the log for.
* `pod-name` (string) - Required. The name of the pod to get the log from.


### CLI 

### Training 

#### Creating a Training Job 

```
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

```
hyp create hyp-jumpstart-endpoint \
    --version 1.0 \
    --model-id jumpstart-model-id\
    --instance-type ml.g5.8xlarge \
    --endpoint-name endpoint-jumpstart \
```


#### Invoke a JumpstartModel Endpoint

```
hyp invoke hyp-jumpstart-endpoint \
    --endpoint-name endpoint-jumpstart \
    --body '{"inputs":"What is the capital of USA?"}'
```

#### Managing an Endpoint 

```
hyp list hyp-jumpstart-endpoint
hyp describe hyp-jumpstart-endpoint --name endpoint-jumpstart
```

#### Creating a Custom Inference Endpoint 

```
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

```
hyp invoke hyp-custom-endpoint \
    --endpoint-name endpoint-custom-pytorch \
    --body '{"inputs":"What is the capital of USA?"}'
    
```

#### Deleting an Endpoint

```
hyp delete hyp-jumpstart-endpoint --name endpoint-jumpstart
```


## SDK 

Along with the CLI, we also have SDKs available that can perform the training and inference functionalities that the CLI performs

### Training SDK

#### Creating a Training Job 

```

from sagemaker.hyperpod.training import HyperPodPytorchJob
from sagemaker.hyperpod.training
import ReplicaSpec, Template, Spec, Containers, Resources, RunPolicy
from sagemaker.hyperpod.common.config import Metadata

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
```
from sagemaker.hyperpod.utils import get_monitoring_config,
monitor_config = get_monitoring_config()
monitor_config.grafanaURL
monitor_config.prometheusURL
```

## Disclaimer 

* This CLI and SDK requires access to the user's file system to set and get context and function properly. 
It needs to read configuration files such as kubeconfig to establish the necessary environment settings.


## Working behind a proxy server ?
* Follow these steps from [here](https://docs.aws.amazon.com/cli/v1/userguide/cli-configure-proxy.html) to set up HTTP proxy connections

