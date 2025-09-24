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


## Creating Training Jobs -- CLI Init Experience


### 1. Start with a Clean Directory

It\'s recommended to start with a new and clean directory for each
job configuration:

``` bash
mkdir my-pytorch-job
cd my-pytorch-job
```

### 2. Initialize a New Job Configuration

`````{tab-set}
````{tab-item} CLI
``` bash
hyp init hyp-pytorch-job
```
````
`````

This creates three files:

- `config.yaml`: The main configuration file you\'ll use to customize
  your job
- `k8s.jinja`: A reference template for parameters mapping in kubernetes payload
- `README.md`: Usage guide with instructions and examples


### 3. Configure Your Job

You can configure your job in two ways:

**Option 1: Edit config.yaml directly**

The config.yaml file contains key parameters like:

``` yaml
template: hyp-pytorch-job
version: 1.1
job_name:
image: 
```

**Option 2: Use CLI command (Pre-Deployment)**

`````{tab-set}
````{tab-item} CLI
``` bash
hyp configure --job-name your-job-name
```
````
`````

```{note}
The `hyp configure` command only modifies local configuration files. It
does not affect existing deployed jobs.
```

### 4. Create the Job


`````{tab-set}
````{tab-item} CLI
``` bash
hyp create
```
````
`````

This will:

- Validate your configuration
- Create a timestamped folder in the `run` directory
- Initialize the job creation process


## Creating Training Jobs -- CLI/SDK

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

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| **job-name** | TEXT | Yes | Unique identifier for your training job |
| **image** | TEXT | Yes | Docker image containing your training environment |
| **accelerators** | INTEGER | No | Number of accelerators a.k.a GPUs or Trainium Chips |
| **vcpu** | FLOAT | No | Number of vCPUs |
| **memory** | FLOAT | No | Amount of memory in GiB |
| **accelerators-limit** | INTEGER | No | Limit for the number of accelerators a.k.a GPUs or Trainium Chips |
| **vcpu-limit** | FLOAT | No | Limit for the number of vCPUs |
| **memory-limit** | FLOAT | No | Limit for the amount of memory in GiB |
| **preferred-topology** | TEXT | No | Preferred topology annotation for scheduling |
| **required-topology** | TEXT | No | Required topology annotation for scheduling |
| **debug** | FLAG | No | Enable debug mode |


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
job = HyperPodPytorchJob.get(name="my-pytorch-job")

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
from sagemaker.hyperpod.training import HyperPodPytorchJob

# List Pods for an existing job
job = HyperPodPytorchJob.get(name="my-pytorch-job")
print(job.list_pods())
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
from sagemaker.hyperpod.training import HyperPodPytorchJob

# Get pod logs for a job
job = HyperPodPytorchJob.get(name="my-pytorch-job")
print(job.get_logs_from_pod("pod-name"))
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
job = HyperPodPytorchJob.get(name="my-pytorch-job")

# Delete the job
job.delete()
```
````
`````

## Training Example Notebooks

For detailed examples of training with HyperPod, see:

- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-init-experience.ipynb" target="_blank">CLI Training Init Experience Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-e2e-cli.ipynb" target="_blank">CLI Training Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/SDK/training_sdk_example.ipynb" target="_blank">SDK Training Example</a>

These examples demonstrate end-to-end workflows for creating and managing training jobs using both the CLI and SDK approaches.
