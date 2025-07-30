---
keywords:
  - distributed
  - kubernetes
  - pytorch
  - monitoring
  - jumpstart
---

(hpcli_docs_mainpage)=

# Overview

```{toctree}
:hidden:
:maxdepth: 1

Installation <installation>
Getting Started <getting_started>
Training <training>
Inference <inference>
CLI Reference <cli_reference>
Example Notebooks <examples>
API reference <_apidoc/modules>
```

Amazon SageMaker HyperPod CLI and SDK are developer tools designed to simplify the management of distributed training workloads on dedicated, high-performance computing clusters. These tools enable ML practitioners to efficiently orchestrate large-scale training operations while abstracting the underlying cluster management complexities.

### What is SageMaker HyperPod CLI and SDK?

The **SageMaker HyperPod CLI** is a command-line interface that enables you to create and manage distributed training clusters and workloads through simple commands. It provides direct control over cluster resources while handling the infrastructure management automatically.

The **SageMaker HyperPod SDK** is a Python library that allows programmatic access to HyperPod functionality for seamless incorporation into your ML workflows and training scripts.

Both tools are built on top of [Amazon SageMaker HyperPod](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html), a managed service that provides dedicated, persistent clusters optimized for distributed ML training workloads.

### Key Use Cases

**Distributed Training**
- Scale PyTorch training jobs across multiple nodes and GPUs
- Manage complex distributed training configurations with simple commands
- Handle fault tolerance and job recovery automatically

**Model Inference**
- Deploy pre-trained models from SageMaker JumpStart with minimal configuration
- Host custom inference endpoints with auto-scaling capabilities
- Manage model serving infrastructure with built-in monitoring

**Cluster Operations**
- Connect to and manage multiple HyperPod clusters
- Monitor resource utilization and job status
- Streamline DevOps workflows for ML teams

### Why Choose HyperPod CLI & SDK?

- **Simplified Management**: Focus on ML code while HyperPod handles infrastructure orchestration
- **AWS Integration**: Native integration with SageMaker features and AWS services
- **Production Ready**: Built-in fault tolerance, auto-scaling, and enterprise security features
- **Development Flexibility**: Choose between CLI for direct control or SDK for programmatic access
- **Cost Management**: Optimize spending with cluster sharing and resource monitoring

For comprehensive information about the underlying infrastructure and advanced configuration options, see the [Amazon SageMaker HyperPod documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html).

## Quick Start

::::{container}
::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} Installation
:link: installation
:link-type: ref
:class-card: sd-border-primary

**New to HyperPod?** Install the CLI/ SDK in minutes.
:::

:::{grid-item-card} Getting Started
:link: getting_started
:link-type: ref
:class-card: sd-border-secondary

**Ready to explore?** Connect to your cluster before running ML workflows.
:::

::::
::::

## What You Can Do

::::{container}
::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Training Workloads
:class-card: sd-border-success

**Distributed Training**
- HyperPodPytorchJob distributed training
- Multi-node, multi-GPU support
- Built-in monitoring and logging

```{dropdown} Learn More About Training
:color: success
:icon: chevron-down

- [Training Guide](training.md) - Complete training workflows
- [Example Notebooks](examples.md) - Hands-on training examples
- Supported frameworks: PyTorch
```
:::

:::{grid-item-card} Inference Endpoints
:class-card: sd-border-info

**Model Serving**
- Deploy models as scalable endpoints
- JumpStart model integration
- Real-time and batch inference

```{dropdown} Learn More About Inference
:color: info
:icon: chevron-down

- [Inference Guide](inference.md) - Complete inference workflows
- [Example Notebooks](examples.md) - Hands-on inference examples
- Supported models: JumpStart models, Custom models
```
:::

::::
::::

## Choose Your Interface

::::{container}
::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Command Line Interface
:class-card: sd-border-warning

**For DevOps & Quick Tasks**
```bash
# Launch a training job
hyp create hyp-pytorch-job \
  --job-name my-training \
  --image pytorch/pytorch:latest \
```

```{dropdown} CLI Features
:color: warning
:icon: terminal

- Interactive job management
- Built-in status monitoring
```
:::

:::{grid-item-card} Python SDK
:class-card: sd-border-danger

**For Programmatic Control**
```python
from sagemaker.hyperpod.training import HyperPodPytorchJob
from sagemaker.hyperpod.common.config import Metadata

pytorch_job = HyperPodPytorchJob(
    metadata=Metadata(name="demo"),
    nproc_per_node="1",
    replica_specs=replica_specs,
    run_policy=run_policy,
)

pytorch_job.create()
```

```{dropdown} SDK Features
:color: danger
:icon: code

- Pythonic API design
- Jupyter notebook integration
- Programmatic job orchestration
```
:::

::::
::::

## Advanced Resources

```{dropdown} Complete Documentation
:color: primary
:icon: book

- [API Reference](_apidoc/modules.rst) - Complete SDK documentation
- [Training Guide](training.md) - In-depth training workflows
- [Inference Guide](inference.md) - Comprehensive inference setup
- [Example Notebooks](examples.md) - End-to-end examples
```