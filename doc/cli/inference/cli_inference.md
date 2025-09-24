(cli_inference)=

# Inference

Complete reference for SageMaker HyperPod inference parameters and configuration options.

* [Initialize Configuration](#hyp-init)
* [Configure Parameters](#hyp-configure)
* [Validate Configuration](#hyp-validate)
* [Reset Configuration](#hyp-reset)
* [Create with Configuration](#hyp-create)
* [Create JumpStart Endpoint](#hyp-create-hyp-jumpstart-endpoint)
* [Create Custom Endpoint](#hyp-create-hyp-custom-endpoint)

* [List JumpStart Endpoints](#hyp-list-hyp-jumpstart-endpoint)
* [List Custom Endpoints](#hyp-list-hyp-custom-endpoint)
* [Describe JumpStart Endpoint](#hyp-describe-hyp-jumpstart-endpoint)
* [Describe Custom Endpoint](#hyp-describe-hyp-custom-endpoint)
* [Invoke JumpStart Endpoint](#hyp-invoke-hyp-jumpstart-endpoint)
* [Invoke Custom Endpoint](#hyp-invoke-hyp-custom-endpoint)
* [Delete JumpStart Endpoint](#hyp-delete-hyp-jumpstart-endpoint)
* [Delete Custom Endpoint](#hyp-delete-hyp-custom-endpoint)

* [List JumpStart Pods](#hyp-list-pods-hyp-jumpstart-endpoint)
* [List Custom Pods](#hyp-list-pods-hyp-custom-endpoint)
* [Get JumpStart Logs](#hyp-get-logs-hyp-jumpstart-endpoint)
* [Get Custom Logs](#hyp-get-logs-hyp-custom-endpoint)
* [Get JumpStart Operator Logs](#hyp-get-operator-logs-hyp-jumpstart-endpoint)
* [Get Custom Operator Logs](#hyp-get-operator-logs-hyp-custom-endpoint)


## Create Inference Endpoint -- Init Experience
### hyp init

Initialize a template scaffold in the current directory.

#### Syntax

```bash
hyp init TEMPLATE [DIRECTORY] [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `TEMPLATE` | CHOICE | Yes | Template type (cluster-stack, hyp-pytorch-job, hyp-custom-endpoint, hyp-jumpstart-endpoint) |
| `DIRECTORY` | PATH | No | Target directory (default: current directory) |
| `--version` | TEXT | No | Schema version to use |


### hyp configure

Configure training job parameters interactively or via command line.

```{important}
**Pre-Deployment Configuration**: This command modifies local `config.yaml` files **before** job creation.
```

#### Syntax

```bash
hyp configure [OPTIONS]
```

**Note:** This command dynamically supports all configuration parameters available in the current template's schema. 


#### Parameters for Jumpstart Endpoint

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--model-id` | TEXT | Yes | JumpStart model identifier (1-63 characters, alphanumeric with hyphens) |
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--accept-eula` | BOOLEAN | No | Whether model terms of use have been accepted (default: false) |
| `--model-version` | TEXT | No | Semantic version of the model (e.g., "1.0.0", 5-14 characters) |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI to write the TLS certificate (optional) |

#### Parameters for Custom Endpoint

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--model-name` | TEXT | Yes | Name of model to create on SageMaker (1-63 characters, alphanumeric with hyphens) |
| `--model-source-type` | TEXT | Yes | Model source type ("s3" or "fsx") |
| `--image-uri` | TEXT | Yes | Docker image URI for inference |
| `--container-port` | INTEGER | Yes | Port on which model server listens (1-65535) |
| `--model-volume-mount-name` | TEXT | Yes | Name of the model volume mount |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--env` | OBJECT | No | Environment variables as key-value pairs |
| `--metrics-enabled` | BOOLEAN | No | Enable metrics collection (default: false) |
| `--model-version` | TEXT | No | Version of the model (semantic version format) |
| `--model-location` | TEXT | No | Specific model data location |
| `--prefetch-enabled` | BOOLEAN | No | Whether to pre-fetch model data (default: false) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI for TLS certificate output |
| `--fsx-dns-name` | TEXT | No | FSx File System DNS Name |
| `--fsx-file-system-id` | TEXT | No | FSx File System ID |
| `--fsx-mount-name` | TEXT | No | FSx File System Mount Name |
| `--s3-bucket-name` | TEXT | No | S3 bucket location |
| `--s3-region` | TEXT | No | S3 bucket region |
| `--model-volume-mount-path` | TEXT | No | Path inside container for model volume (default: "/opt/ml/model") |
| `--resources-limits` | OBJECT | No | Resource limits for the worker |
| `--resources-requests` | OBJECT | No | Resource requests for the worker |
| `--dimensions` | OBJECT | No | CloudWatch Metric dimensions as key-value pairs |
| `--metric-collection-period` | INTEGER | No | Period for CloudWatch query (default: 300) |
| `--metric-collection-start-time` | INTEGER | No | StartTime for CloudWatch query (default: 300) |
| `--metric-name` | TEXT | No | Metric name to query for CloudWatch trigger |
| `--metric-stat` | TEXT | No | Statistics metric for CloudWatch (default: "Average") |
| `--metric-type` | TEXT | No | Type of metric for HPA ("Value" or "Average", default: "Average") |
| `--min-value` | NUMBER | No | Minimum metric value for empty CloudWatch response (default: 0) |
| `--cloud-watch-trigger-name` | TEXT | No | Name for the CloudWatch trigger |
| `--cloud-watch-trigger-namespace` | TEXT | No | AWS CloudWatch namespace for the metric |
| `--target-value` | NUMBER | No | Target value for the CloudWatch metric |
| `--use-cached-metrics` | BOOLEAN | No | Enable caching of metric values (default: true) |
| `--invocation-endpoint` | TEXT | No | Invocation endpoint path (default: "invocations") |



**Note:** The exact parameters available depend on your current template type and version. Run `hyp configure --help` to see all available options for your specific configuration.

### hyp validate

Validate the current directory's configuration file syntax and structure.

#### Syntax

```bash
# Validate current configuration syntax
hyp validate

# Example output on success
✔️ config.yaml is valid!

# Example output with syntax errors
❌ Config validation errors:
  – job_name: Field is required
```

#### Parameters

No parameters required.

```{note}
This command performs **syntactic validation only** of the `config.yaml` file against the appropriate schema. It checks:

- **YAML syntax**: Ensures file is valid YAML
- **Required fields**: Verifies all mandatory fields are present
- **Data types**: Confirms field values match expected types (string, number, boolean, array)
- **Schema structure**: Validates against the template's defined structure

This command performs syntactic validation only and does **not** verify the actual validity of values (e.g., whether AWS regions exist, instance types are available, or resources can be created).

**Prerequisites**

- Must be run in a directory where `hyp init` has created configuration files
- A `config.yaml` file must exist in the current directory

**Output**

- **Success**: Displays confirmation message if syntax is valid
- **Errors**: Lists specific syntax errors with field names and descriptions
```


### hyp reset

Reset the current directory's config.yaml to default values.

#### Syntax

```bash
hyp reset
```

#### Parameters

No parameters required.


### hyp create

Create a new HyperPod endpoint using the provided configuration.

#### Syntax

```bash
hyp create [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--debug` | FLAG | No | Enable debug logging |


## Create Training Job -- Direct Create
### hyp create hyp-jumpstart-endpoint

Deploy pre-trained models from SageMaker JumpStart.

#### Syntax

```bash
hyp create hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--model-id` | TEXT | Yes | JumpStart model identifier (1-63 characters, alphanumeric with hyphens) |
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--accept-eula` | BOOLEAN | No | Whether model terms of use have been accepted (default: false) |
| `--model-version` | TEXT | No | Semantic version of the model (e.g., "1.0.0", 5-14 characters) |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI to write the TLS certificate (optional) |

### hyp create hyp-custom-endpoint

Deploy custom models with your own inference code.

#### Syntax

```bash
hyp create hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--instance-type` | TEXT | Yes | EC2 instance type for inference (must start with "ml.") |
| `--model-name` | TEXT | Yes | Name of model to create on SageMaker (1-63 characters, alphanumeric with hyphens) |
| `--model-source-type` | TEXT | Yes | Model source type ("s3" or "fsx") |
| `--image-uri` | TEXT | Yes | Docker image URI for inference |
| `--container-port` | INTEGER | Yes | Port on which model server listens (1-65535) |
| `--model-volume-mount-name` | TEXT | Yes | Name of the model volume mount |
| `--endpoint-name` | TEXT | No | Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens) |
| `--env` | OBJECT | No | Environment variables as key-value pairs |
| `--metrics-enabled` | BOOLEAN | No | Enable metrics collection (default: false) |
| `--model-version` | TEXT | No | Version of the model (semantic version format) |
| `--model-location` | TEXT | No | Specific model data location |
| `--prefetch-enabled` | BOOLEAN | No | Whether to pre-fetch model data (default: false) |
| `--tls-certificate-output-s3-uri` | TEXT | No | S3 URI for TLS certificate output |
| `--fsx-dns-name` | TEXT | No | FSx File System DNS Name |
| `--fsx-file-system-id` | TEXT | No | FSx File System ID |
| `--fsx-mount-name` | TEXT | No | FSx File System Mount Name |
| `--s3-bucket-name` | TEXT | No | S3 bucket location |
| `--s3-region` | TEXT | No | S3 bucket region |
| `--model-volume-mount-path` | TEXT | No | Path inside container for model volume (default: "/opt/ml/model") |
| `--resources-limits` | OBJECT | No | Resource limits for the worker |
| `--resources-requests` | OBJECT | No | Resource requests for the worker |
| `--dimensions` | OBJECT | No | CloudWatch Metric dimensions as key-value pairs |
| `--metric-collection-period` | INTEGER | No | Period for CloudWatch query (default: 300) |
| `--metric-collection-start-time` | INTEGER | No | StartTime for CloudWatch query (default: 300) |
| `--metric-name` | TEXT | No | Metric name to query for CloudWatch trigger |
| `--metric-stat` | TEXT | No | Statistics metric for CloudWatch (default: "Average") |
| `--metric-type` | TEXT | No | Type of metric for HPA ("Value" or "Average", default: "Average") |
| `--min-value` | NUMBER | No | Minimum metric value for empty CloudWatch response (default: 0) |
| `--cloud-watch-trigger-name` | TEXT | No | Name for the CloudWatch trigger |
| `--cloud-watch-trigger-namespace` | TEXT | No | AWS CloudWatch namespace for the metric |
| `--target-value` | NUMBER | No | Target value for the CloudWatch metric |
| `--use-cached-metrics` | BOOLEAN | No | Enable caching of metric values (default: true) |
| `--invocation-endpoint` | TEXT | No | Invocation endpoint path (default: "invocations") |

## Inference Endpoint Management Commands

Commands for managing inference endpoints.

### hyp list hyp-jumpstart-endpoint

List JumpStart model endpoints.

#### Syntax

```bash
hyp list hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace` | TEXT | No | Namespace to list endpoints from (default: "default") |

### hyp list hyp-custom-endpoint

List custom model endpoints.

#### Syntax

```bash
hyp list hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace` | TEXT | No | Namespace to list endpoints from (default: "default") |

### hyp describe hyp-jumpstart-endpoint

Describe a JumpStart model endpoint.

#### Syntax

```bash
hyp describe hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the endpoint to describe |
| `--namespace` | TEXT | No | Namespace of the endpoint (default: "default") |
| `--full` | FLAG | No | Display full JSON output |

### hyp describe hyp-custom-endpoint

Describe a custom model endpoint.

#### Syntax

```bash
hyp describe hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the endpoint to describe |
| `--namespace` | TEXT | No | Namespace of the endpoint (default: "default") |
| `--full` | FLAG | No | Display full JSON output |

### hyp invoke hyp-jumpstart-endpoint

Invoke a JumpStart model endpoint.

#### Syntax

```bash
hyp invoke hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--endpoint-name` | TEXT | Yes | Name of the endpoint to invoke |
| `--body` | TEXT | Yes | Request body (JSON format) |
| `--content-type` | TEXT | No | Content type of the request (default: "application/json") |

### hyp invoke hyp-custom-endpoint

Invoke a custom model endpoint.

#### Syntax

```bash
hyp invoke hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--endpoint-name` | TEXT | Yes | Name of the endpoint to invoke |
| `--body` | TEXT | Yes | Request body (JSON format) |
| `--content-type` | TEXT | No | Content type of the request (default: "application/json") |

### hyp delete hyp-jumpstart-endpoint

Delete a JumpStart model endpoint.

#### Syntax

```bash
hyp delete hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the endpoint to delete |
| `--namespace` | TEXT | No | Namespace of the endpoint (default: "default") |

### hyp delete hyp-custom-endpoint

Delete a custom model endpoint.

#### Syntax

```bash
hyp delete hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the endpoint to delete |
| `--namespace` | TEXT | No | Namespace of the endpoint (default: "default") |

### hyp list-pods hyp-jumpstart-endpoint

List pods for JumpStart endpoints.

#### Syntax

```bash
hyp list-pods hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace` | TEXT | No | Namespace to list pods from (default: "default") |

### hyp list-pods hyp-custom-endpoint

List pods for custom endpoints.

#### Syntax

```bash
hyp list-pods hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace` | TEXT | No | Namespace to list pods from (default: "default") |

### hyp get-logs hyp-jumpstart-endpoint

Get logs from JumpStart endpoint pods.

#### Syntax

```bash
hyp get-logs hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--pod-name` | TEXT | Yes | Name of the pod to get logs from |
| `--container` | TEXT | No | Container name to get logs from |
| `--namespace` | TEXT | No | Namespace of the pod (default: "default") |

### hyp get-logs hyp-custom-endpoint

Get logs from custom endpoint pods.

#### Syntax

```bash
hyp get-logs hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--pod-name` | TEXT | Yes | Name of the pod to get logs from |
| `--container` | TEXT | No | Container name to get logs from |
| `--namespace` | TEXT | No | Namespace of the pod (default: "default") |

### hyp get-operator-logs hyp-jumpstart-endpoint

Get operator logs for JumpStart endpoints.

#### Syntax

```bash
hyp get-operator-logs hyp-jumpstart-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--since-hours` | FLOAT | Yes | Time frame to get logs for (in hours) |

### hyp get-operator-logs hyp-custom-endpoint

Get operator logs for custom endpoints.

#### Syntax

```bash
hyp get-operator-logs hyp-custom-endpoint [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--since-hours` | FLOAT | Yes | Time frame to get logs for (in hours) |

## Parameter Reference

### Common Parameters Across Commands

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--namespace` | TEXT | Kubernetes namespace | Current context |
| `--help` | FLAG | Show command help | - |
