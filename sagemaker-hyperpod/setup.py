from setuptools import setup, find_packages

setup(
    name="sagemaker-hyperpod",
    version="3.0.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"": ["*.whl", "py.typed"]},
    include_package_data=True,
    install_requires=[
        "awscli>=1.34.9",
        "awscli-cwlogs>=1.4.6",
        "boto3>=1.35.3,<2.0",
        "botocore>=1.35.6 ",
        "kubernetes==30.1.0",
        "pyyaml==6.0.2",
        "ratelimit==2.2.1",
        "tabulate==0.9.0",
        "pydantic==2.11.7",
        "pytest==8.3.2",
        "pytest-cov==5.0.0",
        "pytest-order==1.3.0",
        "tox==4.18.0",
        "ruff==0.6.2",
        "hera-workflows==5.16.3",
        "click==8.1.7",
        # NeMo framework required packages:
        # https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/requirements.txt
        "hydra-core==1.3.2",
        "omegaconf==2.3",
        "pynvml==11.4.1",
        "requests==2.32.3",
        "tqdm==4.66.5",
        "zstandard==0.15.2",
    ],
    entry_points={
        "console_scripts": [
            "hyp=sagemaker.hyperpod.cli.cli:cli",
        ],
    },
    check_format=True,
    # Enable type checking
    test_mypy=True,
    # Enable linting at build time
    test_flake8=True,
)
