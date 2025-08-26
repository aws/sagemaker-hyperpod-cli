(cli_cluster_management)=

# Cluster Management

Complete reference for SageMaker HyperPod cluster management parameters and configuration options.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

* [Initialize Configuration](#hyp-init)
* [Create Cluster Stack](#hyp-create)
* [Update Cluster](#hyp-update-hyp-cluster)
* [List Cluster Stacks](#hyp-list-hyp-cluster)
* [Describe Cluster Stack](#hyp-describe-hyp-cluster)
* [List HyperPod Clusters](#hyp-list-cluster)
* [Set Cluster Context](#hyp-set-cluster-context)
* [Get Cluster Context](#hyp-get-cluster-context)
* [Get Monitoring](#hyp-get-monitoring)

* [Configure Parameters](#hyp-configure)
* [Validate Configuration](#hyp-validate)
* [Reset Configuration](#hyp-reset)

## hyp init

Initialize a template scaffold in the current directory.

#### Syntax

```bash
hyp init TEMPLATE [DIRECTORY] [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `TEMPLATE` | CHOICE | Yes | Template type (hyp-cluster, hyp-pytorch-job, hyp-custom-endpoint, hyp-jumpstart-endpoint) |
| `DIRECTORY` | PATH | No | Target directory (default: current directory) |
| `--version` | TEXT | No | Schema version to use |

```{important}
The `resource_name_prefix` parameter in the generated `config.yaml` file serves as the primary identifier for all AWS resources created during deployment. Each deployment must use a unique resource name prefix to avoid conflicts. This prefix is automatically appended with a unique identifier during cluster creation to ensure resource uniqueness.
```

## hyp create

Create a new HyperPod cluster stack using the provided configuration.

#### Syntax

```bash
hyp create [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--region` | TEXT | No | AWS region where the cluster stack will be created |
| `--debug` | FLAG | No | Enable debug logging |

## hyp update hyp-cluster

Update an existing HyperPod cluster configuration.

#### Syntax

```bash
hyp update hyp-cluster [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--cluster-name` | TEXT | Yes | Name of the cluster to update |
| `--instance-groups` | TEXT | No | JSON string of instance group configurations |
| `--instance-groups-to-delete` | TEXT | No | JSON string of instance groups to delete |
| `--region` | TEXT | No | AWS region of the cluster |
| `--node-recovery` | TEXT | No | Node recovery setting (Automatic or None) |
| `--debug` | FLAG | No | Enable debug logging |

## hyp list hyp-cluster

List all HyperPod cluster stacks (CloudFormation stacks).

#### Syntax

```bash
hyp list hyp-cluster [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--region` | TEXT | No | AWS region to list stacks from |
| `--status` | TEXT | No | Filter by stack status. Format: "['CREATE_COMPLETE', 'UPDATE_COMPLETE']" |
| `--debug` | FLAG | No | Enable debug logging |

## hyp describe hyp-cluster

Describe a specific HyperPod cluster stack.

#### Syntax

```bash
hyp describe hyp-cluster STACK-NAME [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `STACK-NAME` | TEXT | Yes | Name of the CloudFormation stack to describe |
| `--region` | TEXT | No | AWS region of the stack |
| `--debug` | FLAG | No | Enable debug logging |

## hyp list-cluster

List SageMaker HyperPod clusters with capacity information.

#### Syntax

```bash
hyp list-cluster [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--region` | TEXT | No | AWS region to list clusters from |
| `--output` | TEXT | No | Output format ("table" or "json", default: "json") |
| `--clusters` | TEXT | No | Comma-separated list of specific cluster names |
| `--namespace` | TEXT | No | Namespace to check capacity for (can be used multiple times) |
| `--debug` | FLAG | No | Enable debug logging |

## hyp set-cluster-context

Connect to a HyperPod EKS cluster and set kubectl context.

#### Syntax

```bash
hyp set-cluster-context [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--cluster-name` | TEXT | Yes | Name of the HyperPod cluster to connect to |
| `--region` | TEXT | No | AWS region of the cluster |
| `--namespace` | TEXT | No | Kubernetes namespace to connect to |
| `--debug` | FLAG | No | Enable debug logging |

## hyp get-cluster-context

Get context information for the currently connected cluster.

#### Syntax

```bash
hyp get-cluster-context [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--debug` | FLAG | No | Enable debug logging |

## hyp get-monitoring

Get monitoring configurations for the HyperPod cluster.

#### Syntax

```bash
hyp get-monitoring [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--grafana` | FLAG | No | Return Grafana dashboard URL |
| `--prometheus` | FLAG | No | Return Prometheus workspace URL |
| `--list` | FLAG | No | Return list of available metrics |

## hyp configure

Configure cluster parameters interactively or via command line.

#### Syntax

```bash
hyp configure [OPTIONS]
```

#### Parameters

This command dynamically supports all configuration parameters available in the current template's schema. Common parameters include:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--resource-name-prefix` | TEXT | No | Prefix for all AWS resources |
| `--stage` | TEXT | No | Deployment stage ("gamma" or "prod") |
| `--vpc-cidr` | TEXT | No | VPC CIDR block |
| `--kubernetes-version` | TEXT | No | Kubernetes version for EKS cluster |
| `--node-recovery` | TEXT | No | Node recovery setting ("Automatic" or "None") |
| `--env` | JSON | No | Environment variables as JSON object |
| `--args` | JSON | No | Command arguments as JSON array |
| `--command` | JSON | No | Command to run as JSON array |
| `--tags` | JSON | No | Resource tags as JSON object |

**Note:** The exact parameters available depend on your current template type and version. Run `hyp configure --help` to see all available options for your specific configuration.

## hyp validate

Validate the current directory's configuration file syntax and structure.

#### Syntax

```bash
hyp validate
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


#### Syntax

```bash
# Validate current configuration syntax
hyp validate

# Example output on success
✔️ config.yaml is valid!

# Example output with syntax errors
❌ Config validation errors:
  – kubernetes_version: Field is required
  – vpc_cidr: Expected string, got number
```

## hyp reset

Reset the current directory's config.yaml to default values.

#### Syntax

```bash
hyp reset
```

#### Parameters

No parameters required.



## Parameter Reference

### Common Parameters Across Commands

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `--region` | TEXT | AWS region | Current AWS profile region |
| `--help` | FLAG | Show command help | - |
| `--verbose` | FLAG | Enable verbose output | false |

### Configuration File Parameters

The `config.yaml` file supports the following parameters:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `template` | TEXT | Template name | "hyp-cluster" |
| `namespace` | TEXT | Kubernetes namespace | "kube-system" |
| `stage` | TEXT | Deployment stage | "gamma" |
| `resource_name_prefix` | TEXT | Resource name prefix | "sagemaker-hyperpod-eks" |
| `vpc_cidr` | TEXT | VPC CIDR block | "10.192.0.0/16" |
| `kubernetes_version` | TEXT | Kubernetes version | "1.31" |
| `node_recovery` | TEXT | Node recovery setting | "Automatic" |
| `create_vpc_stack` | BOOLEAN | Create new VPC | true |
| `create_eks_cluster_stack` | BOOLEAN | Create new EKS cluster | true |
| `create_hyperpod_cluster_stack` | BOOLEAN | Create HyperPod cluster | true |

**Note:** The actual available configuration parameters depend on the specific template schema version. Use `hyp init hyp-cluster` to see all available parameters for your version.

## Examples

### Basic Cluster Stack Creation

```bash
# Start with a clean directory
mkdir my-hyperpod-cluster
cd my-hyperpod-cluster

# Initialize cluster configuration
hyp init hyp-cluster

# Configure basic parameters
hyp configure --resource-name-prefix my-cluster --stage prod

# Validate configuration
hyp validate

# Create cluster stack
hyp create --region us-west-2
```

### Update Existing Cluster

```bash
# Update instance groups
hyp update hyp-cluster \
    --cluster-name my-cluster \
    --instance-groups '[{"InstanceCount":2,"InstanceGroupName":"worker-nodes","InstanceType":"ml.m5.large"}]' \
    --region us-west-2
```

### List and Describe

```bash
# List all cluster stacks
hyp list hyp-cluster --region us-west-2

# Describe specific cluster stack
hyp describe hyp-cluster my-stack-name --region us-west-2

# List HyperPod clusters with capacity info
hyp list-cluster --region us-west-2 --output table

# Connect to cluster
hyp set-cluster-context --cluster-name my-cluster --region us-west-2

# Get current context
hyp get-cluster-context
```