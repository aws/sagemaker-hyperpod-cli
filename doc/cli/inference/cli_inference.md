(cli_inference)=

# Inference

Complete reference for SageMaker HyperPod inference parameters and configuration options.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

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



## hyp create hyp-jumpstart-endpoint

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
