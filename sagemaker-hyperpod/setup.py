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
    ],
)
