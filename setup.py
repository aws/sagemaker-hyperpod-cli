import os
import subprocess

from setuptools import find_packages, setup

# Update submodules
subprocess.call(["git", "submodule", "update", "--init", "--recursive"])

# Declare your non-python data files:
# Files underneath configuration/ will be copied into the build preserving the
# subdirectory structure if they exist.
examples = []
for root, dirs, files in os.walk("src/hyperpod_cli/custom_launcher/examples/custom_script"):
    examples.append(
        (os.path.relpath(root, "examples/custom_script"), [os.path.join(root, f) for f in files])
    )

k8s_templates = []
for root, dirs, files in os.walk("src/hyperpod_cli/custom_launcher/launcher/nemo/k8s_templates"):
    k8s_templates.append(
        (
            os.path.relpath(root, "src/hyperpod_cli/custom_launcher/launcher/nemo/k8s_templates"),
            [os.path.join(root, f) for f in files],
        )
    )

nemo_framework_launcher = []
for root, dirs, files in os.walk(
    "src/hyperpod_cli/custom_launcher/launcher/nemo/nemo_framework_launcher"
):
    nemo_framework_launcher.append(
        (
            os.path.relpath(
                root, "src/hyperpod_cli/custom_launcher/launcher/nemo/nemo_framework_launcher"
            ),
            [os.path.join(root, f) for f in files],
        )
    )

setup(
    # include data files
    data_files=examples + k8s_templates + nemo_framework_launcher,
    name="hyperpod",
    version="0.1.0",
    packages=find_packages(where="src", exclude=("test",)),
    install_requires=[
        "click",
        "boto3",
        "botocore",
        "kubernetes",
        "pyyaml",
        "ratelimit",
        "tabulate",
        # NeMo framework required packages: https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/main/requirements.txt
        "hera",
        "omegaconf>=2.2,<2.3",
        "zstandard==0.15.2",
        "hydra-core>=1.2.0,<1.3",
        # Test dependencies
        "pytest",
        "pytest-cov",
    ],
    entry_points={
        "console_scripts": [
            "hyperpod=hyperpod_cli.cli:cli",
        ],
    },
    test_command="brazilpython_pytest",
    # Enable build-time format checking
    check_format=True,
    # Enable type checking
    test_mypy=True,
    # Enable linting at build time
    test_flake8=True,
)
