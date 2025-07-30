(cli_install_configure)=

# Install and Configure CLI

This guide provides installation instructions for the SageMaker HyperPod CLI and SDK.

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

### Install from GitHub

For the latest development version or to contribute to the project, you can install directly from the GitHub repository:

**Clone the SageMaker HyperPod CLI package from GitHub:**
```bash
git clone https://github.com/aws/sagemaker-hyperpod-cli.git
```

**Install the SageMaker HyperPod CLI:**
```bash
cd sagemaker-hyperpod-cli && pip install .
```

**Test if the SageMaker HyperPod CLI is successfully installed by running the following command:**
```bash
hyp --help
```

```{note}
The GitHub installation provides access to the latest features and bug fixes that may not yet be available in the PyPI release. However, it may be less stable than the official PyPI release.
```
