(installation)=

# Installation

This guide provides installation instructions for the SageMaker HyperPod CLI and SDK.

## System Requirements

### Supported Platforms
- Linux
- macOS

```{note}
 Windows is not supported at this time.
```

### Supported ML Frameworks
- PyTorch (version ≥ 1.10)

### Supported Python Versions
- 3.9
- 3.10
- 3.11

## Prerequisites

### For Training
SageMaker HyperPod CLI currently supports `PyTorchJob` training workloads.
To run these jobs, install the **SageMaker Training Operator**.

[Install the SageMaker Training Operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html)

### For Inference
The CLI supports creating inference endpoints using JumpStart models or custom configurations.
To enable this, install the **SageMaker Inference Operator**.

[Install the SageMaker Inference Operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-model-deployment-setup.html)

## Installation Options

### Option 1: Install from PyPI

You can install the SageMaker HyperPod CLI and SDK directly using `pip`:

```bash
# Install from PyPI
pip install sagemaker-hyperpod
```

To verify that the installation was successful, run:

```bash
# Verify CLI installation
hyp --help
```

### Option 2: Install from Source

Clone the GitHub repository and install the CLI from source:

```bash
# Clone the repository
git clone https://github.com/aws/sagemaker-hyperpod-cli.git

# Change to the repository directory
cd sagemaker-hyperpod-cli

# Install using pip
pip install .
```
