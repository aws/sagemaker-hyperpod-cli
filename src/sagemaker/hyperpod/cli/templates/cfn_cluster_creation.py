CLOUDFORMATION_CLUSTER_CREATION_TEMPLATE = """### Please keep template file unchanged ###
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: General Settings
        Parameters:
          - ResourceNamePrefix
          - Stage
          - NodeRecovery
          - Tags
      - Label:
          default: Networking
        Parameters:
          - CreateVPCStack
          - VpcId
          - VpcCIDR
          - AvailabilityZoneIds
          - CreateSecurityGroupStack
          - SecurityGroupId
          - SecurityGroupIds
          - CreatePrivateSubnetStack
          - PrivateSubnetIds
          - EksPrivateSubnetIds
          - NatGatewayIds
          - PrivateRouteTableIds
          - CreateS3EndpointStack
      - Label:
          default: Orchestration
        Parameters:
          - CreateEKSClusterStack
          - EKSClusterName
          - KubernetesVersion
          - CreateHelmChartStack
          - HelmRepoUrl
          - HelmRepoPath
          - HelmRelease
          - Namespace
          - HelmOperators
      - Label:
          default: Lifecycle Configuration
        Parameters:
          - CreateLifeCycleScriptStack
          - CreateS3BucketStack
          - S3BucketName
          - GithubRawUrl
          - OnCreatePath
      - Label:
          default: Permissions
        Parameters:
          - CreateSageMakerIAMRoleStack
          - SageMakerIAMRoleName
      - Label:
          default: Storage
        Parameters:
          - CreateFsxStack
          - FsxFileSystemId
          - FsxSubnetId
          - FsxAvailabilityZone
          - StorageCapacity
          - PerUnitStorageThroughput
          - DataCompressionType
          - FileSystemTypeVersion
      - Label:
          default: HyperPod Cluster
        Parameters:
          - CreateHyperPodClusterStack
          - HyperPodClusterName
      - Label:
          default: Instance Groups
        Parameters:
          - InstanceGroupSettings1
          - InstanceGroupSettings2
          - InstanceGroupSettings3
          - InstanceGroupSettings4
          - InstanceGroupSettings5
          - InstanceGroupSettings6
          - InstanceGroupSettings7
          - InstanceGroupSettings8
          - InstanceGroupSettings9
          - InstanceGroupSettings10
          - InstanceGroupSettings11
          - InstanceGroupSettings12
          - InstanceGroupSettings13
          - InstanceGroupSettings14
          - InstanceGroupSettings15
          - InstanceGroupSettings16
          - InstanceGroupSettings17
          - InstanceGroupSettings18
          - InstanceGroupSettings19
          - InstanceGroupSettings20
      - Label:
          default: Restricted Instance Groups
        Parameters:
          - RigSettings1
          - RigSettings2
          - RigSettings3
          - RigSettings4
          - RigSettings5
          - RigSettings6
          - RigSettings7
          - RigSettings8
          - RigSettings9
          - RigSettings10
          - RigSettings11
          - RigSettings12
          - RigSettings13
          - RigSettings14
          - RigSettings15
          - RigSettings16
          - RigSettings17
          - RigSettings18
          - RigSettings19
          - RigSettings20
    ParameterLabels:
      ResourceNamePrefix:
        default: Resource Name Prefix
      Stage:
        default: Deployment Stage
      NodeRecovery:
        default: Instance Recovery
      Tags:
        default: Resource Tags
      CreateVPCStack:
        default: Create New VPC
      VpcId:
        default: Existing VPC ID
      VpcCIDR:
        default: VPC CIDR Range
      AvailabilityZoneIds:
        default: Availability Zone IDs
      CreateSecurityGroupStack:
        default: Create New Security Group
      SecurityGroupId:
        default: Existing Security Group ID
      SecurityGroupIds:
        default: Security Group IDs
      CreatePrivateSubnetStack:
        default: Create Private Subnets
      PrivateSubnetIds:
        default: Private Subnet IDs
      EksPrivateSubnetIds:
        default: EKS Private Subnet IDs
      NatGatewayIds:
        default: NAT Gateway IDs
      PrivateRouteTableIds:
        default: Private Route Table IDs
      CreateS3EndpointStack:
        default: Create S3 Endpoint
      CreateEKSClusterStack:
        default: Create New EKS Cluster
      EKSClusterName:
        default: EKS Cluster Name
      KubernetesVersion:
        default: Kubernetes Version
      CreateHelmChartStack:
        default: Install Helm Charts
      HelmRepoUrl:
        default: Helm Repository URL
      HelmRepoPath:
        default: Helm Chart Path
      HelmRelease:
        default: Helm Release Name
      Namespace:
        default: Kubernetes Namespace
      HelmOperators:
        default: Enabled Operators
      CreateLifeCycleScriptStack:
        default: Create Lifecycle Scripts
      CreateS3BucketStack:
        default: Create New S3 Bucket
      S3BucketName:
        default: S3 Bucket Name
      GithubRawUrl:
        default: GitHub Raw URL
      OnCreatePath:
        default: OnCreate Script Path
      CreateSageMakerIAMRoleStack:
        default: Create New IAM Role
      SageMakerIAMRoleName:
        default: IAM Role Name
      CreateFsxStack:
        default: Create New FSx for Lustre File System
      FsxFileSystemId:
        default: Existing FSx File System ID
      FsxSubnetId:
        default: FSx Subnet ID
      FsxAvailabilityZone:
        default: FSx Availability Zone
      StorageCapacity:
        default: Storage Capacity (GB)
      PerUnitStorageThroughput:
        default: Per-unit Storage Throughput (MB/s/TiB)
      DataCompressionType:
        default: Compression Type
      FileSystemTypeVersion:
        default: Lustre Version
      CreateHyperPodClusterStack:
        default: Create HyperPod Cluster
      HyperPodClusterName:
        default: HyperPod Cluster Name
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
    Default: {{ availability_zone_ids | default('') }}
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
    Default: https://raw.githubusercontent.com/aws-samples/awsome-distributed-training/refs/heads/main/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config/on_create.sh
    Description: The raw GitHub URL for the lifecycle script.
  HelmRepoUrl:
    Type: String
    Default: https://github.com/aws/sagemaker-hyperpod-cli.git
    Description: The URL of the Helm repo containing the HyperPod Helm chart.
  HelmRepoPath:
    Type: String
    Default: helm_chart/HyperPodHelmChart
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
    Description: Custom tags for managing the SageMaker HyperPod cluster as an AWS resource.
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
    Default: {{ file_system_type_version | default(2.15) }}
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
    Description: Boolean to Create FSx for Lustre File System Stack
Conditions:
  CreateVPCStackCondition:
    Fn::Equals:
      - Ref: CreateVPCStack
      - 'true'
  CreatePrivateSubnetStackCondition:
    Fn::Equals:
      - Ref: CreatePrivateSubnetStack
      - 'true'
  CreateSecurityGroupStackCondition:
    Fn::Equals:
      - Ref: CreateSecurityGroupStack
      - 'true'
  CreateEKSClusterStackCondition:
    Fn::Equals:
      - Ref: CreateEKSClusterStack
      - 'true'
  CreateS3BucketStackCondition:
    Fn::Equals:
      - Ref: CreateS3BucketStack
      - 'true'
  CreateS3EndpointStackCondition:
    Fn::Equals:
      - Ref: CreateS3EndpointStack
      - 'true'
  CreateLifeCycleScriptStackCondition:
    Fn::Equals:
      - Ref: CreateLifeCycleScriptStack
      - 'true'
  CreateSageMakerIAMRoleStackCondition:
    Fn::Equals:
      - Ref: CreateSageMakerIAMRoleStack
      - 'true'
  CreateHelmChartStackCondition:
    Fn::Equals:
      - Ref: CreateHelmChartStack
      - 'true'
  CreateHyperPodClusterStackCondition:
    Fn::And:
      - Fn::Equals:
          - Ref: CreateHyperPodClusterStack
          - 'true'
      - Fn::Not:
          - Fn::And:
              - Fn::Equals:
                  - Ref: CreateEKSClusterStack
                  - 'true'
              - Fn::Equals:
                  - Ref: CreateHelmChartStack
                  - 'false'
  CreateFsxStackCondition:
    Fn::Equals:
      - Ref: CreateFsxStack
      - 'true'
Resources:
  VPCStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/vpc-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        VpcCIDR:
          Ref: VpcCIDR
        AvailabilityZoneIds:
          Fn::Join:
            - ','
            - - Ref: AvailabilityZoneIds
              - ''
              - ''
              - ''
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/VPCStack
    Condition: CreateVPCStackCondition
  PrivateSubnetStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/private-subnet-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        VpcId:
          Fn::If:
            - CreateVPCStackCondition
            - Fn::GetAtt:
                - VPCStack
                - Outputs.VpcId
            - Ref: VpcId
        VpcCidrBlock:
          Ref: VpcCIDR
        AvailabilityZoneIds:
          Fn::Join:
            - ','
            - - Ref: AvailabilityZoneIds
              - ''
              - ''
              - ''
        NatGatewayIds:
          Fn::If:
            - CreateVPCStackCondition
            - Fn::GetAtt:
                - VPCStack
                - Outputs.NatGatewayIds
            - Ref: NatGatewayIds
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/PrivateSubnetStack
    Condition: CreatePrivateSubnetStackCondition
  SecurityGroupStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/security-group-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        VpcId:
          Fn::If:
            - CreateVPCStackCondition
            - Fn::GetAtt:
                - VPCStack
                - Outputs.VpcId
            - Ref: VpcId
        SecurityGroupId:
          Ref: SecurityGroupId
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/SecurityGroupStack
    Condition: CreateSecurityGroupStackCondition
  EKSClusterStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/eks-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        VpcId:
          Fn::If:
            - CreateVPCStackCondition
            - Fn::GetAtt:
                - VPCStack
                - Outputs.VpcId
            - Ref: VpcId
        KubernetesVersion:
          Ref: KubernetesVersion
        EKSClusterName:
          Ref: EKSClusterName
        EksPrivateSubnetIds:
          Fn::If:
            - CreatePrivateSubnetStackCondition
            - Fn::GetAtt:
                - PrivateSubnetStack
                - Outputs.EksPrivateSubnetIds
            - Ref: PrivateSubnetIds
        SecurityGroupIds:
          Fn::If:
            - CreateSecurityGroupStackCondition
            - Fn::GetAtt:
                - SecurityGroupStack
                - Outputs.SecurityGroupId
            - Ref: SecurityGroupIds
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/EKSClusterStack
    Condition: CreateEKSClusterStackCondition
  S3BucketStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/s3-bucket-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/S3BucketStack
    Condition: CreateS3BucketStackCondition
  S3EndpointStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/s3-endpoint-template.yaml
      Parameters:
        VpcId:
          Fn::If:
            - CreateVPCStackCondition
            - Fn::GetAtt:
                - VPCStack
                - Outputs.VpcId
            - Ref: VpcId
        PrivateRouteTableIds:
          Fn::If:
            - CreatePrivateSubnetStackCondition
            - Fn::GetAtt:
                - PrivateSubnetStack
                - Outputs.PrivateRouteTableIds
            - Ref: PrivateRouteTableIds
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/S3EndpointStack
    Condition: CreateS3EndpointStackCondition
  LifeCycleScriptStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/lifecycle-script-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        S3BucketName:
          Fn::If:
            - CreateS3BucketStackCondition
            - Fn::GetAtt:
                - S3BucketStack
                - Outputs.S3BucketName
            - Ref: S3BucketName
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/LifeCycleScriptStack
    Condition: CreateLifeCycleScriptStackCondition
  SageMakerIAMRoleStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/sagemaker-iam-role-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        S3BucketName:
          Fn::If:
            - CreateS3BucketStackCondition
            - Fn::GetAtt:
                - S3BucketStack
                - Outputs.S3BucketName
            - Ref: S3BucketName
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/SageMakerIAMRoleStack
    Condition: CreateSageMakerIAMRoleStackCondition
  HelmChartStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/helm-chart-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        HelmRepoUrl:
          Ref: HelmRepoUrl
        HelmRepoPath:
          Ref: HelmRepoPath
        Namespace:
          Ref: Namespace
        HelmRelease:
          Ref: HelmRelease
        HelmOperators:
          Ref: HelmOperators
        CustomResourceS3Bucket:
          Fn::Sub: aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}
        EKSClusterName:
          Fn::If:
            - CreateEKSClusterStackCondition
            - Fn::GetAtt:
                - EKSClusterStack
                - Outputs.EKSClusterName
            - Ref: EKSClusterName
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/HelmChartStack
    Condition: CreateHelmChartStackCondition
  HyperPodClusterStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/hyperpod-cluster-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        HelmChartStatus:
          Fn::If:
            - CreateHelmChartStackCondition
            - Fn::GetAtt:
                - HelmChartStack
                - Outputs.HelmChartDeploymentComplete
            - HelmChartNotRequired
        HyperPodClusterName:
          Ref: HyperPodClusterName
        NodeRecovery:
          Ref: NodeRecovery
        EKSClusterName:
          Fn::If:
            - CreateEKSClusterStackCondition
            - Fn::GetAtt:
                - EKSClusterStack
                - Outputs.EKSClusterName
            - Ref: EKSClusterName
        SecurityGroupIds:
          Fn::If:
            - CreateSecurityGroupStackCondition
            - Fn::GetAtt:
                - SecurityGroupStack
                - Outputs.SecurityGroupId
            - Ref: SecurityGroupIds
        PrivateSubnetIds:
          Fn::If:
            - CreatePrivateSubnetStackCondition
            - Fn::GetAtt:
                - PrivateSubnetStack
                - Outputs.PrivateSubnetIds
            - Ref: PrivateSubnetIds
        CustomResourceS3Bucket:
          Fn::Sub: aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}
        SageMakerIAMRoleName:
          Fn::If:
            - CreateSageMakerIAMRoleStackCondition
            - Fn::GetAtt:
                - SageMakerIAMRoleStack
                - Outputs.SageMakerIAMRoleName
            - Ref: SageMakerIAMRoleName
        S3BucketName:
          Fn::If:
            - CreateS3BucketStackCondition
            - Fn::GetAtt:
                - S3BucketStack
                - Outputs.S3BucketName
            - Ref: S3BucketName
        OnCreatePath:
          Fn::If:
            - CreateS3BucketStackCondition
            - on_create.sh
            - Ref: OnCreatePath
        InstanceGroupSettings1:
          Ref: InstanceGroupSettings1
        InstanceGroupSettings2:
          Ref: InstanceGroupSettings2
        InstanceGroupSettings3:
          Ref: InstanceGroupSettings3
        InstanceGroupSettings4:
          Ref: InstanceGroupSettings4
        InstanceGroupSettings5:
          Ref: InstanceGroupSettings5
        InstanceGroupSettings6:
          Ref: InstanceGroupSettings6
        InstanceGroupSettings7:
          Ref: InstanceGroupSettings7
        InstanceGroupSettings8:
          Ref: InstanceGroupSettings8
        InstanceGroupSettings9:
          Ref: InstanceGroupSettings9
        InstanceGroupSettings10:
          Ref: InstanceGroupSettings10
        InstanceGroupSettings11:
          Ref: InstanceGroupSettings11
        InstanceGroupSettings12:
          Ref: InstanceGroupSettings12
        InstanceGroupSettings13:
          Ref: InstanceGroupSettings13
        InstanceGroupSettings14:
          Ref: InstanceGroupSettings14
        InstanceGroupSettings15:
          Ref: InstanceGroupSettings15
        InstanceGroupSettings16:
          Ref: InstanceGroupSettings16
        InstanceGroupSettings17:
          Ref: InstanceGroupSettings17
        InstanceGroupSettings18:
          Ref: InstanceGroupSettings18
        InstanceGroupSettings19:
          Ref: InstanceGroupSettings19
        InstanceGroupSettings20:
          Ref: InstanceGroupSettings20
        RigSettings1:
          Ref: RigSettings1
        RigSettings2:
          Ref: RigSettings2
        RigSettings3:
          Ref: RigSettings3
        RigSettings4:
          Ref: RigSettings4
        RigSettings5:
          Ref: RigSettings5
        RigSettings6:
          Ref: RigSettings6
        RigSettings7:
          Ref: RigSettings7
        RigSettings8:
          Ref: RigSettings8
        RigSettings9:
          Ref: RigSettings9
        RigSettings10:
          Ref: RigSettings10
        RigSettings11:
          Ref: RigSettings11
        RigSettings12:
          Ref: RigSettings12
        RigSettings13:
          Ref: RigSettings13
        RigSettings14:
          Ref: RigSettings14
        RigSettings15:
          Ref: RigSettings15
        RigSettings16:
          Ref: RigSettings16
        RigSettings17:
          Ref: RigSettings17
        RigSettings18:
          Ref: RigSettings18
        RigSettings19:
          Ref: RigSettings19
        RigSettings20:
          Ref: RigSettings20
        Tags:
          Ref: Tags
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/HyperPodClusterStack
    Condition: CreateHyperPodClusterStackCondition
  FsxStack:
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL:
        Fn::Sub: https://aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}.s3.${AWS::Region}.amazonaws.com/templates/fsx-template.yaml
      Parameters:
        ResourceNamePrefix:
          Ref: ResourceNamePrefix
        HelmChartStatus:
          Fn::If:
            - CreateHelmChartStackCondition
            - Fn::GetAtt:
                - HelmChartStack
                - Outputs.HelmChartDeploymentComplete
            - HelmChartNotRequired
        EKSClusterName:
          Fn::If:
            - CreateEKSClusterStackCondition
            - Fn::GetAtt:
                - EKSClusterStack
                - Outputs.EKSClusterName
            - Ref: EKSClusterName
        CustomResourceS3Bucket:
          Fn::Sub: aws-sagemaker-hyperpod-cluster-setup-${AWS::Region}-${Stage}
        PrivateSubnetIds:
          Fn::If:
            - CreatePrivateSubnetStackCondition
            - Fn::GetAtt:
                - PrivateSubnetStack
                - Outputs.PrivateSubnetIds
            - Ref: PrivateSubnetIds
        FsxSubnetId:
          Ref: FsxSubnetId
        FsxAvailabilityZone:
          Ref: FsxAvailabilityZone
        SecurityGroupIds:
          Fn::If:
            - CreateSecurityGroupStackCondition
            - Fn::GetAtt:
                - SecurityGroupStack
                - Outputs.SecurityGroupId
            - Ref: SecurityGroupIds
        PerUnitStorageThroughput:
          Ref: PerUnitStorageThroughput
        DataCompressionType:
          Ref: DataCompressionType
        FileSystemTypeVersion:
          Ref: FileSystemTypeVersion
        StorageCapacity:
          Ref: StorageCapacity
        FsxFileSystemId:
          Ref: FsxFileSystemId
    Metadata:
      aws:cdk:path: MainEksBasedCfnTemplate/FsxStack
    Condition: CreateFsxStackCondition
Outputs:
  OutputVpcId:
    Value:
      Fn::GetAtt:
        - VPCStack
        - Outputs.VpcId
    Condition: CreateVPCStackCondition
  OutputPrivateSubnetIds:
    Value:
      Fn::GetAtt:
        - PrivateSubnetStack
        - Outputs.PrivateSubnetIds
    Condition: CreatePrivateSubnetStackCondition
  OutputSecurityGroupId:
    Value:
      Fn::GetAtt:
        - SecurityGroupStack
        - Outputs.SecurityGroupId
    Condition: CreateSecurityGroupStackCondition
  OutputEKSClusterArn:
    Value:
      Fn::GetAtt:
        - EKSClusterStack
        - Outputs.EKSClusterArn
    Condition: CreateEKSClusterStackCondition
  OutputEKSClusterName:
    Value:
      Fn::GetAtt:
        - EKSClusterStack
        - Outputs.EKSClusterName
    Condition: CreateEKSClusterStackCondition
  OutputSageMakerIAMRoleArn:
    Value:
      Fn::GetAtt:
        - SageMakerIAMRoleStack
        - Outputs.SageMakerIAMRoleArn
    Condition: CreateSageMakerIAMRoleStackCondition
  OutputS3BucketName:
    Value:
      Fn::GetAtt:
        - S3BucketStack
        - Outputs.S3BucketName
    Condition: CreateS3BucketStackCondition
  OutputHyperPodClusterName:
    Value:
      Fn::GetAtt:
        - HyperPodClusterStack
        - Outputs.HyperPodClusterName
    Condition: CreateHyperPodClusterStackCondition
  OutputHyperPodClusterArn:
    Value:
      Fn::GetAtt:
        - HyperPodClusterStack
        - Outputs.HyperPodClusterArn
    Condition: CreateHyperPodClusterStackCondition
"""