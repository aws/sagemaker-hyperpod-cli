
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any

class _ClusterStackBase(BaseModel):
    stack_id: Optional[str] = Field(
        None,
        description="CloudFormation stack ID set after stack creation"
    )
    stack_name: Optional[str] = Field(
        None,
        description="CloudFormation stack name set after stack creation"
    )
    tags: Optional[List[Any]] = Field(
        None,
        description="Custom tags for the CloudFormation stack",
        examples=[[]]
    )
    stage: Optional[str] = Field(
        None, 
        description="Deployment stage (gamma, prod)",
        examples=["gamma", "prod"]
    )
    resource_name_prefix: Optional[str] = Field(
        None, 
        description="Prefix to be used for all resources created by this template.",
        examples=["sagemaker-hyperpod-eks"]
    )
    vpc_cidr: Optional[str] = Field(
        None, 
        description="The IP range (CIDR notation) for the VPC.",
        examples=["10.192.0.0/16"]
    )
    availability_zone_ids: Optional[str] = Field(
        None, 
        description="List of AZs to deploy subnets in (up to 5, comma separated)",
        examples=["use2-az1,use2-az2"]
    )
    vpc_id: Optional[str] = Field(
        None, 
        description="The ID of the VPC you wish to use if you do not want to create a new VPC.",
        examples=["vpc-1234567890abcdef0"]
    )
    nat_gateway_ids: Optional[str] = Field(
        None, 
        description="Comma-separated list of NAT Gateway IDs to route internet bound traffic to from the newly created private subnets.",
        examples=["nat-1234567890abcdef0"]
    )
    security_group_id: Optional[str] = Field(
        None, 
        description="The ID of the security group associated with an existing EKS cluster."
    )
    kubernetes_version: Optional[str] = Field(
        None, 
        description="The Kubernetes version to use for the EKS cluster.",
        examples=["1.31"]
    )
    eks_cluster_name: Optional[str] = Field(
        None, 
        description="The name of the newly created of preexisting EKS cluster you wish to use.",
        examples=["eks"]
    )
    eks_private_subnet_ids: Optional[str] = Field(
        None, 
        description="Comma-delimited list of private subnet IDs for the EKS cluster",
        examples=["subnet-1234567890abcdef0,subnet-1234567890abcdef0"]
    )
    security_group_ids: Optional[str] = Field(
        None, 
        description="The Id of your cluster security group.",
        examples=["sg-1234567890abcdef0"]
    )
    private_route_table_ids: Optional[str] = Field(
        None, 
        description="Comma-separated list of private route table IDs.",
        examples=["rtb-1234567890abcdef0"]
    )
    s3_bucket_name: Optional[str] = Field(
        None, 
        description="The name of the S3 bucket used to store the cluster lifecycle scripts.",
        examples=["s3-bucket"]
    )
    github_raw_url: Optional[str] = Field(
        None, 
        description="The raw GitHub URL for the lifecycle script."
    )
    helm_repo_url: Optional[str] = Field(
        None, 
        description="The URL of the Helm repo containing the HyperPod Helm chart.",
        examples=["https://github.com/aws/sagemaker-hyperpod-cli.git"]
    )
    helm_repo_path: Optional[str] = Field(
        None, 
        description="The path to the HyperPod Helm chart in the Helm repo.",
        examples=["helm_chart/HyperPodHelmChart"]
    )
    helm_operators: Optional[str] = Field(
        None, 
        description="The configuration of HyperPod Helm chart"
    )
    namespace: Optional[str] = Field(
        None, 
        description="The namespace to deploy the HyperPod Helm chart into.",
        examples=["kube-system"]
    )
    helm_release: Optional[str] = Field(
        None, 
        description="The name of the Helm release.",
        examples=["hyperpod-dependencies"]
    )
    hyperpod_cluster_name: Optional[str] = Field(
        None, 
        description="Name of SageMaker HyperPod Cluster.",
        examples=["hp-cluster"]
    )
    node_recovery: Optional[Literal["Automatic", "None"]] = Field(
        None, 
        description="Specifies whether to enable or disable the automatic node recovery feature (Automatic or None)."
    )
    sagemaker_iam_role_name: Optional[str] = Field(
        None, 
        description="The name of the IAM role that SageMaker will use to access the AWS resources on your behalf.",
        examples=["iam-role"]
    )
    private_subnet_ids: Optional[str] = Field(
        None, 
        description="Comma-separated list of private subnet IDs for EKS cluster.",
        examples=["subnet-1234567890abcdef0,subnet-1234567890abcdef0"]
    )
    on_create_path: Optional[str] = Field(
        None, 
        description="The file name of lifecycle script for the general purpose instance group. This script runs during cluster creation.",
        examples=["sagemaker-hyperpod-eks-bucket"]
    )
    instance_group_settings: Optional[str] = Field(
        None,
        description="Array of JSON strings containing instance group configurations.",
        examples=[[]]
    )
    rig_settings: Optional[str] = Field(
        None,
        description="Array of JSON strings containing restricted instance group configurations.",
        examples=[[]]
    )
    fsx_subnet_id: Optional[str] = Field(
        None, 
        description="The subnet id that will be used to create FSx"
    )
    fsx_availability_zone: Optional[str] = Field(
        None, 
        description="The availability zone to get subnet id that will be used to create FSx",
        examples=["use2-az1"]
    )
    per_unit_storage_throughput: Optional[int] = Field(
        None, 
        description="Per unit storage throughput for the FSx file system",
        examples=[250]
    )
    data_compression_type: Optional[Literal["NONE", "LZ4"]] = Field(
        None, 
        description="Data compression type for the FSx file system (NONE, LZ4)"
    )
    file_system_type_version: Optional[float] = Field(
        None, 
        description="File system type version for the FSx file system",
        examples=[2.12]
    )
    storage_capacity: Optional[int] = Field(
        None, 
        description="Storage capacity for the FSx file system in GiB",
        examples=[1200]
    )
    fsx_file_system_id: Optional[str] = Field(
        None, 
        description="Existing FSx for Lustre file system"
    )
    create_vpc_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create VPC Stack"
    )
    create_private_subnet_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create Private Subnet Stack"
    )
    create_security_group_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create Security Group Stack"
    )
    create_eks_cluster_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create EKS Cluster Stack"
    )
    create_s3_bucket_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create S3 Bucket Stack"
    )
    create_s3_endpoint_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create S3 Endpoint Stack"
    )
    create_life_cycle_script_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create Life Cycle Script Stack"
    )
    create_sagemaker_iam_role_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create SageMaker IAM Role Stack"
    )
    create_helm_chart_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create Helm Chart Stack"
    )
    create_hyperpod_cluster_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create HyperPod Cluster Stack"
    )
    create_fsx_stack: Optional[bool] = Field(
        None, 
        description="Boolean to Create FSx Stack"
    )


class ClusterStackOutput(BaseModel):
    output_vpc_id: Optional[str] = Field(
        None, 
        description="The ID of the VPC created or used by the stack"
    )
    output_private_subnet_ids: Optional[str] = Field(
        None, 
        description="Comma-separated list of private subnet IDs created or used by the stack"
    )
    output_security_group_id: Optional[str] = Field(
        None, 
        description="The ID of the security group created or used by the stack"
    )
    output_eks_cluster_arn: Optional[str] = Field(
        None, 
        description="The ARN of the EKS cluster created or used by the stack"
    )
    output_eks_cluster_name: Optional[str] = Field(
        None, 
        description="The name of the EKS cluster created or used by the stack"
    )
    output_sagemaker_iam_role_arn: Optional[str] = Field(
        None, 
        description="The ARN of the SageMaker IAM role created or used by the stack"
    )
    output_s3_bucket_name: Optional[str] = Field(
        None, 
        description="The name of the S3 bucket created or used by the stack"
    )
    output_hyperpod_cluster_name: Optional[str] = Field(
        None, 
        description="The name of the HyperPod cluster created by the stack"
    )
    output_hyperpod_cluster_arn: Optional[str] = Field(
        None, 
        description="The ARN of the HyperPod cluster created by the stack"
    )

