(cli_space)=

# Space

Complete reference for Amazon SageMaker Space management commands and configuration options.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

* [Create Space](#hyp-create-hyp-space)
* [List Spaces](#hyp-list-hyp-space)
* [Describe Space](#hyp-describe-hyp-space)
* [Update Space](#hyp-update-hyp-space)
* [Delete Space](#hyp-delete-hyp-space)
* [Start Space](#hyp-start-hyp-space)
* [Stop Space](#hyp-stop-hyp-space)
* [Get Logs](#hyp-get-logs-hyp-space)
* [Create Space Access](#hyp-create-hyp-space-access)
* [Create Space Template](#hyp-create-hyp-space-template)
* [List Space Templates](#hyp-list-hyp-space-template)
* [Describe Space Template](#hyp-describe-hyp-space-template)
* [Update Space Template](#hyp-update-hyp-space-template)
* [Delete Space Template](#hyp-delete-hyp-space-template)

## hyp create hyp-space

Create a space resource on SageMaker HyperPod clusters.

### Syntax

```bash
hyp create hyp-space [OPTIONS]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--version` | TEXT | No | Schema version to use |
| `--name` | TEXT | Yes | Space name |
| `--display-name` | TEXT | Yes | Display Name of the space |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--image` | TEXT | No | Image specifies the container image to use |
| `--desired-status` | TEXT | No | DesiredStatus specifies the desired operational status |
| `--ownership-type` | TEXT | No | OwnershipType specifies who can modify the space ('Public' or 'OwnerOnly') |
| `--node-selector` | TEXT | No | NodeSelector specifies node selection constraints for the space pod (JSON string) |
| `--affinity` | TEXT | No | Affinity specifies node affinity and anti-affinity rules for the space pod (JSON string) |
| `--tolerations` | TEXT | No | Tolerations specifies tolerations for the space pod to schedule on nodes with matching taints (JSON string) |
| `--lifecycle` | TEXT | No | Lifecycle specifies actions that the management system should take in response to container lifecycle events (JSON string) |
| `--app-type` | TEXT | No | AppType specifies the application type for this workspace |
| `--service-account-name` | TEXT | No | ServiceAccountName specifies the name of the ServiceAccount to use for the workspace pod |
| `--idle-shutdown` | TEXT | No | Idle shutdown configuration. Format: enabled=<bool>,idleTimeoutInMinutes=<int>,detection=<JSON string> |
| `--template-ref` | TEXT | No | TemplateRef references a WorkspaceTemplate to use as base configuration. Format: name=<name>,namespace=<namespace> |
| `--container-config` | TEXT | No | Container configuration. Format: command=<cmd>,args=<arg1;arg2> |
| `--storage` | TEXT | No | Storage configuration. Format: storageClassName=<class>,size=<size>,mountPath=<path> |
| `--volume` | TEXT | No | Volume configuration. Format: name=<name>,mountPath=<path>,persistentVolumeClaimName=<pvc_name>. Use multiple --volume flags for multiple volumes |
| `--accelerator-partition-count` | TEXT | No | Fractional GPU partition count, e.g. '1' |
| `--accelerator-partition-type` | TEXT | No | Fractional GPU partition type, e.g. 'mig-3g.20gb' |
| `--gpu-limit` | TEXT | No | GPU resource limit, e.g. '1' |
| `--gpu` | TEXT | No | GPU resource request, e.g. '1' |
| `--memory-limit` | TEXT | No | Memory resource limit, e.g. '2Gi' |
| `--memory` | TEXT | No | Memory resource request, e.g. '2Gi' |
| `--cpu-limit` | TEXT | No | CPU resource limit, e.g. '500m' |
| `--cpu` | TEXT | No | CPU resource request, e.g. '500m' |

### Example

```bash
hyp create hyp-space --version 1.0 --name my-space --namespace default
```

## Space Management Commands

Commands for managing Amazon SageMaker Spaces.

### hyp list hyp-space

List all spaces in a namespace.

#### Syntax

```bash
hyp list hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |
| `--output, -o` | TEXT | No | Output format: table or json (default: "table") |

#### Example

```bash
hyp list hyp-space --namespace default --output table
```

### hyp describe hyp-space

Describe a specific space resource.

#### Syntax

```bash
hyp describe hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to describe |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |
| `--output, -o` | TEXT | No | Output format: yaml or json (default: "yaml") |

#### Example

```bash
hyp describe hyp-space --name my-space --namespace default --output yaml
```

### hyp update hyp-space

Update an existing space resource.

#### Syntax

```bash
hyp update hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--version` | TEXT | No | Schema version to use |
| `--name` | TEXT | Yes | Space name |
| `--display-name` | TEXT | No | Display Name of the space |
| `--namespace` | TEXT | No | Kubernetes namespace |
| `--image` | TEXT | No | Image specifies the container image to use |
| `--desired-status` | TEXT | No | DesiredStatus specifies the desired operational status |
| `--ownership-type` | TEXT | No | OwnershipType specifies who can modify the space ('Public' or 'OwnerOnly') |
| `--node-selector` | TEXT | No | NodeSelector specifies node selection constraints for the space pod (JSON string) |
| `--affinity` | TEXT | No | Affinity specifies node affinity and anti-affinity rules for the space pod (JSON string) |
| `--tolerations` | TEXT | No | Tolerations specifies tolerations for the space pod to schedule on nodes with matching taints (JSON string) |
| `--lifecycle` | TEXT | No | Lifecycle specifies actions that the management system should take in response to container lifecycle events (JSON string) |
| `--app-type` | TEXT | No | AppType specifies the application type for this workspace |
| `--service-account-name` | TEXT | No | ServiceAccountName specifies the name of the ServiceAccount to use for the workspace pod |
| `--idle-shutdown` | TEXT | No | Idle shutdown configuration. Format: enabled=<bool>,idleTimeoutInMinutes=<int>,detection=<JSON string> |
| `--template-ref` | TEXT | No | TemplateRef references a WorkspaceTemplate to use as base configuration. Format: name=<name>,namespace=<namespace> |
| `--container-config` | TEXT | No | Container configuration. Format: command=<cmd>,args=<arg1;arg2> |
| `--volume` | TEXT | No | Volume configuration. Format: name=<name>,mountPath=<path>,persistentVolumeClaimName=<pvc_name>. Use multiple --volume flags for multiple volumes |
| `--accelerator-partition-count` | TEXT | No | Fractional GPU partition count, e.g. '1' |
| `--accelerator-partition-type` | TEXT | No | Fractional GPU partition type, e.g. 'mig-3g.20gb' |
| `--gpu-limit` | TEXT | No | GPU resource limit, e.g. '1' |
| `--gpu` | TEXT | No | GPU resource request, e.g. '1' |
| `--memory-limit` | TEXT | No | Memory resource limit, e.g. '2Gi' |
| `--memory` | TEXT | No | Memory resource request, e.g. '2Gi' |
| `--cpu-limit` | TEXT | No | CPU resource limit, e.g. '500m' |
| `--cpu` | TEXT | No | CPU resource request, e.g. '500m' |

#### Example

```bash
hyp update hyp-space --version 1.0 --name my-space --namespace default
```

### hyp delete hyp-space

Delete a space resource.

#### Syntax

```bash
hyp delete hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to delete |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |

#### Example

```bash
hyp delete hyp-space --name my-space --namespace default
```

### hyp start hyp-space

Start a space resource.

#### Syntax

```bash
hyp start hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to start |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |

#### Example

```bash
hyp start hyp-space --name my-space --namespace default
```

### hyp stop hyp-space

Stop a space resource.

#### Syntax

```bash
hyp stop hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to stop |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |

#### Example

```bash
hyp stop hyp-space --name my-space --namespace default
```

### hyp get-logs hyp-space

Get logs from a space resource.

#### Syntax

```bash
hyp get-logs hyp-space [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to get logs from |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |
| `--pod-name` | TEXT | No | Name of the specific pod to get logs from |
| `--container` | TEXT | No | Name of the specific container to get logs from |

#### Example

```bash
hyp get-logs hyp-space --name my-space --namespace default --pod-name my-pod
```

## Space Access Commands

Commands for managing space access resources.

### hyp create hyp-space-access

Create a space access resource for remote connection to a space.

#### Syntax

```bash
hyp create hyp-space-access [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space to create access for |
| `--namespace, -n` | TEXT | No | Kubernetes namespace (default: "default") |
| `--connection-type, -t` | TEXT | No | Remote access type: vscode-remote or web-ui (default: "vscode-remote") |

#### Example

```bash
hyp create hyp-space-access --name my-space --namespace default --connection-type vscode-remote
```

## Space Template Commands

Commands for managing space template resources.

### hyp create hyp-space-template

Create a space template resource from a YAML configuration file.

#### Syntax

```bash
hyp create hyp-space-template [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--file, -f` | TEXT | Yes | YAML file containing the template configuration |

#### Example

```bash
hyp create hyp-space-template --file my-template.yaml
```

### hyp list hyp-space-template

List all space template resources.

#### Syntax

```bash
hyp list hyp-space-template [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--namespace, -n` | TEXT | No | Kubernetes namespace |
| `--output, -o` | TEXT | No | Output format: table or json (default: "table") |

#### Example

```bash
hyp list hyp-space-template --namespace default --output table
```

### hyp describe hyp-space-template

Describe a specific space template resource.

#### Syntax

```bash
hyp describe hyp-space-template [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space template to describe |
| `--namespace, -n` | TEXT | No | Kubernetes namespace |
| `--output, -o` | TEXT | No | Output format: yaml or json (default: "yaml") |

#### Example

```bash
hyp describe hyp-space-template --name my-template --namespace default --output yaml
```

### hyp update hyp-space-template

Update an existing space template resource.

#### Syntax

```bash
hyp update hyp-space-template [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space template to update |
| `--namespace, -n` | TEXT | No | Kubernetes namespace |
| `--file, -f` | TEXT | Yes | YAML file containing the updated template configuration |

#### Example

```bash
hyp update hyp-space-template --name my-template --namespace default --file updated-template.yaml
```

### hyp delete hyp-space-template

Delete a space template resource.

#### Syntax

```bash
hyp delete hyp-space-template [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--name` | TEXT | Yes | Name of the space template to delete |
| `--namespace, -n` | TEXT | No | Kubernetes namespace |

#### Example

```bash
hyp delete hyp-space-template --name my-template --namespace default
```
