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


## Creating Inference Endpoints -- CLI Init Experience

The following is a step-by-step guide of creating a jumpstart endpoint with `hyp-jumpstart-endpoint` template for init experience. In order to create a custom endpoint, you can use `hyp-custom-endpoint` template during the init command call. The init experience is the same across templates.

### 1. Start with a Clean Directory

It\'s recommended to start with a new and clean directory for each
endpoint configuration:

``` bash
mkdir my-endpoint
cd my-endpoint
```

### 2. Initialize a New Endpoint Configuration


`````{tab-set}
````{tab-item} CLI
``` bash
hyp init hyp-jumpstart-endpoint
```
````
`````

```{note}
In order to create custom endpoint, you can simply use `hyp init hyp-custom-endpoint`.
```

This creates three files:

- `config.yaml`: The main configuration file you\'ll use to customize
  your endpoint
- `k8s.jinja`: A reference template for parameters mapping in kubernetes payload
- `README.md`: Usage guide with instructions and examples



### 3. Configure Your Endpoint

You can configure your endpoint in two ways:

**Option 1: Edit config.yaml directly**

The config.yaml file contains key parameters like:

``` yaml
template: hyp-jumpstart-endpoint
version: 1.0
model_id:
instance_type: 
endpoint_name:
```

**Option 2: Use CLI command (Pre-Deployment)**

`````{tab-set}
````{tab-item} CLI
``` bash
hyp configure --endpoint-name your-endpoint-name
```
````
`````

```{note}
The `hyp configure` command only modifies local configuration files. It
does not affect existing deployed endpoints.
```

### 4. Create the Endpoint

`````{tab-set}
````{tab-item} CLI
``` bash
hyp create
```
````
`````

This will:

- Validate your configuration
- Create a timestamped folder in the `run` directory
- Initialize the endpoint creation process



## Creating Inference Endpoints -- CLI/SDK

You can create inference endpoints using either JumpStart models or custom models:

### JumpStart Model Endpoints

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-jumpstart-endpoint \
  --model-id jumpstart-model-id \
  --instance-type ml.g5.8xlarge \
  --endpoint-name endpoint-jumpstart
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import Model, Server, SageMakerEndpoint, TlsConfig
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

model = Model(
    model_id="deepseek-llm-r1-distill-qwen-1-5b"
)

server = Server(
    instance_type="ml.g5.8xlarge"
)

endpoint_name = SageMakerEndpoint(name="endpoint-jumpstart")

js_endpoint = HPJumpStartEndpoint(
    model=model,
    server=server,
    sage_maker_endpoint=endpoint_name
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
  --endpoint-name endpoint-s3 \
  --model-name <model-name> \
  --model-source-type s3 \
  --instance-type <instance-type> \
  --image-uri <image-uri> \
  --container-port 8080 \
  --model-volume-mount-name model-weights
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.config.hp_endpoint_config import CloudWatchTrigger, Dimensions, AutoScalingSpec, Metrics, S3Storage, ModelSourceConfig, TlsConfig, EnvironmentVariables, ModelInvocationPort, ModelVolumeMount, Resources, Worker
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

model_source_config = ModelSourceConfig(
    model_source_type='s3',
    model_location="<my-model-folder-in-s3>",
    s3_storage=S3Storage(
        bucket_name='<my-model-artifacts-bucket>',
        region='us-east-2',
    ),
)

environment_variables = [
    EnvironmentVariables(name="HF_MODEL_ID", value="/opt/ml/model"),
    EnvironmentVariables(name="SAGEMAKER_PROGRAM", value="inference.py"),
    EnvironmentVariables(name="SAGEMAKER_SUBMIT_DIRECTORY", value="/opt/ml/model/code"),
    EnvironmentVariables(name="MODEL_CACHE_ROOT", value="/opt/ml/model"),
    EnvironmentVariables(name="SAGEMAKER_ENV", value="1"),
]

worker = Worker(
    image='763104351884.dkr.ecr.us-east-2.amazonaws.com/huggingface-pytorch-tgi-inference:2.4.0-tgi2.3.1-gpu-py311-cu124-ubuntu22.04-v2.0',
    model_volume_mount=ModelVolumeMount(
        name='model-weights',
    ),
    model_invocation_port=ModelInvocationPort(container_port=8080),
    resources=Resources(
            requests={"cpu": "30000m", "nvidia.com/gpu": 1, "memory": "100Gi"},
            limits={"nvidia.com/gpu": 1}
    ),
    environment_variables=environment_variables,
)

tls_config=TlsConfig(tls_certificate_output_s3_uri='s3://<my-tls-bucket-name>')

custom_endpoint = HPEndpoint(
    endpoint_name='<my-endpoint-name>',
    instance_type='ml.g5.8xlarge',
    model_name='deepseek15b-test-model-name',  
    tls_config=tls_config,
    model_source_config=model_source_config,
    worker=worker,
)

custom_endpoint.create()
```
````
`````

### Key Parameters

When creating an inference endpoint, you'll need to specify:

1. **Parameters required for Jumpstart Endpoint**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| **endpoint-name** | TEXT | Yes | Unique identifier for your endpoint |
| **instance-type** | TEXT | Yes | The EC2 instance type to use |
| **model-id** | TEXT | Yes | ID of the pre-trained JumpStart model |

2. **Parameters required for Custom Endpoint**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| **endpoint-name** | TEXT | Yes | Unique identifier for your endpoint |
| **instance-type** | TEXT | Yes | The EC2 instance type to use |
| **image-uri** | TEXT | Yes | Docker image containing your inference code |
| **model-name** | TEXT | Yes | Name of model to create on SageMaker |
| **model-source-type** | TEXT | Yes | Source type: fsx or s3 |
| **model-volume-mount-name** | TEXT | Yes | Name of the model volume mount |
| **container-port** | INTEGER | Yes | Port on which the model server listens |

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
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# List JumpStart endpoints
jumpstart_endpoints = HPJumpStartEndpoint.list()
print(jumpstart_endpoints)

# List custom endpoints
custom_endpoints = HPEndpoint.list()
print(custom_endpoints)
```
````
`````

### Describe an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Describe JumpStart endpoint
hyp describe hyp-jumpstart-endpoint --name <endpoint-name>

# Describe custom endpoint
hyp describe hyp-custom-endpoint --name <endpoint-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Get JumpStart endpoint details
jumpstart_endpoint = HPJumpStartEndpoint.get(name="js-endpoint-name", namespace="test")
print(jumpstart_endpoint)

# Get custom endpoint details
custom_endpoint = HPEndpoint.get(name="endpoint-custom")
print(custom_endpoint)

```
````
`````

### Invoke an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Invoke Jumpstart endpoint
hyp invoke hyp-jumpstart-endpoint \
    --endpoint-name <endpoint-name> \
    --body '{"inputs":"What is the capital of USA?"}'

# Invoke custom endpoint
hyp invoke hyp-custom-endpoint \
    --endpoint-name <endpoint-name> \
    --body '{"inputs": "What is machine learning?"}'
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

data = '{"inputs":"What is the capital of USA?"}'
jumpstart_endpoint = HPJumpStartEndpoint.get(name="endpoint-jumpstart")
response = jumpstart_endpoint.invoke(body=data).body.read()
print(response)

custom_endpoint = HPEndpoint.get(name="endpoint-custom")
response = custom_endpoint.invoke(body=data).body.read()
print(response)
```
````
`````

### List Pods

`````{tab-set}
````{tab-item} CLI
```bash
# JumpStart endpoint
hyp list-pods hyp-jumpstart-endpoint

# Custom endpoint
hyp list-pods hyp-custom-endpoint
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# List pods 
js_pods = HPJumpStartEndpoint.list_pods()
print(js_pods)

c_pods = HPEndpoint.list_pods()
print(c_pods)
```
````
`````

### Get Logs

`````{tab-set}
````{tab-item} CLI
```bash
# JumpStart endpoint
hyp get-logs hyp-jumpstart-endpoint --pod-name <pod-name>

# Custom endpoint
hyp get-logs hyp-custom-endpoint --pod-name <pod-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Get logs from pod 
js_logs = HPJumpStartEndpoint.get_logs(pod=<pod-name>)
print(js_logs)

c_logs = HPEndpoint.get_logs(pod=<pod-name>)
print(c_logs)
```
````
`````

### Get Operator Logs

`````{tab-set}
````{tab-item} CLI
```bash
# JumpStart endpoint
hyp get-operator-logs hyp-jumpstart-endpoint --since-hours 0.5

# Custom endpoint
hyp get-operator-logs hyp-custom-endpoint --since-hours 0.5
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Invoke JumpStart endpoint
print(HPJumpStartEndpoint.get_operator_logs(since_hours=0.1))

# Invoke custom endpoint
print(HPEndpoint.get_operator_logs(since_hours=0.1))
```
````
`````

### Delete an Endpoint

`````{tab-set}
````{tab-item} CLI
```bash
# Delete JumpStart endpoint
hyp delete hyp-jumpstart-endpoint --name <endpoint-name>

# Delete custom endpoint
hyp delete hyp-custom-endpoint --name <endpoint-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

# Delete JumpStart endpoint
jumpstart_endpoint = HPJumpStartEndpoint.get(name="endpoint-jumpstart")
jumpstart_endpoint.delete()

# Delete custom endpoint
custom_endpoint = HPEndpoint.get(name="endpoint-custom")
custom_endpoint.delete()
```
````
`````

## Inference Example Notebooks

For detailed examples of inference with HyperPod, explore these interactive Jupyter notebooks:

CLI Examples:
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-init-experience.ipynb" target="_blank">CLI Inference JumpStart Model Init Experience Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-jumpstart-e2e-cli.ipynb" target="_blank">CLI Inference JumpStart Model Example</a>

- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-init-experience.ipynb" target="_blank">CLI Inference S3 Model Init Experience Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-s3-model-e2e-cli.ipynb" target="_blank">CLI Inference S3 Model Example</a>

- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/CLI/inference-fsx-model-e2e-cli.ipynb" target="_blank">CLI Inference FSX Model Example</a>

SDK Examples:
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-fsx-model-e2e.ipynb" target="_blank">SDK Inference FSX Model Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-jumpstart-e2e.ipynb" target="_blank">SDK Inference JumpStart Model Example</a>
- <a href="https://github.com/aws/sagemaker-hyperpod-cli/blob/main/examples/inference/SDK/inference-s3-model-e2e.ipynb" target="_blank">SDK Inference S3 Model Example</a>

These Jupyter notebooks demonstrate comprehensive workflows for deploying and managing inference endpoints using different model storage options and both CLI and SDK approaches. You can run these notebooks directly
in your local environment or SageMaker Studio.
