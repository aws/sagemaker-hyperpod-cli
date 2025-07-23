(training)=

# Training with SageMaker HyperPod

SageMaker HyperPod provides powerful capabilities for running distributed training workloads on EKS-hosted clusters. This guide covers how to create and manage training jobs using both the HyperPod CLI and SDK.

## Overview

SageMaker HyperPod training jobs allow you to:

- Run distributed PyTorch training workloads
- Specify custom Docker images with your training code
- Configure resource requirements (instance types, GPUs)
- Set up node selection with label selectors
- Manage job scheduling and priorities
- Mount volumes and persistent volume claims
- Store model artifacts in S3

## Creating Training Jobs

You can create training jobs using either the CLI or SDK approach:

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-pytorch-job \
    --version 1.0 \
    --job-name test-pytorch-job \
    --image pytorch/pytorch:latest \
    --command '["python", "train.py"]' \
    --args '["--epochs", "10", "--batch-size", "32"]' \
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
    --volumes '["data-vol", "model-vol", "checkpoint-vol"]' \
    --persistent-volume-claims '["shared-data-pvc", "model-registry-pvc"]' \
    --output-s3-uri s3://my-bucket/model-artifacts
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod import HyperPodPytorchJob
from sagemaker.hyperpod.job import ReplicaSpec, Template, Spec, Container, Resources, RunPolicy, Metadata

# Define job specifications
nproc_per_node = "1"  # Number of processes per node
replica_specs = [
    ReplicaSpec(
        name = "pod",  # Replica name
        template = Template(
            spec = Spec(
                containers = [
                    Container(
                        # Container name
                        name="container-name",  
                        
                        # Training image
                        image="123456789012.dkr.ecr.us-west-2.amazonaws.com/my-training-image:latest",  
                        
                        # Always pull image
                        image_pull_policy="Always",  
                        resources=Resources(
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

# Create the PyTorch job
pytorch_job = HyperPodPytorchJob(
    job_name="my-pytorch-job",
    replica_specs=replica_specs,
    run_policy=RunPolicy(
        clean_pod_policy="Running"  # Keep pods after completion
    )
)

# Submit the job
pytorch_job.create()
```
````
`````

## Key Parameters

When creating a training job, you'll need to specify:

- **job-name**: Unique identifier for your training job
- **image**: Docker image containing your training environment
- **command**: Command to run inside the container
- **args**: Arguments to pass to the command
- **instance-type**: The EC2 instance type to use
- **tasks-per-node**: Number of processes to run per node
- **output-s3-uri**: S3 location to store model artifacts

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
from sagemaker.hyperpod import HyperPodManager

# List all PyTorch jobs
jobs = HyperPodManager.list_jobs(job_type="hyp-pytorch-job")
print(jobs)
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
from sagemaker.hyperpod import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.load(job_name="my-pytorch-job")

# Get job details
job_details = job.describe()
print(job_details)
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
from sagemaker.hyperpod import HyperPodPytorchJob

# Get an existing job
job = HyperPodPytorchJob.load(job_name="my-pytorch-job")

# Delete the job
job.delete()
```
````
`````

## Training Example Notebooks

For detailed examples of training with HyperPod, see:

- [CLI Training Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/CLI/training-e2e-cli.ipynb)
- [SDK Training Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/training/SDK/training_sdk_example.ipynb)

These examples demonstrate end-to-end workflows for creating and managing training jobs using both the CLI and SDK approaches.
