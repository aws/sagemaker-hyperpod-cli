(cli_inference)=

# Inference

Complete reference for SageMaker HyperPod inference parameters and configuration options.

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

#### Required Parameters

- `--model-id TEXT`: JumpStart model identifier (1-63 characters, alphanumeric with hyphens)
- `--instance-type TEXT`: EC2 instance type for inference (must start with "ml.")

#### Optional Parameters

- `--accept-eula BOOLEAN`: Whether model terms of use have been accepted (default: false)
- `--model-version TEXT`: Semantic version of the model (e.g., "1.0.0", 5-14 characters)
- `--endpoint-name TEXT`: Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens)
- `--tls-certificate-output-s3-uri TEXT`: S3 URI to write the TLS certificate (optional)

### hyp create hyp-custom-endpoint

Deploy custom models with your own inference code.

#### Syntax

```bash
hyp create hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--instance-type TEXT`: EC2 instance type for inference (must start with "ml.")
- `--model-name TEXT`: Name of model to create on SageMaker (1-63 characters, alphanumeric with hyphens)
- `--model-source-type TEXT`: Model source type ("s3" or "fsx")
- `--image-uri TEXT`: Docker image URI for inference
- `--container-port INTEGER`: Port on which model server listens (1-65535)
- `--model-volume-mount-name TEXT`: Name of the model volume mount

#### Optional Parameters

- `--endpoint-name TEXT`: Name of SageMaker endpoint (1-63 characters, alphanumeric with hyphens)
- `--env OBJECT`: Environment variables as key-value pairs
- `--metrics-enabled BOOLEAN`: Enable metrics collection (default: false)
- `--model-version TEXT`: Version of the model (semantic version format)
- `--model-location TEXT`: Specific model data location
- `--prefetch-enabled BOOLEAN`: Whether to pre-fetch model data (default: false)
- `--tls-certificate-output-s3-uri TEXT`: S3 URI for TLS certificate output
- `--fsx-dns-name TEXT`: FSx File System DNS Name
- `--fsx-file-system-id TEXT`: FSx File System ID
- `--fsx-mount-name TEXT`: FSx File System Mount Name
- `--s3-bucket-name TEXT`: S3 bucket location
- `--s3-region TEXT`: S3 bucket region
- `--model-volume-mount-path TEXT`: Path inside container for model volume (default: "/opt/ml/model")
- `--resources-limits OBJECT`: Resource limits for the worker
- `--resources-requests OBJECT`: Resource requests for the worker
- `--dimensions OBJECT`: CloudWatch Metric dimensions as key-value pairs
- `--metric-collection-period INTEGER`: Period for CloudWatch query (default: 300)
- `--metric-collection-start-time INTEGER`: StartTime for CloudWatch query (default: 300)
- `--metric-name TEXT`: Metric name to query for CloudWatch trigger
- `--metric-stat TEXT`: Statistics metric for CloudWatch (default: "Average")
- `--metric-type TEXT`: Type of metric for HPA ("Value" or "Average", default: "Average")
- `--min-value NUMBER`: Minimum metric value for empty CloudWatch response (default: 0)
- `--cloud-watch-trigger-name TEXT`: Name for the CloudWatch trigger
- `--cloud-watch-trigger-namespace TEXT`: AWS CloudWatch namespace for the metric
- `--target-value NUMBER`: Target value for the CloudWatch metric
- `--use-cached-metrics BOOLEAN`: Enable caching of metric values (default: true)
- `--invocation-endpoint TEXT`: Invocation endpoint path (default: "invocations")

## Inference Endpoint Management Commands

Commands for managing inference endpoints.

### hyp list hyp-jumpstart-endpoint

List JumpStart model endpoints.

#### Syntax

```bash
hyp list hyp-jumpstart-endpoint [OPTIONS]
```

#### Optional Parameters

- `--namespace TEXT`: Namespace to list endpoints from (default: "default")

### hyp list hyp-custom-endpoint

List custom model endpoints.

#### Syntax

```bash
hyp list hyp-custom-endpoint [OPTIONS]
```

#### Optional Parameters

- `--namespace TEXT`: Namespace to list endpoints from (default: "default")

### hyp describe hyp-jumpstart-endpoint

Describe a JumpStart model endpoint.

#### Syntax

```bash
hyp describe hyp-jumpstart-endpoint [OPTIONS]
```

#### Required Parameters

- `--name TEXT`: Name of the endpoint to describe

#### Optional Parameters

- `--namespace TEXT`: Namespace of the endpoint (default: "default")
- `--full`: Display full JSON output

### hyp describe hyp-custom-endpoint

Describe a custom model endpoint.

#### Syntax

```bash
hyp describe hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--name TEXT`: Name of the endpoint to describe

#### Optional Parameters

- `--namespace TEXT`: Namespace of the endpoint (default: "default")
- `--full`: Display full JSON output

### hyp invoke hyp-jumpstart-endpoint

Invoke a JumpStart model endpoint.

#### Syntax

```bash
hyp invoke hyp-jumpstart-endpoint [OPTIONS]
```

#### Required Parameters

- `--endpoint-name TEXT`: Name of the endpoint to invoke
- `--body TEXT`: Request body (JSON format)

#### Optional Parameters

- `--content-type TEXT`: Content type of the request (default: "application/json")

### hyp invoke hyp-custom-endpoint

Invoke a custom model endpoint.

#### Syntax

```bash
hyp invoke hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--endpoint-name TEXT`: Name of the endpoint to invoke
- `--body TEXT`: Request body (JSON format)

#### Optional Parameters

- `--content-type TEXT`: Content type of the request (default: "application/json")

### hyp delete hyp-jumpstart-endpoint

Delete a JumpStart model endpoint.

#### Syntax

```bash
hyp delete hyp-jumpstart-endpoint [OPTIONS]
```

#### Required Parameters

- `--name TEXT`: Name of the endpoint to delete

#### Optional Parameters

- `--namespace TEXT`: Namespace of the endpoint (default: "default")

### hyp delete hyp-custom-endpoint

Delete a custom model endpoint.

#### Syntax

```bash
hyp delete hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--name TEXT`: Name of the endpoint to delete

#### Optional Parameters

- `--namespace TEXT`: Namespace of the endpoint (default: "default")

### hyp list-pods hyp-jumpstart-endpoint

List pods for JumpStart endpoints.

#### Syntax

```bash
hyp list-pods hyp-jumpstart-endpoint [OPTIONS]
```

#### Optional Parameters

- `--namespace TEXT`: Namespace to list pods from (default: "default")

### hyp list-pods hyp-custom-endpoint

List pods for custom endpoints.

#### Syntax

```bash
hyp list-pods hyp-custom-endpoint [OPTIONS]
```

#### Optional Parameters

- `--namespace TEXT`: Namespace to list pods from (default: "default")

### hyp get-logs hyp-jumpstart-endpoint

Get logs from JumpStart endpoint pods.

#### Syntax

```bash
hyp get-logs hyp-jumpstart-endpoint [OPTIONS]
```

#### Required Parameters

- `--pod-name TEXT`: Name of the pod to get logs from

#### Optional Parameters

- `--container TEXT`: Container name to get logs from
- `--namespace TEXT`: Namespace of the pod (default: "default")

### hyp get-logs hyp-custom-endpoint

Get logs from custom endpoint pods.

#### Syntax

```bash
hyp get-logs hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--pod-name TEXT`: Name of the pod to get logs from

#### Optional Parameters

- `--container TEXT`: Container name to get logs from
- `--namespace TEXT`: Namespace of the pod (default: "default")

### hyp get-operator-logs hyp-jumpstart-endpoint

Get operator logs for JumpStart endpoints.

#### Syntax

```bash
hyp get-operator-logs hyp-jumpstart-endpoint [OPTIONS]
```

#### Required Parameters

- `--since-hours FLOAT`: Time frame to get logs for (in hours)

### hyp get-operator-logs hyp-custom-endpoint

Get operator logs for custom endpoints.

#### Syntax

```bash
hyp get-operator-logs hyp-custom-endpoint [OPTIONS]
```

#### Required Parameters

- `--since-hours FLOAT`: Time frame to get logs for (in hours)

## Parameter Reference

### Common Parameters Across Commands

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--namespace` | TEXT | Kubernetes namespace | Current context |
| `--help` | FLAG | Show command help | - |
