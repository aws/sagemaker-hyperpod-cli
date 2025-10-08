from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Any, Union
from sagemaker.hyperpod.common.utils import region_to_az_ids

class ClusterStackBase(BaseModel):
    resource_name_prefix: Optional[str] = Field("hyp-eks-stack", description="Prefix to be used for all resources. A 4-digit UUID will be added to prefix during submission")
    create_hyperpod_cluster_stack: Optional[bool] = Field(True, description="Boolean to Create HyperPod Cluster Stack")
    hyperpod_cluster_name: Optional[str] = Field("hyperpod-cluster", description="Name of SageMaker HyperPod Cluster")
    create_eks_cluster_stack: Optional[bool] = Field(True, description="Boolean to Create EKS Cluster Stack")
    kubernetes_version: Optional[str] = Field("1.31", description="The Kubernetes version")
    eks_cluster_name: Optional[str] = Field("eks-cluster", description="The name of the EKS cluster")
    create_helm_chart_stack: Optional[bool] = Field(True, description="Boolean to Create Helm Chart Stack")
    namespace: Optional[str] = Field("kube-system", description="The namespace to deploy the HyperPod Helm chart")
    helm_repo_url: str = Field("https://github.com/aws/sagemaker-hyperpod-cli.git", description="The URL of the Helm repo containing the HyperPod Helm chart (fixed default)")
    helm_repo_path: str = Field("helm_chart/HyperPodHelmChart", description="The path to the HyperPod Helm chart in the Helm repo (fixed default)")
    helm_operators: Optional[str] = Field("mlflow.enabled=true,trainingOperators.enabled=true,cluster-role-and-bindings.enabled=true,namespaced-role-and-bindings.enable=true,nvidia-device-plugin.devicePlugin.enabled=true,neuron-device-plugin.devicePlugin.enabled=true,aws-efa-k8s-device-plugin.devicePlugin.enabled=true,mpi-operator.enabled=true,health-monitoring-agent.enabled=true,deep-health-check.enabled=true,job-auto-restart.enabled=true,hyperpod-patching.enabled=true", description="The configuration of HyperPod Helm chart")
    helm_release: Optional[str] = Field("dependencies", description="The name used for Helm chart release")
    node_provisioning_mode: Optional[str] = Field("Continuous", description="Enable or disable the continuous provisioning mode. Valid values: \"Continuous\" or leave empty")
    node_recovery: Optional[str] = Field("Automatic", description="Specifies whether to enable or disable the automatic node recovery feature. Valid values: \"Automatic\", \"None\"")
    instance_group_settings: Union[List[Any], None] = Field([{"InstanceCount":1,"InstanceGroupName":"default","InstanceType":"ml.t3.medium","TargetAvailabilityZoneId":"use2-az2","ThreadsPerCore":1,"InstanceStorageConfigs":[{"EbsVolumeConfig":{"VolumeSizeInGB":500}}]}], description="List of string containing instance group configurations")
    rig_settings: Union[List[Any], None] = Field(None, description="List of string containing restricted instance group configurations")
    rig_s3_bucket_name: Optional[str] = Field(None, description="The name of the S3 bucket used to store the RIG resources")
    tags: Union[List[Any], None] = Field(None, description="Custom tags for managing the SageMaker HyperPod cluster as an AWS resource")
    create_vpc_stack: Optional[bool] = Field(True, description="Boolean to Create VPC Stack")
    vpc_id: Optional[str] = Field(None, description="The ID of the VPC you wish to use if you do not want to create a new VPC")
    vpc_cidr: Optional[str] = Field("10.192.0.0/16", description="The IP range (CIDR notation) for the VPC")
    availability_zone_ids: Union[List[str], None] = Field(None, description="List of AZs in submission region to deploy subnets in. Must be provided in YAML format starting with \"-\" below. Example: - use2-az1 for us-east-2 region")
    create_security_group_stack: Optional[bool] = Field(True, description="Boolean to Create Security Group Stack")
    security_group_id: Optional[str] = Field(None, description="The ID of the security group you wish to use in SecurityGroup substack if you do not want to create a new one")
    security_group_ids: Union[List[str], None] = Field(None, description="The security groups you wish to use for Hyperpod cluster if you do not want to create new ones")
    private_subnet_ids: Union[List[str], None] = Field(None, description="List of private subnet IDs used for HyperPod cluster if you do not want to create VPC stack")
    eks_private_subnet_ids: Union[List[str], None] = Field(None, description="List of private subnet IDs for the EKS cluster if you do not want to create VPC stack")
    nat_gateway_ids: Union[List[str], None] = Field(None, description="List of NAT Gateway IDs to route internet bound traffic if you do not want to create VPC stack")
    private_route_table_ids: Union[List[str], None] = Field(None, description="List of private route table IDs if you do not want to create VPC stack")
    create_s3_endpoint_stack: Optional[bool] = Field(True, description="Boolean to Create S3 Endpoint stack")
    enable_hp_inference_feature: Optional[bool] = Field(False, description="Boolean to enable inference operator in Hyperpod cluster")
    stage: Optional[str] = Field("prod", description="Deployment stage used in S3 bucket naming for inference operator. Valid values: \"gamma\", \"prod\"")
    custom_bucket_name: str = Field("", description="Custom S3 bucket name for templates")
    create_life_cycle_script_stack: Optional[bool] = Field(True, description="Boolean to Create Life Cycle Script Stack")
    create_s3_bucket_stack: Optional[bool] = Field(True, description="Boolean to Create S3 Bucket Stack")
    s3_bucket_name: Optional[str] = Field("s3-bucket", description="The name of the S3 bucket used to store the cluster lifecycle scripts")
    github_raw_url: str = Field("https://raw.githubusercontent.com/aws-samples/awsome-distributed-training/refs/heads/main/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config/on_create.sh", description="The raw GitHub URL for the lifecycle script (fixed default)")
    on_create_path: Optional[str] = Field("sagemaker-hyperpod-eks-bucket", description="The file name of lifecycle script")
    create_sagemaker_iam_role_stack: Optional[bool] = Field(True, description="Boolean to Create SageMaker IAM Role Stack")
    sagemaker_iam_role_name: Optional[str] = Field("create-cluster-role", description="The name of the IAM role that SageMaker will use during cluster creation to access the AWS resources on your behalf")
    create_fsx_stack: Optional[bool] = Field(True, description="Boolean to Create FSx Stack")
    fsx_subnet_id: Optional[str] = Field("", description="The subnet id that will be used to create FSx")
    fsx_availability_zone_id: Optional[str] = Field("", description="The availability zone to get subnet id that will be used to create FSx")
    per_unit_storage_throughput: Optional[int] = Field(250, description="Per unit storage throughput")
    data_compression_type: Optional[str] = Field("NONE", description="Data compression type for the FSx file system. Valid values: \"NONE\", \"LZ4\"")
    file_system_type_version: Optional[float] = Field(2.15, description="File system type version for the FSx file system")
    storage_capacity: Optional[int] = Field(1200, description="Storage capacity for the FSx file system in GiB")
    fsx_file_system_id: Optional[str] = Field("", description="Existing FSx file system ID")

    @field_validator('kubernetes_version', mode='before')
    @classmethod
    def validate_kubernetes_version(cls, v):
        if v is not None:
            return str(v)
        return v

    def to_config(self, region: str = None):
        """Convert CLI model to SDK configuration for cluster stack creation.
        
        Transforms the CLI model instance into a configuration dictionary that can be used
        to instantiate the HpClusterStack SDK class. Applies necessary transformations
        including AZ configuration, UUID generation, and field restructuring.
        
        Args:
            region (str, optional): AWS region for AZ configuration. If provided,
                automatically sets availability_zone_ids and fsx_availability_zone_id
                when not already specified.
        
        Returns:
            dict: Configuration dictionary ready for HpClusterStack instantiation.
                Contains all transformed parameters with defaults applied.
        
        Example:
            >>> cli_model = ClusterStackBase(hyperpod_cluster_name="my-cluster")
            >>> config = cli_model.to_config(region="us-west-2")
            >>> sdk_instance = HpClusterStack(**config)
        """
        import uuid
        
        # Convert model to dict and apply transformations
        config = self.model_dump(exclude_none=True)
        
        # Prepare CFN arrays from numbered fields
        instance_group_settings = []
        rig_settings = []
        for i in range(1, 21):
            ig_key = f'instance_group_settings{i}'
            rig_key = f'rig_settings{i}'
            if ig_key in config:
                instance_group_settings.append(config.pop(ig_key))
            if rig_key in config:
                rig_settings.append(config.pop(rig_key))
        
        # Add arrays to config
        if instance_group_settings:
            config['instance_group_settings'] = instance_group_settings
        if rig_settings:
            config['rig_settings'] = rig_settings
        
        # Add default AZ configuration if not provided
        if region and (not config.get('availability_zone_ids') or not config.get('fsx_availability_zone_id')):
            all_az_ids = region_to_az_ids(region)
            default_az_config =     {
                'availability_zone_ids': all_az_ids[:2],  # First 2 AZs
                'fsx_availability_zone_id': all_az_ids[0]  # First AZ
            }
            if not config.get('availability_zone_ids'):
                config['availability_zone_ids'] = default_az_config['availability_zone_ids']
            if not config.get('fsx_availability_zone_id'):
                config['fsx_availability_zone_id'] = default_az_config['fsx_availability_zone_id']
        
        # Append 4-digit UUID to resource_name_prefix
        if config.get('resource_name_prefix'):
            config['resource_name_prefix'] = f"{config['resource_name_prefix']}-{str(uuid.uuid4())[:4]}"
        
        # Set fixed defaults
        defaults = {
            'custom_bucket_name': '',
            'github_raw_url': 'https://raw.githubusercontent.com/aws-samples/awsome-distributed-training/refs/heads/main/1.architectures/7.sagemaker-hyperpod-eks/LifecycleScripts/base-config/on_create.sh',
            'helm_repo_url': 'https://github.com/aws/sagemaker-hyperpod-cli.git',
            'helm_repo_path': 'helm_chart/HyperPodHelmChart'
        }
        
        for key, default_value in defaults.items():
            if key not in config:
                config[key] = default_value
        
        return config