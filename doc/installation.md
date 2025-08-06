(installation)=
# Get Started
This guide provides installation instructions for the SageMaker HyperPod CLI and SDK.

## System Requirements

### Supported Platforms
- Linux
- macOS

```{note}
 Windows is not supported at this time.
```

### Supported ML Frameworks for Training
- PyTorch (version ≥ 1.10)

### Supported Python Versions
- 3.9 and above

## Prerequisites

### For Training
SageMaker HyperPod CLI currently supports `HyperPodPytorchJob` training workloads.
To run these jobs, install the **SageMaker Training Operator**.

[Install the SageMaker Training Operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-eks-operator-install.html)

### For Inference
The CLI supports creating inference endpoints using JumpStart models or custom models.
To enable this, install the **SageMaker Inference Operator**.

[Install the SageMaker Inference Operator](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod-model-deployment-setup.html)

## Installation Options

### Install from PyPI

It's recommended to install the SageMaker HyperPod CLI and SDK in a Python virtual environment to avoid conflicts with other packages:
```bash
# Create a virtual environment
python -m venv {venv-name}

# Activate the virtual environment
source {venv-name}/bin/activate
```
```{note}
Remember to activate your virtual environment (source {venv-name}/bin/activate) each time you want to use the HyperPod CLI and SDK if you chose the virtual environment installation method.
```
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
