# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import os
import subprocess

from setuptools import find_packages, setup

# Update submodules
subprocess.call(
    [
        "git",
        "submodule",
        "update",
        "--init",
        "--recursive",
        "--remote",
    ]
)

# Declare your non-python data files:
# Files underneath configuration/ will be copied into the build preserving the
# subdirectory structure if they exist.
examples = []
for root, dirs, files in os.walk(
    "src/hyperpod_cli/custom_launcher/examples/custom_script"
):
    examples.append(
        (
            os.path.relpath(root, "examples/custom_script"),
            [os.path.join(root, f) for f in files],
        )
    )

k8s_templates = []
for root, dirs, files in os.walk(
    "src/hyperpod_cli/custom_launcher/launcher/nemo/k8s_templates"
):
    k8s_templates.append(
        (
            os.path.relpath(
                root,
                "src/hyperpod_cli/custom_launcher/launcher/nemo/k8s_templates",
            ),
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
                root,
                "src/hyperpod_cli/custom_launcher/launcher/nemo/nemo_framework_launcher",
            ),
            [os.path.join(root, f) for f in files],
        )
    )

setup(
    data_files=examples + k8s_templates + nemo_framework_launcher,
    name="hyperpod",
    version="2.0.0",
    packages=find_packages(where="src", exclude=("test",)),
    install_requires=[
        "click==8.1.7",
        "awscli>=1.34.9",
        "awscli-cwlogs>=1.4.6",
        "boto3>=1.35.3,<2.0",
        "botocore>=1.35.6 ",
        "kubernetes==30.1.0",
        "pyyaml==6.0.2",
        "ratelimit==2.2.1",
        "tabulate==0.9.0",
        # NeMo framework required packages:
        # https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/requirements.txt
        "hydra-core==1.3.2",
        "omegaconf==2.3",
        "pynvml==11.4.1",
        "requests==2.32.3",
        "tqdm==4.66.5",
        "zstandard==0.15.2",
        # Test dependencies
        "pytest==8.3.2",
        "pytest-cov==5.0.0",
        "pytest-order==1.3.0",
        "tox==4.18.0",
        "ruff==0.6.2",
    ],
    entry_points={
        "console_scripts": [
            "hyperpod=hyperpod_cli.cli:cli",
        ],
    },
    check_format=True,
    # Enable type checking
    test_mypy=True,
    # Enable linting at build time
    test_flake8=True,
)
