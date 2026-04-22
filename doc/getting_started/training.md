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


## Creating Training Jobs -- Recipe Job Init Experience

The `hyp-recipe-job` experience lets you submit fine-tuning and evaluation jobs using pre-built recipes published to SageMaker JumpStart Hub. No YAML authoring required — the CLI fetches the Kubernetes job template and parameter spec automatically.

### 1. Initialize a Recipe Job

`````{tab-set}
````{tab-item} CLI (HuggingFace model ID)
```bash
mkdir my-recipe-job
cd my-recipe-job
hyp init hyp-recipe-job . \
    --huggingface-model-id Qwen/Qwen3-0.6B \
    --technique SFT \
    --instance-type ml.g5.48xlarge
```
````
````{tab-item} CLI (JumpStart model ID)
```bash
mkdir my-recipe-job
cd my-recipe-job
hyp init hyp-recipe-job . \
    --model-id huggingface-reasoning-qwen3-06b \
    --technique SFT \
    --instance-type ml.g5.48xlarge
```
````
`````

Supported job types:
- **Fine-tuning**: `SFT`, `DPO`, `CPT`, `PPO`, `RLAIF`, `RLVR`
- **Evaluation**: `deterministic`, `LLMAJ`

```{note}
If you omit `--instance-type`, the CLI will automatically query your HyperPod clusters and find clusters with instance types supported by the selected recipe and technique. You will be presented with a list of compatible clusters to choose from. Note that this interactive prompt requires a terminal and is not supported in Jupyter notebooks.
```

This creates three files in your job directory:
- `config.yaml` — your editable training parameters
- `.override_spec.json` — the parameter schema
- `k8s.jinja` — the Kubernetes job template

### 3. Configure Recipe Job Parameters

```bash
hyp configure \
    --name my-recipe-job \
    --namespace default \
    --data-path /data/recipes-data/sft/train.jsonl \
    --global-batch-size 8 \
    --learning-rate 0.0001 \
    --max-epochs 1 \
    --output-path /data/output/my-model \
    --instance-type ml.g5.48xlarge
```

### 4. Validate Configuration

```bash
hyp validate
```

### 4a. Reset Configuration (Optional)

To reset `config.yaml` back to its default values:

```bash
hyp reset
```

### 5. Submit the Recipe Job

```bash
hyp create
```

### 6. Manage Recipe Jobs

```bash
# List jobs
hyp list hyp-recipe-job --namespace default

# Describe a job
hyp describe hyp-recipe-job --job-name <job-name> --namespace default

# List pods
hyp list-pods hyp-recipe-job --job-name <job-name> --namespace default

# Get logs
hyp get-logs hyp-recipe-job --job-name <job-name> --pod-name <pod-name> --namespace default

# Get operator logs
hyp get-operator-logs hyp-recipe-job

# Exec into pods
hyp exec hyp-recipe-job --job-name <job-name> --namespace default --all-pods -- echo hello

# Delete job
hyp delete hyp-recipe-job --job-name <job-name> --namespace default
```

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
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/end_to_end_walkthrough/01-training-job-submission/02-recipe-job-cli.ipynb" target="_blank">Recipe Job CLI Example</a>

These examples demonstrate end-to-end workflows for creating and managing training jobs using both the CLI and SDK approaches.
