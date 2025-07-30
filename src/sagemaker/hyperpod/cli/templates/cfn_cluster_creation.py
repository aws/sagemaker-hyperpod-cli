CLOUDFORMATION_CLUSTER_CREATION_TEMPLATE = """### Please keep template file unchanged ###
Description: Main Stack for EKS based HyperPod Cluster
Parameters:
  Stage:
    Type: String
    Default: {{ stage | default('gamma') }}
    AllowedValues:
      - gamma
      - prod
    Description: Deployment stage (gamma, prod)
  ResourceNamePrefix:
    Type: String
    Default: {{ resource_name_prefix | default('sagemaker-hyperpod-eks') }}
    Description: Prefix to be used for all resources created by this template.
  VpcCIDR:
    Type: String
    Default: {{ vpc_cidr | default('10.192.0.0/16') }}
    Description: The IP range (CIDR notation) for the VPC.
  AvailabilityZoneIds:
    Type: String
    Default: {{ availability_zone_ids | default('use2-az1,use2-az2') }}
    Description: List of AZs to deploy subnets in (up to 5, comma separated)
  VpcId:
    Type: String
    Default: {{ vpc_id | default('vpc-1234567890abcdef0') }}
    Description: The ID of the VPC you wish to use if you do not want to create a new VPC.
  NatGatewayIds:
    Type: String
    Default: {{ nat_gateway_ids | default('nat-1234567890abcdef0') }}
    Description: Comma-separated list of NAT Gateway IDs to route internet bound traffic to from the newly created private subnets.
  SecurityGroupId:
    Type: String
    Default: {{ security_group_id | default('') }}
    Description: The ID of the security group associated with an existing EKS cluster.
  KubernetesVersion:
    Type: String
    Default: {{ kubernetes_version | default('1.31') }}
    Description: The Kubernetes version to use for the EKS cluster.
  EKSClusterName:
    Type: String
    Default: {{ eks_cluster_name | default('eks') }}
    Description: The name of the newly created of preexisting EKS cluster you wish to use.
  EksPrivateSubnetIds:
    Type: String
    Default: {{ eks_private_subnet_ids | default('subnet-1234567890abcdef0,subnet-1234567890abcdef0') }}
    Description: Comma-delimited list of private subnet IDs for the EKS cluster
  SecurityGroupIds:
    Type: String
    Default: {{ security_group_ids | default('sg-1234567890abcdef0') }}
    Description: The Id of your cluster security group.
  PrivateRouteTableIds:
    Type: String
    Default: {{ private_route_table_ids | default('rtb-1234567890abcdef0') }}
    Description: Comma-separated list of private route table IDs.
  S3BucketName:
    Type: String
    Default: {{ s3_bucket_name | default('s3-bucket') }}
    Description: The name of the S3 bucket used to store the cluster lifecycle scripts.
  GithubRawUrl:
    Type: String
    Default: {{ github_raw_url | default('https://raw.githubusercontent.com/aws-samples/awsome-distributed-training/refs/heads/main/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config/on_create.sh') }}
    Description: The raw GitHub URL for the lifecycle script.
  HelmRepoUrl:
    Type: String
    Default: {{ helm_repo_url | default('https://github.com/aws/sagemaker-hyperpod-cli.git') }}
    Description: The URL of the Helm repo containing the HyperPod Helm chart.
  HelmRepoPath:
    Type: String
    Default: {{ helm_repo_path | default('helm_chart/HyperPodHelmChart') }}
    Description: The path to the HyperPod Helm chart in the Helm repo.
  HelmOperators:
    Type: String
    Default: {{ helm_operators | default('') }}
    Description: The configuration of HyperPod Helm chart
  Namespace:
    Type: String
    Default: {{ namespace | default('kube-system') }}
    Description: The namespace to deploy the HyperPod Helm chart into.
  HelmRelease:
    Type: String
    Default: {{ helm_release | default('hyperpod-dependencies') }}
    Description: The name of the Helm release.
  HyperPodClusterName:
    Type: String
    Default: {{ hyperpod_cluster_name | default('hp-cluster') }}
    Description: Name of SageMaker HyperPod Cluster.
  NodeRecovery:
    Type: String
    Default: {{ node_recovery | default('Automatic') }}
    AllowedValues:
      - Automatic
      - None
    Description: Specifies whether to enable or disable the automatic node recovery feature (Automatic or None).
  SageMakerIAMRoleName:
    Type: String
    Default: {{ sagemaker_iam_role_name | default('iam-role') }}
    Description: The name of the IAM role that SageMaker will use to access the AWS resources on your behalf.
  PrivateSubnetIds:
    Type: String
    Default: {{ private_subnet_ids | default('subnet-1234567890abcdef0,subnet-1234567890abcdef0') }}
    Description: Comma-separated list of private subnet IDs for EKS cluster.
  OnCreatePath:
    Type: String
    Default: {{ on_create_path | default('sagemaker-hyperpod-eks-bucket') }}
    Description: The file name of lifecycle script for the general purpose instance group. This script runs during cluster creation.
{% for i in range(1, 21) %}
  InstanceGroupSettings{{ i }}:
    Type: String
    Default: {{ instance_group_settings[i-1] | default('[]') }}
    Description: JSON array string containing instance group configurations.
  RigSettings{{ i }}:
    Type: String
    Default: {{ rig_settings[i-1] | default('[]') }}
    Description: JSON array string containing restricted instance group configurations.
{% endfor %}
  Tags:
    Type: String
    Default: {{ tags | default('[]') }}
    Description: Custom tags for managing the SageMaker HyperPod cluster as an AWS resource.'
  FsxSubnetId:
    Type: String
    Default: {{ fsx_subnet_id | default('') }}
    Description: The subnet id that will be used to create FSx
  FsxAvailabilityZone:
    Type: String
    Default: {{ fsx_availability_zone | default('use2-az1') }}
    Description: The availability zone to get subnet id that will be used to create FSx
  PerUnitStorageThroughput:
    Type: Number
    Default: {{ per_unit_storage_throughput | default(250) }}
    Description: Per unit storage throughput for the FSx file system
  DataCompressionType:
    Type: String
    Default: {{ data_compression_type | default('NONE') }}
    AllowedValues:
      - NONE
      - LZ4
    Description: Data compression type for the FSx file system (NONE, LZ4)
  FileSystemTypeVersion:
    Type: Number
    Default: {{ file_system_type_version | default(2.12) }}
    Description: File system type version for the FSx file system
  StorageCapacity:
    Type: Number
    Default: {{ storage_capacity | default(1200) }}
    Description: Storage capacity for the FSx file system in GiB
  FsxFileSystemId:
    Type: String
    Default: {{ fsx_file_system_id | default('') }}
    Description: Existing FSx for Lustre file system
  CreateVPCStack:
    Type: String
    Default: {{ create_vpc_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create VPC Stack
  CreatePrivateSubnetStack:
    Type: String
    Default: {{ create_private_subnet_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create Private Subnet Stack
  CreateSecurityGroupStack:
    Type: String
    Default: {{ create_security_group_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create Security Group Stack
  CreateEKSClusterStack:
    Type: String
    Default: {{ create_eks_cluster_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create EKS Cluster Stack
  CreateS3BucketStack:
    Type: String
    Default: {{ create_s3_bucket_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create S3 Bucket Stack
  CreateS3EndpointStack:
    Type: String
    Default: {{ create_s3_endpoint_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create S3 Endpoint Stack
  CreateLifeCycleScriptStack:
    Type: String
    Default: {{ create_life_cycle_script_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create Life Cycle Script Stack
  CreateSageMakerIAMRoleStack:
    Type: String
    Default: {{ create_sagemaker_iam_role_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create SageMaker IAM Role Stack
  CreateHelmChartStack:
    Type: String
    Default: {{ create_helm_chart_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create Helm Chart Stack
  CreateHyperPodClusterStack:
    Type: String
    Default: {{ create_hyperpod_cluster_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create HyperPod Cluster Stack
  CreateFsxStack:
    Type: String
    Default: {{ create_fsx_stack | default('true') }}
    AllowedValues:
      - 'true'
      - 'false'
    Description: Boolean to Create HyperPod Cluster Stack
"""