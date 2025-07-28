---
keywords:
  - distributed
  - kubernetes
  - pytorch
  - containerized
  - orchestration
---

(training)=

# Training with SageMaker HyperPod

SageMaker HyperPod provides powerful capabilities for running distributed training workloads on EKS-orchestrated clusters. This guide covers how to create and manage training jobs using both the HyperPod CLI and SDK.

## Overview

SageMaker HyperPod training jobs allow you to:

- Run distributed PyTorch training workloads
- Specify custom Docker images with your training code
- Configure resource requirements (instance types, GPUs)
- Set up node selection with label selectors
- Manage job scheduling and priorities
- Mount volumes and persistent volume claims

## Creating Training Jobs

You can create training jobs using either the CLI or SDK approach:

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-pytorch-job \
    --job-name test-pytorch-job \
    --image pytorch/pytorch:latest \
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.training import (
    HyperPodPytorchJob,
    Containers,
    ReplicaSpec,
    Resources,
    RunPolicy,
    Spec,
    Template,
)
from sagemaker.hyperpod.common.config import Metadata


nproc_per_node="1"
replica_specs=[
    ReplicaSpec(
        name="pod",
        template=Template(
            spec=Spec(
                containers=[
                    Containers(
                        name="container-name",
                        image="448049793756.dkr.ecr.us-west-2.amazonaws.com/ptjob:mnist",
                        image_pull_policy="Always",
                        resources=Resources(
                            requests={"nvidia.com/gpu": "0"},
                            limits={"nvidia.com/gpu": "0"},
                        ),
                        # command=[]
                    )
                ]
            )
        ),
    )
]
run_policy=RunPolicy(clean_pod_policy="None")

pytorch_job = HyperPodPytorchJob(
    metadata=Metadata(name="demo"),
    nproc_per_node="1",
    replica_specs=replica_specs,
    run_policy=run_policy,
)

pytorch_job.create()
```
````
`````

### Key Parameters

When creating a training job, you'll need to specify:

- **job-name**: Unique identifier for your training job
- **image**: Docker image containing your training environment


## Managing Training Jobs

### List Training Jobs

`````{tab-set}
````{tab-item} CLI
```bash
hyp list hyp-pytorch-job
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob
import yaml

# List all PyTorch jobs
jobs = HyperPodPytorchJob.list()
print(yaml.dump(jobs))
```
````
`````

### Describe a Training Job

`````{tab-set}
````{tab-item} CLI
```bash
hyp describe hyp-pytorch-job --job-name <job-name>
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job", namespace="my-namespace")

print(job)
```
````
`````

### List Pods for a Training Job

`````{tab-set}
````{tab-item} CLI
```bash
hyp list-pods hyp-pytorch-job --job-name <job-name>
```
````

````{tab-item} SDK
```python
print(pytorch_job.list_pods())
```
````
`````

### Get Logs from a Pod

`````{tab-set}
````{tab-item} CLI
```bash
hyp get-logs hyp-pytorch-job --pod-name test-pytorch-job-cli-pod-0 --job-name test-pytorch-job-cli
```
````

````{tab-item} SDK
```python
print(pytorch_job.get_logs_from_pod("pod-name"))
```
````
`````

### Delete a Training Job

`````{tab-set}
````{tab-item} CLI
```bash
hyp delete hyp-pytorch-job --job-name <job-name>
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job", namespace="my-namespace")

# Delete the job
job.delete()
```
````
`````

## Training Example Notebooks

For detailed examples of training with HyperPod, see:

- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-e2e-cli.ipynb" target="_blank">CLI Training Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/SDK/training_sdk_example.ipynb" target="_blank">SDK Training Example</a>

These examples demonstrate end-to-end workflows for creating and managing training jobs using both the CLI and SDK approaches.
