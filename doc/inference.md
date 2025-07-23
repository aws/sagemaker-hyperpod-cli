(inference)=

# Inference with SageMaker HyperPod

SageMaker HyperPod provides powerful capabilities for deploying and managing inference endpoints on EKS-hosted clusters. This guide covers how to create, invoke, and manage inference endpoints using both the HyperPod CLI and SDK.

## Overview

SageMaker HyperPod inference endpoints allow you to:

- Deploy pre-trained JumpStart models
- Deploy custom models with your own inference code
- Configure resource requirements for inference
- Manage endpoint lifecycle
- Invoke endpoints for real-time predictions
- Monitor endpoint performance

## Creating Inference Endpoints

You can create inference endpoints using either JumpStart models or custom models:

### JumpStart Model Endpoints

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-jumpstart-endpoint \
    --version 1.0 \
    --model-id jumpstart-model-id \
    --instance-type ml.g5.8xlarge \
    --endpoint-name endpoint-jumpstart \
    --tls-output-s3-uri s3://sample-bucket
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import Model, Server, SageMakerEndpoint, TlsConfig
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

model = Model(
    model_id="deepseek-llm-r1-distill-qwen-1-5b",
    model_version="2.0.4"
)

server = Server(
    instance_type="ml.g5.8xlarge"
)

endpoint_name = SageMakerEndpoint(name="endpoint-jumpstart")

tls_config = TlsConfig(tls_certificate_output_s3_uri="s3://sample-bucket")

js_endpoint = HPJumpStartEndpoint(
    model=model,
    server=server,
    sage_maker_endpoint=endpoint_name,
    tls_config=tls_config
)

js_endpoint.create()
```
````
`````

### Custom Model Endpoints

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-custom-endpoint \
    --version 1.0 \
    --endpoint-name endpoint-custom \
    --model-uri s3://my-bucket/model-artifacts \
    --image 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-inference-image:latest \
    --instance-type ml.g5.8xlarge \
    --tls-output-s3-uri s3://sample-bucket
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.config.hp_custom_endpoint_config import Model, Server, SageMakerEndpoint, TlsConfig, EnvironmentVariables
from sagemaker.hyperpod.inference.hp_custom_endpoint import HPCustomEndpoint

model = Model(
    model_source_type="s3",
    model_location="test-pytorch-job/model.tar.gz",
    s3_bucket_name="my-bucket",
    s3_region="us-east-2",
    prefetch_enabled=True
)

server = Server(
    instance_type="ml.g5.8xlarge",
    image_uri="763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0",
    container_port=8080,
    model_volume_mount_name="model-weights"
)

resources = {
    "requests": {"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
    "limits": {"nvidia.com/gpu": 1}
}

env = EnvironmentVariables(
    HF_MODEL_ID="/opt/ml/model",
    SAGEMAKER_PROGRAM="inference.py",
    SAGEMAKER_SUBMIT_DIRECTORY="/opt/ml/model/code",
    MODEL_CACHE_ROOT="/opt/ml/model",
    SAGEMAKER_ENV="1"
)

endpoint_name = SageMakerEndpoint(name="endpoint-custom-pytorch")

tls_config = TlsConfig(tls_certificate_output_s3_uri="s3://sample-bucket")

custom_endpoint = HPCustomEndpoint(
    model=model,
    server=server,
    resources=resources,
    environment=env,
    sage_maker_endpoint=endpoint_name,
    tls_config=tls_config,
)

custom_endpoint.create()
```
````
`````

## Key Parameters

When creating an inference endpoint, you'll need to specify:

- **endpoint-name**: Unique identifier for your endpoint
- **model-id** (JumpStart): ID of the pre-trained JumpStart model
- **model-uri** (Custom): S3 location of your model artifacts
- **image** (Custom): Docker image containing your inference code
- **instance-type**: The EC2 instance type to use
- **tls-output-s3-uri**: S3 location to store TLS certificates

## Managing Inference Endpoints

### List Endpoints

`````{tab-set}
````{tab-item} CLI
```bash
# List JumpStart endpoints
hyp list hyp-jumpstart-endpoint

# List custom endpoints
hyp list hyp-custom-endpoint
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_custom_endpoint import HPCustomEndpoint

# List JumpStart endpoints
jumpstart_endpoints = HPJumpStartEndpoint.list()
print(jumpstart_endpoints)

# List custom endpoints
custom_endpoints = HPCustomEndpoint.list()
print(custom_endpoints)
```
````
`````

### Describe an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Describe JumpStart endpoint
hyp describe hyp-jumpstart-endpoint --endpoint-name <endpoint-name>

# Describe custom endpoint
hyp describe hyp-custom-endpoint --endpoint-name <endpoint-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference import HyperPodJumpstartEndpoint, HyperPodCustomEndpoint

# Get JumpStart endpoint details
jumpstart_endpoint = HyperPodJumpstartEndpoint.load(endpoint_name="endpoint-jumpstart")
jumpstart_details = jumpstart_endpoint.describe()
print(jumpstart_details)

# Get custom endpoint details
custom_endpoint = HyperPodCustomEndpoint.load(endpoint_name="endpoint-custom")
custom_details = custom_endpoint.describe()
print(custom_details)
```
````
`````

### Invoke an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Invoke custom endpoint
hyp invoke hyp-custom-endpoint \
    --endpoint-name <endpoint-name> \
    --content-type "application/json" \
    --payload '{"inputs": "What is machine learning?"}'
```
````

````{tab-item} SDK
```python
data = '{"inputs":"What is the capital of USA?"}'
response = endpoint.invoke(body=data).body.read()
print(response)
```
````
`````

### Delete an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Delete JumpStart endpoint
hyp delete hyp-jumpstart-endpoint --endpoint-name <endpoint-name>

# Delete custom endpoint
hyp delete hyp-custom-endpoint --endpoint-name <endpoint-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference import HyperPodJumpstartEndpoint, HyperPodCustomEndpoint

# Delete JumpStart endpoint
jumpstart_endpoint = HyperPodJumpstartEndpoint.load(endpoint_name="endpoint-jumpstart")
jumpstart_endpoint.delete()

# Delete custom endpoint
custom_endpoint = HyperPodCustomEndpoint.load(endpoint_name="endpoint-custom")
custom_endpoint.delete()
```
````
`````

## Inference Example Notebooks

For detailed examples of inference with HyperPod, see:
- [CLI Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-fsx-model-e2e-cli.ipynb)
- [CLI Inference Jumpstart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-e2e-cli.ipynb)
- [CLI Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-e2e-cli.ipynb)
- [SDK Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-fsx-model-e2e.ipynb)
- [SDK Inference Jumpstart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-jumpstart-e2e.ipynb)
- [SDK Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-s3-model-e2e.ipynb)

