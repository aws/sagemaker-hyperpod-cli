
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Any


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

