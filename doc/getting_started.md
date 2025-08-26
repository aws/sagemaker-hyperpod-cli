(getting_started)=

# Getting Started

```{toctree}
:hidden:
:maxdepth: 1

Cluster Management <getting_started/cluster_management>
Training <getting_started/training>
Inference <getting_started/inference>

```

This guide will help you get started with the SageMaker HyperPod CLI and SDK to perform basic operations.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

## List Available Clusters

List all available SageMaker HyperPod clusters in your account:

`````{tab-set}
````{tab-item} CLI
```bash
hyp list-cluster [--region <region>]
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod import list_clusters

list_clusters(region='aws-region')

```
````
`````

## Connect to a Cluster

Configure your local kubectl environment to interact with a specific SageMaker HyperPod cluster and namespace:

`````{tab-set}
````{tab-item} CLI
```bash
hyp set-cluster-context --cluster-name <cluster-name>
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod import set_cluster_context

set_cluster_context('<my-cluster>')

```
````
`````

## Get Current Cluster Context

View information about the currently configured cluster context:

`````{tab-set}
````{tab-item} CLI
```bash
hyp get-cluster-context
```
````

````{tab-item} SDK
```python
from sagemaker.hyperpod import get_cluster_context

get_cluster_context()
```
````
`````


## Next Steps

After setting up your environment and connecting to a cluster, you can:

- Create and manage PyTorch training jobs
- Deploy and manage inference endpoints
- Monitor cluster resources and job performance

For more detailed information on specific commands, use the `--help` flag:

```bash
hyp <command> --help
```