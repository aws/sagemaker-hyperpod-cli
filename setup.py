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
sagemaker_hyperpod_recipes = []
for root, dirs, files in os.walk(
        "src/sagemaker/hyperpod/cli/sagemaker_hyperpod_recipes"
):
    sagemaker_hyperpod_recipes.append(
        (
            os.path.relpath(
                root,
                "src/sagemaker/hyperpod/cli/sagemaker_hyperpod_recipes",
            ),
            [os.path.join(root, f) for f in files],
        )
    )

setup(
    data_files=sagemaker_hyperpod_recipes,
    name="sagemaker-hyperpod",
    version="3.0.0",
    description="Amazon SageMaker HyperPod SDK and CLI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    url="https://github.com/aws/sagemaker-hyperpod-cli",
    packages=find_packages(where="src", exclude=("test",)),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "click==8.1.7",
        "awscli>=1.34.9",
        "awscli-cwlogs>=1.4.6",
        "boto3>=1.35.3,<2.0",
        "botocore>=1.35.6 ",
        "kubernetes==33.1.0",
        "pyyaml==6.0.2",
        "ratelimit==2.2.1",
        "tabulate==0.9.0",
        "itables>=2.2.2",
        "jinja2>=3.1.2",
        "ipywidgets>=8.1.7",
        # NeMo framework required packages:
        # https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/requirements.txt
        "hydra-core==1.3.2",
        "omegaconf==2.3",
        "pynvml==11.4.1",
        "requests==2.32.4",
        "tqdm==4.66.5",
        "zstandard==0.15.2",
        # Test dependencies
        "pytest==8.3.2",
        "pytest-cov==5.0.0",
        "pytest-order==1.3.0",
        "tox==4.18.0",
        "ruff==0.6.2",
        "hera-workflows==5.16.3",
        "sagemaker-core<2.0.0",
        "pydantic>=2.10.6,<3.0.0",
        "hyperpod-pytorch-job-template>=1.0.0, <2.0.0",
        "hyperpod-custom-inference-template>=1.0.0, <2.0.0",
        "hyperpod-jumpstart-inference-template>=1.0.0, <2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "hyp=sagemaker.hyperpod.cli.hyp_cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    check_format=True,
    # Enable type checking
    test_mypy=True,
    # Enable linting at build time
    test_flake8=True,
)
