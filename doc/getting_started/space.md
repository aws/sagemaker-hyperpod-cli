---
keywords:
  - workspace
  - kubernetes
  - interactive
  - development
  - jupyter
  - code editor
---

(space)=

# Spaces with SageMaker HyperPod

SageMaker HyperPod Spaces provide interactive development environments on EKS-orchestrated clusters. This guide covers how to create and manage spaces using both the HyperPod CLI and SDK.

## Overview

SageMaker HyperPod Spaces allow you to:

- Create interactive development workspaces
- Specify custom Docker images for your environment
- Configure resource requirements (CPUs, GPUs, memory, etc.)
- Set up persistent storage with volumes
- Manage workspace lifecycle (create, start, stop, list, describe, update, delete)
- Access workspaces via port forwarding, web UI, or remote connections


## Creating Spaces

You can create spaces using either the CLI or SDK approach:

`````{tab-set}
````{tab-item} CLI
```bash
hyp create hyp-space \
    --name myspace \
    --display-name "My Space"
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace
from hyperpod_space_template.v1_0.model import SpaceConfig

# Create space configuration
space_config = SpaceConfig(
    name="myspace",
    display_name="My Space",
)

# Create and start the space
space = HPSpace(config=space_config)
space.create()
```
````
`````

### Key Parameters

When creating a space, you'll need to specify:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| **name** | TEXT | Yes | Unique identifier for your space |
| **display-name** | TEXT | Yes | Human-readable name for the space |
| **namespace** | TEXT | No | Kubernetes namespace |
| **image** | TEXT | No | Docker image for the workspace environment |
| **cpu** | TEXT | No | CPU resource request |
| **cpu-limit** | TEXT | No | CPU resource limit |
| **memory** | TEXT | No | Memory resource request |
| **memory-limit** | TEXT | No | Memory resource limit |
| **gpu** | TEXT | No | GPU resource request |
| **gpu-limit** | TEXT | No | GPU resource limit |
| **accelerator-partition-type** | TEXT | No | Fractional GPU partition type (e.g., 'mig-3g.20gb') |
| **accelerator-partition-count** | TEXT | No | Fractional GPU partition count |
| **volume** | TEXT | No | Volume configuration (can be specified multiple times) |
| **debug** | FLAG | No | Enable debug mode |


## Managing Spaces

### List Spaces

`````{tab-set}
````{tab-item} CLI
```bash
# List spaces in default namespace
hyp list hyp-space

# List spaces in specific namespace
hyp list hyp-space --namespace my-namespace

# List spaces across all namespaces
hyp list hyp-space --all-namespaces
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# List all spaces in default namespace
spaces = HPSpace.list()
for space in spaces:
    print(f"Space: {space.config.name}, Status: {space.status}")

# List spaces in specific namespace
spaces = HPSpace.list(namespace="your-namespace")
```
````
`````

### Describe a Space

`````{tab-set}
````{tab-item} CLI
```bash
hyp describe hyp-space --name myspace
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get specific space
space = HPSpace.get(name="myspace", namespace="default")
print(f"Space name: {space.config.name}")
print(f"Display name: {space.config.display_name}")
```
````
`````

### Update a Space

`````{tab-set}
````{tab-item} CLI
```bash
hyp update hyp-space \
    --name myspace \
    --display-name "Updated Space Name"
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Update space configuration
space.update(
    display_name="Updated Space Name",
)
```
````
`````

### Start/Stop a Space

`````{tab-set}
````{tab-item} CLI
```bash
# Start a space
hyp start hyp-space --name myspace

# Stop a space
hyp stop hyp-space --name myspace
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Start the space
space.start()

# Stop the space
space.stop()
```
````
`````

### Get Logs from a Space

`````{tab-set}
````{tab-item} CLI
```bash
hyp get-logs hyp-space --name myspace
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get space and retrieve logs
space = HPSpace.get(name="myspace")

# Get logs from default pod and container
logs = space.get_logs()
print(logs)
```
````
`````

### Port Forward to a Space

`````{tab-set}
````{tab-item} CLI
```bash
# Port forward with default port (8888)
hyp portforward hyp-space --name myspace

# Port forward with custom local port
hyp portforward hyp-space --name myspace --local-port 8080
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Port forward with default remote port (8888)
space.portforward_space(local_port="8080")

# Port forward with custom remote port
space.portforward_space(local_port="8080", remote_port="8888")
```
````
`````

Access the space via `http://localhost:<local-port>` after port forwarding is established. Press Ctrl+C to stop port forwarding.

### Create Space Access

`````{tab-set}
````{tab-item} CLI
```bash
# Create VS Code remote access
hyp create hyp-space-access --name myspace --connection-type vscode-remote

# Create web UI access
hyp create hyp-space-access --name myspace --connection-type web-ui
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Create VS Code remote access
vscode_access = space.create_space_access(connection_type="vscode-remote")
print(f"VS Code URL: {vscode_access['SpaceConnectionUrl']}")

# Create web UI access
web_access = space.create_space_access(connection_type="web-ui")
print(f"Web UI URL: {web_access['SpaceConnectionUrl']}")
```
````
`````

### Delete a Space

`````{tab-set}
````{tab-item} CLI
```bash
hyp delete hyp-space --name myspace
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space import HPSpace

# Get existing space
space = HPSpace.get(name="myspace")

# Delete the space
space.delete()
```
````
`````

## Space Template Management

Create reusable space templates for standardized workspace configurations:

`````{tab-set}
````{tab-item} CLI
```bash
# Create a space template
hyp create hyp-space-template --file template.yaml

# List all space templates
hyp list hyp-space-template --all-namespaces

# Describe a specific template
hyp describe hyp-space-template --name <template-name>

# Update a space template
hyp update hyp-space-template --name <template-name> --file updated-template.yaml

# Delete a space template
hyp delete hyp-space-template --name <template-name>
```
````
````{tab-item} SDK
```python
from sagemaker.hyperpod.space.hyperpod_space_template import HPSpaceTemplate

# Create space template from YAML file
template = HPSpaceTemplate(file_path="template.yaml")
template.create()

# List all space templates
templates = HPSpaceTemplate.list()
for template in templates:
    print(f"Template: {template.name}")

# Get specific space template
template = HPSpaceTemplate.get(name="my-template")
print(template.to_yaml())

# Update space template
template.update(file_path="updated-template.yaml")

# Delete space template
template.delete()
```
````
`````
