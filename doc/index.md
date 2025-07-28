---
keywords:
  - distributed
  - kubernetes
  - pytorch
  - monitoring
  - jumpstart
---

(hpcli_docs_mainpage)=

# SageMaker HyperPod CLI & SDK

```{toctree}
:hidden:
:maxdepth: 1

Installation <installation>
Getting Started <getting_started>
Training <training>
Inference <inference>
Example Notebooks <examples>
API reference <_apidoc/modules>
```

**Manage distributed Machine Learning workloads on Kubernetes clusters without the complexity.**

The SageMaker HyperPod Command Line Interface and SDK simplify distributed training and inference on EKS-orchestrated clusters.

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