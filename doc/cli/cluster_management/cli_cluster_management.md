(cli_cluster_management)=

# Cluster Management

Complete reference for SageMaker HyperPod cluster management parameters and configuration options.

```{note}
**Region Configuration**: For commands that accept the `--region` option, if no region is explicitly provided, the command will use the default region from your AWS credentials configuration.
```

* [Initialize Configuration](#hyp-init)
* [Create Cluster Stack](#hyp-create)
* [Update Cluster](#hyp-update-cluster)
* [List Cluster Stacks](#hyp-list-cluster-stack)
* [Describe Cluster Stack](#hyp-describe-cluster-stack)
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
| `TEMPLATE` | CHOICE | Yes | Template type (cluster-stack, hyp-pytorch-job, hyp-custom-endpoint, hyp-jumpstart-endpoint) |
| `DIRECTORY` | PATH | No | Target directory (default: current directory) |
| `--version` | TEXT | No | Schema version to use |

```{important}
The `resource_name_prefix` parameter in the generated `config.yaml` file serves as the primary identifier for all AWS resources created during deployment. Each deployment must use a unique resource name prefix to avoid conflicts. This prefix is automatically appended with a unique identifier during cluster creation to ensure resource uniqueness.

**Cluster stack names must be unique within each AWS region.** If you attempt to create a cluster stack with a name that already exists in the same region, the deployment will fail.
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

## hyp update cluster

Update an existing HyperPod cluster configuration.

```{important}
**Runtime vs Configuration Commands**: This command modifies an **existing, deployed cluster's** runtime settings (instance groups, node recovery). This is different from `hyp configure`, which only modifies local configuration files before cluster creation.
```

#### Syntax

```bash
hyp update cluster [OPTIONS]
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

## hyp list cluster-stack

List all HyperPod cluster stacks (CloudFormation stacks).

#### Syntax

```bash
hyp list cluster-stack [OPTIONS]
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--region` | TEXT | No | AWS region to list stacks from |
| `--status` | TEXT | No | Filter by stack status. Format: "['CREATE_COMPLETE', 'UPDATE_COMPLETE']" |
| `--debug` | FLAG | No | Enable debug logging |

## hyp describe cluster-stack

Describe a specific HyperPod cluster stack.

```{note}
**Region-Specific Stack Names**: Cluster stack names are unique within each AWS region. When describing a stack, ensure you specify the correct region where the stack was created, or the command will fail to find the stack.
```

#### Syntax

```bash
hyp describe cluster-stack STACK-NAME [OPTIONS]
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

```{important}
**Pre-Deployment Configuration**: This command modifies local `config.yaml` files **before** cluster creation. For updating **existing, deployed clusters**, use `hyp update cluster` instead.
```

#### Syntax

```bash
hyp configure [OPTIONS]
```

#### Parameters

This command dynamically supports all configuration parameters available in the current template's schema. Common parameters include:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--resource-name-prefix` | TEXT | No | Prefix for all AWS resources |
| `--create-hyperpod-cluster-stack` | BOOLEAN | No | Create HyperPod Cluster Stack |
| `--hyperpod-cluster-name` | TEXT | No | Name of SageMaker HyperPod Cluster |
| `--create-eks-cluster-stack` | BOOLEAN | No | Create EKS Cluster Stack |
| `--kubernetes-version` | TEXT | No | Kubernetes version |
| `--eks-cluster-name` | TEXT | No | Name of the EKS cluster |
| `--create-helm-chart-stack` | BOOLEAN | No | Create Helm Chart Stack |
| `--namespace` | TEXT | No | Namespace to deploy HyperPod Helm chart |
| `--node-provisioning-mode` | TEXT | No | Continuous provisioning mode |
| `--node-recovery` | TEXT | No | Node recovery setting ("Automatic" or "None") |
| `--create-vpc-stack` | BOOLEAN | No | Create VPC Stack |
| `--vpc-id` | TEXT | No | Existing VPC ID |
| `--vpc-cidr` | TEXT | No | VPC CIDR block |
| `--create-security-group-stack` | BOOLEAN | No | Create Security Group Stack |
| `--enable-hp-inference-feature` | BOOLEAN | No | Enable inference operator |
| `--stage` | TEXT | No | Deployment stage ("gamma" or "prod") |
| `--create-fsx-stack` | BOOLEAN | No | Create FSx Stack |
| `--storage-capacity` | INTEGER | No | FSx storage capacity in GiB |
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
| `resource_name_prefix` | TEXT | Prefix for all AWS resources (4-digit UUID added during submission) | "hyp-eks-stack" |
| `create_hyperpod_cluster_stack` | BOOLEAN | Create HyperPod Cluster Stack | true |
| `hyperpod_cluster_name` | TEXT | Name of SageMaker HyperPod Cluster | "hyperpod-cluster" |
| `create_eks_cluster_stack` | BOOLEAN | Create EKS Cluster Stack | true |
| `kubernetes_version` | TEXT | Kubernetes version | "1.31" |
| `eks_cluster_name` | TEXT | Name of the EKS cluster | "eks-cluster" |
| `create_helm_chart_stack` | BOOLEAN | Create Helm Chart Stack | true |
| `namespace` | TEXT | Namespace to deploy HyperPod Helm chart | "kube-system" |
| `helm_repo_url` | TEXT | URL of Helm repo containing HyperPod Helm chart | "https://github.com/aws/sagemaker-hyperpod-cli.git" |
| `helm_repo_path` | TEXT | Path to HyperPod Helm chart in repo | "helm_chart/HyperPodHelmChart" |
| `helm_operators` | TEXT | Configuration of HyperPod Helm chart | "mlflow.enabled=true,trainingOperators.enabled=true,..." |
| `helm_release` | TEXT | Name for Helm chart release | "dependencies" |
| `node_provisioning_mode` | TEXT | Continuous provisioning mode ("Continuous" or empty) | "Continuous" |
| `node_recovery` | TEXT | Automatic node recovery ("Automatic" or "None") | "Automatic" |
| `instance_group_settings` | ARRAY | List of instance group configurations | [Default controller group] |
| `rig_settings` | ARRAY | Restricted instance group configurations | null |
| `rig_s3_bucket_name` | TEXT | S3 bucket for RIG resources | null |
| `tags` | ARRAY | Custom tags for SageMaker HyperPod cluster | null |
| `create_vpc_stack` | BOOLEAN | Create VPC Stack | true |
| `vpc_id` | TEXT | Existing VPC ID (if not creating new) | null |
| `vpc_cidr` | TEXT | IP range for VPC | "10.192.0.0/16" |
| `availability_zone_ids` | ARRAY | List of AZs to deploy subnets | null |
| `create_security_group_stack` | BOOLEAN | Create Security Group Stack | true |
| `security_group_id` | TEXT | Existing security group ID | null |
| `security_group_ids` | ARRAY | Security groups for HyperPod cluster | null |
| `private_subnet_ids` | ARRAY | Private subnet IDs for HyperPod cluster | null |
| `eks_private_subnet_ids` | ARRAY | Private subnet IDs for EKS cluster | null |
| `nat_gateway_ids` | ARRAY | NAT Gateway IDs for internet routing | null |
| `private_route_table_ids` | ARRAY | Private route table IDs | null |
| `create_s3_endpoint_stack` | BOOLEAN | Create S3 Endpoint stack | true |
| `enable_hp_inference_feature` | BOOLEAN | Enable inference operator | false |
| `stage` | TEXT | Deployment stage ("gamma" or "prod") | "prod" |
| `custom_bucket_name` | TEXT | S3 bucket name for templates | "sagemaker-hyperpod-cluster-stack-bucket" |
| `create_life_cycle_script_stack` | BOOLEAN | Create Life Cycle Script Stack | true |
| `create_s3_bucket_stack` | BOOLEAN | Create S3 Bucket Stack | true |
| `s3_bucket_name` | TEXT | S3 bucket for cluster lifecycle scripts | "s3-bucket" |
| `github_raw_url` | TEXT | Raw GitHub URL for lifecycle script | "https://raw.githubusercontent.com/aws-samples/..." |
| `on_create_path` | TEXT | File name of lifecycle script | "sagemaker-hyperpod-eks-bucket" |
| `create_sagemaker_iam_role_stack` | BOOLEAN | Create SageMaker IAM Role Stack | true |
| `sagemaker_iam_role_name` | TEXT | IAM role name for SageMaker cluster creation | "create-cluster-role" |
| `create_fsx_stack` | BOOLEAN | Create FSx Stack | true |
| `fsx_subnet_id` | TEXT | Subnet ID for FSx creation | "" |
| `fsx_availability_zone_id` | TEXT | Availability zone for FSx subnet | "" |
| `per_unit_storage_throughput` | INTEGER | Per unit storage throughput | 250 |
| `data_compression_type` | TEXT | Data compression type ("NONE" or "LZ4") | "NONE" |
| `file_system_type_version` | FLOAT | File system type version | 2.15 |
| `storage_capacity` | INTEGER | Storage capacity in GiB | 1200 |
| `fsx_file_system_id` | TEXT | Existing FSx file system ID | "" |

**Note:** The actual available configuration parameters depend on the specific template schema version. Use `hyp init cluster-stack` to see all available parameters for your version.

## Examples

### Basic Cluster Stack Creation

```bash
# Start with a clean directory
mkdir my-hyperpod-cluster
cd my-hyperpod-cluster

# Initialize cluster configuration
hyp init cluster-stack

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
hyp update cluster \
    --cluster-name my-cluster \
    --instance-groups '[{"InstanceCount":2,"InstanceGroupName":"worker-nodes","InstanceType":"ml.m5.large"}]' \
    --region us-west-2
```

### List and Describe

```bash
# List all cluster stacks
hyp list cluster-stack --region us-west-2

# Describe specific cluster stack
hyp describe cluster-stack my-stack-name --region us-west-2

# List HyperPod clusters with capacity info
hyp list-cluster --region us-west-2 --output table

# Connect to cluster
hyp set-cluster-context --cluster-name my-cluster --region us-west-2

# Get current context
hyp get-cluster-context
```