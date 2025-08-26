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
CLI Reference <cli/cli_index>
SDK Reference <sdk/sdk_index>
Advanced Resources <advanced_resources>
```

Transform your AI/ML development process with Amazon SageMaker HyperPod CLI and SDK. These tools handle infrastructure management complexities, allowing you to focus on model development and innovation. Whether it's scaling your PyTorch training jobs across thousands of GPUs, deploying production-grade inference endpoints or managing multiple clusters efficiently; the intuitive command-line interface and programmatic control enable you to:
- Accelerate development cycles and reduce operational overhead
- Automate ML workflows while maintaining operational visibility
- Optimize computing resources across your AI/ML projects


```{note}
Version Info - you’re viewing latest documentation for SageMaker Hyperpod CLI and SDK v3.0.0.
```


```{admonition} What's New
:class: important

🚀 We are excited to announce general availability of Amazon SageMaker HyperPod CLI and SDK!


**Major Updates**:
- **Distributed Training**: Scale PyTorch jobs across multiple nodes and GPUs with simplified management and automatic fault tolerance.
- **Model Inference**: Deploy pre-trained models from SageMaker JumpStart and host custom auto-scaling inference endpoints.
- **Observability**: Connect to and manage multiple HyperPod clusters with enhanced monitoring capabilities.
- **Usability Improvements**: Intuitive CLI for quick experimentation and cluster management, granular SDK control over workload configurations and easy access to system logs and observability dashboards for efficient debugging

```

## Quick Start


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

:::{grid-item-card} Training
:link: training
:link-type: ref
:class-card: sd-border-secondary

**Scale Your ML Models!** Get started with training
:::

:::{grid-item-card} Inference
:link: inference
:link-type: ref
:class-card: sd-border-secondary

**Deploy Your ML Model!** Get started with inference
:::

::::

## Advanced Resources

::::{grid} 1 2 2 2
:gutter: 3

:::{grid-item-card} API reference
:link: sdk/sdk_index.html
:class-card: sd-border-primary

**Explore APIs** - Checkout API Documentation
:::

:::{grid-item-card} Github
:link: examples
:link-type: ref
:class-card: sd-border-secondary

**Example Notebooks** - Ready-to-use implementation guides
:::

:::{grid-item-card} AWS SageMaker HyperPod Docs
:link: https://docs.aws.amazon.com/sagemaker/latest/dg/hyperpod.html
:link-type: url
:class-card: sd-border-secondary

**HyperPod Documentation** - Know more about HyperPod
:::

:::{grid-item-card} HyperPod Developer Guide
:link: https://catalog.workshops.aws/sagemaker-hyperpod-eks/en-US
:link-type: url
:class-card: sd-border-secondary

**Developer Guide** - Refer to this practical development guide
:::

:::{grid-item-card} SageMaker HyperPod Workshop
:link: https://catalog.workshops.aws/sagemaker-hyperpod-eks/en-US
:link-type: url
:class-card: sd-border-secondary

**Practical Guide** - Refer to the workshop for detailed follow-through steps
:::


::::
