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

**CLI**
```bash
hyp create hyp-jumpstart-endpoint \
    --version 1.0 \
    --model-id jumpstart-model-id \
    --instance-type ml.g5.8xlarge \
    --endpoint-name endpoint-jumpstart \
    --tls-output-s3-uri s3://sample-bucket
```

**SDK**
```python
from sagemaker.hyperpod.inference import HyperPodJumpstartEndpoint

# Create a JumpStart endpoint
endpoint = HyperPodJumpstartEndpoint(
    endpoint_name="endpoint-jumpstart",
    model_id="jumpstart-model-id",
    instance_type="ml.g5.8xlarge",
    tls_output_s3_uri="s3://sample-bucket"
)

# Deploy the endpoint
endpoint.create()
```

### Custom Model Endpoints

**CLI**
```bash
hyp create hyp-custom-endpoint \
    --version 1.0 \
    --endpoint-name endpoint-custom \
    --model-uri s3://my-bucket/model-artifacts \
    --image 123456789012.dkr.ecr.us-west-2.amazonaws.com/my-inference-image:latest \
    --instance-type ml.g5.8xlarge \
    --tls-output-s3-uri s3://sample-bucket
```

**SDK**
```python
from sagemaker.hyperpod.inference import HyperPodCustomEndpoint

# Create a custom endpoint
endpoint = HyperPodCustomEndpoint(
    endpoint_name="endpoint-custom",
    model_uri="s3://my-bucket/model-artifacts",
    image="123456789012.dkr.ecr.us-west-2.amazonaws.com/my-inference-image:latest",
    instance_type="ml.g5.8xlarge",
    tls_output_s3_uri="s3://sample-bucket"
)

# Deploy the endpoint
endpoint.create()
```

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

**CLI**
```bash
# List JumpStart endpoints
hyp list hyp-jumpstart-endpoint

# List custom endpoints
hyp list hyp-custom-endpoint
```

**SDK**
```python
from sagemaker.hyperpod.inference import HyperPodJumpstartEndpoint, HyperPodCustomEndpoint

# List JumpStart endpoints
jumpstart_endpoints = HyperPodJumpstartEndpoint.list()
print(jumpstart_endpoints)

# List custom endpoints
custom_endpoints = HyperPodCustomEndpoint.list()
print(custom_endpoints)
```

### Describe an Endpoint

**CLI**
```bash
# Describe JumpStart endpoint
hyp describe hyp-jumpstart-endpoint --endpoint-name <endpoint-name>

# Describe custom endpoint
hyp describe hyp-custom-endpoint --endpoint-name <endpoint-name>
```

**SDK**
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

### Invoke an Endpoint

**CLI**
```bash
# Invoke custom endpoint
hyp invoke hyp-custom-endpoint \
    --endpoint-name <endpoint-name> \
    --content-type "application/json" \
    --payload '{"inputs": "What is machine learning?"}'
```

**SDK**
```python
from sagemaker.hyperpod.inference import HyperPodCustomEndpoint

# Load the endpoint
endpoint = HyperPodCustomEndpoint.load(endpoint_name="endpoint-custom")

# Invoke the endpoint
response = endpoint.invoke(
    payload={"inputs": "What is machine learning?"},
    content_type="application/json"
)
print(response)
```

### Delete an Endpoint

**CLI**
```bash
# Delete JumpStart endpoint
hyp delete hyp-jumpstart-endpoint --endpoint-name <endpoint-name>

# Delete custom endpoint
hyp delete hyp-custom-endpoint --endpoint-name <endpoint-name>
```

**SDK**
```python
from sagemaker.hyperpod.inference import HyperPodJumpstartEndpoint, HyperPodCustomEndpoint

# Delete JumpStart endpoint
jumpstart_endpoint = HyperPodJumpstartEndpoint.load(endpoint_name="endpoint-jumpstart")
jumpstart_endpoint.delete()

# Delete custom endpoint
custom_endpoint = HyperPodCustomEndpoint.load(endpoint_name="endpoint-custom")
custom_endpoint.delete()
```

## Inference Example Notebooks

For detailed examples of inference with HyperPod, see:
- [CLI Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-fsx-model-e2e-cli.ipynb)
- [CLI Inference Jumpstart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-e2e-cli.ipynb)
- [CLI Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-e2e-cli.ipynb)
- [SDK Inference FSX Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-fsx-model-e2e.ipynb)
- [SDK Inference Jumpstart Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-jumpstart-e2e.ipynb)
- [SDK Inference S3 Model Example](https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-s3-model-e2e.ipynb)
