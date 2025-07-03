from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union, Literal
from sagemaker.hyperpod.common.config import *


class Dimensions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="CloudWatch Metric dimension name")
    value: str = Field(description="CloudWatch Metric dimension value")


class CloudWatchTrigger(BaseModel):
    """CloudWatch metric trigger to use for autoscaling"""

    model_config = ConfigDict(extra="forbid")

    dimensions: Optional[List[Dimensions]] = Field(
        default=None, description="Dimensions for Cloudwatch metrics"
    )
    metricCollectionPeriod: Optional[int] = Field(
        default=300,
        alias="metric_collection_period",
        description="Defines the Period for CloudWatch query",
    )
    metricCollectionStartTime: Optional[int] = Field(
        default=300,
        alias="metric_collection_start_time",
        description="Defines the StartTime for CloudWatch query",
    )
    metricName: Optional[str] = Field(
        default=None,
        alias="metric_name",
        description="Metric name to query for Cloudwatch trigger",
    )
    metricStat: Optional[str] = Field(
        default="Average",
        alias="metric_stat",
        description="Statistics metric to be used by Trigger. Used to define Stat for CloudWatch query. Default is Average.",
    )
    metricType: Optional[Literal["Value", "Average"]] = Field(
        default="Average",
        alias="metric_type",
        description="The type of metric to be used by HPA. Enum: AverageValue - Uses average value of metric per pod, Value - Uses absolute metric value",
    )
    minValue: Optional[float] = Field(
        default=0,
        alias="min_value",
        description="Minimum metric value used in case of empty response from CloudWatch. Default is 0.",
    )
    name: Optional[str] = Field(
        default=None, description="Name for the CloudWatch trigger"
    )
    namespace: Optional[str] = Field(
        default=None, description="AWS CloudWatch namespace for metric"
    )
    targetValue: Optional[float] = Field(
        default=None,
        alias="target_value",
        description="TargetValue for CloudWatch metric",
    )
    useCachedMetrics: Optional[bool] = Field(
        default=True,
        alias="use_cached_metrics",
        description="Enable caching of metric values during polling interval. Default is true",
    )


class PrometheusTrigger(BaseModel):
    """Prometheus metric trigger to use for autoscaling"""

    model_config = ConfigDict(extra="forbid")

    customHeaders: Optional[str] = Field(
        default=None,
        alias="custom_headers",
        description="Custom headers to include while querying the prometheus endpoint.",
    )
    metricType: Optional[Literal["Value", "Average"]] = Field(
        default="Average",
        alias="metric_type",
        description="The type of metric to be used by HPA. Enum: AverageValue - Uses average value of metric per pod, Value - Uses absolute metric value",
    )
    name: Optional[str] = Field(
        default=None, description="Name for the Prometheus trigger"
    )
    namespace: Optional[str] = Field(
        default=None, description="Namespace for namespaced queries"
    )
    query: Optional[str] = Field(
        default=None, description="PromQLQuery for the metric."
    )
    serverAddress: Optional[str] = Field(
        default=None,
        alias="server_address",
        description="Server address for AMP workspace",
    )
    targetValue: Optional[float] = Field(
        default=None,
        alias="target_value",
        description="Target metric value for scaling",
    )
    useCachedMetrics: Optional[bool] = Field(
        default=True,
        alias="use_cached_metrics",
        description="Enable caching of metric values during polling interval. Default is true",
    )


class AutoScalingSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cloudWatchTrigger: Optional[CloudWatchTrigger] = Field(
        default=None,
        alias="cloud_watch_trigger",
        description="CloudWatch metric trigger to use for autoscaling",
    )
    cooldownPeriod: Optional[int] = Field(
        default=300,
        alias="cooldown_period",
        description="The period to wait after the last trigger reported active before scaling the resource back to 0. Default 300 seconds.",
    )
    initialCooldownPeriod: Optional[int] = Field(
        default=300,
        alias="initial_cooldown_period",
        description="The delay before the cooldownPeriod starts after the initial creation of the ScaledObject. Default 300 seconds.",
    )
    maxReplicaCount: Optional[int] = Field(
        default=5,
        alias="max_replica_count",
        description="The maximum number of model pods to scale to. Default 5.",
    )
    minReplicaCount: Optional[int] = Field(
        default=1,
        alias="min_replica_count",
        description="The minimum number of model pods to scale down to. Default 1.",
    )
    pollingInterval: Optional[int] = Field(
        default=30,
        alias="polling_interval",
        description="This is the interval to check each trigger on. Default 30 seconds.",
    )
    prometheusTrigger: Optional[PrometheusTrigger] = Field(
        default=None,
        alias="prometheus_trigger",
        description="Prometheus metric trigger to use for autoscaling",
    )
    scaleDownStabilizationTime: Optional[int] = Field(
        default=300,
        alias="scale_down_stabilization_time",
        description="The time window to stabilize for HPA before scaling down. Default 300 seconds.",
    )
    scaleUpStabilizationTime: Optional[int] = Field(
        default=0,
        alias="scale_up_stabilization_time",
        description="The time window to stabilize for HPA before scaling up. Default 0 seconds.",
    )


class EnvironmentVariables(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: str


class ModelMetrics(BaseModel):
    """Configuration for model container metrics scraping"""

    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = Field(
        default="/metrics", description="Path where the model exposes metrics"
    )
    port: Optional[int] = Field(
        default=8080,
        description="Port where the model exposes metrics. If not specified, a default port will be used.",
    )


class Metrics(BaseModel):
    """Configuration for metrics collection and exposure"""

    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = Field(
        default=False, description="Enable metrics collection for this model deployment"
    )
    metricsScrapeIntervalSeconds: Optional[int] = Field(
        default=15,
        alias="metrics_scrape_interval_seconds",
        description="Scrape interval in seconds for metrics collection from sidecar and model container.",
    )
    modelMetrics: Optional[ModelMetrics] = Field(
        default=None,
        alias="model_metrics",
        description="Configuration for model container metrics scraping",
    )


class AdditionalConfigs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: str


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acceptEula: bool = Field(
        default=False,
        alias="accept_eula",
        description="For models that require a Model Access Config, specify True or False to indicate whether model terms of use have been accepted.",
    )
    additionalConfigs: Optional[List[AdditionalConfigs]] = Field(
        default=None, alias="additional_configs"
    )
    gatedModelDownloadRole: Optional[str] = Field(
        default=None,
        alias="gated_model_download_role",
        description="The Amazon Resource Name (ARN) of an IAM role that will be used to download gated model",
    )
    modelHubName: Optional[str] = Field(
        default="SageMakerPublicHub",
        alias="model_hub_name",
        description="The name of the model hub content. Can be an ARN or a simple name.",
    )
    modelId: str = Field(
        alias="model_id",
        description="The unique identifier of the model within the specified hub (hubContentArn).",
    )
    modelVersion: Optional[str] = Field(
        default=None,
        alias="model_version",
        description="The version of the model to deploy, in semantic versioning format (e.g., 1.0.0).",
    )


class SageMakerEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(
        default="",
        description="Name of sagemaker endpoint. Defaults to empty string which represents that Sagemaker endpoint will not be created.",
    )


class Server(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executionRole: Optional[str] = Field(
        default=None,
        alias="execution_role",
        description="The Amazon Resource Name (ARN) of an IAM role that will be used to deploy and manage the inference server",
    )
    instanceType: str = Field(
        alias="instance_type",
        description="The EC2 instance type to use for the inference server. Must be one of the supported types.",
    )


class TlsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tlsCertificateOutputS3Uri: Optional[str] = Field(
        default=None, alias="tls_certificate_output_s3_uri"
    )


class _HPJumpStartEndpoint(BaseModel):
    """Config defines the desired state of JumpStartModel."""

    model_config = ConfigDict(extra="ignore")

    autoScalingSpec: Optional[AutoScalingSpec] = Field(
        default=None, alias="auto_scaling_spec"
    )
    environmentVariables: Optional[List[EnvironmentVariables]] = Field(
        default=None,
        alias="environment_variables",
        description="Additional environment variables to be passed to the inference server. Limited to 100 key-value pairs.",
    )
    maxDeployTimeInSeconds: Optional[int] = Field(
        default=3600,
        alias="max_deploy_time_in_seconds",
        description="Maximum allowed time in seconds for the deployment to complete before timing out. Defaults to 1 hour (3600 seconds)",
    )
    metrics: Optional[Metrics] = Field(
        default=None, description="Configuration for metrics collection and exposure"
    )
    model: Model
    replicas: Optional[int] = Field(
        default=1,
        description="The desired number of inference server replicas. Default 1.",
    )
    sageMakerEndpoint: Optional[SageMakerEndpoint] = Field(
        default=None, alias="sage_maker_endpoint"
    )
    server: Server
    tlsConfig: Optional[TlsConfig] = Field(default=None, alias="tls_config")


class Conditions(BaseModel):
    """DeploymentCondition describes the state of a deployment at a certain point."""

    model_config = ConfigDict(extra="forbid")

    lastTransitionTime: Optional[str] = Field(
        default=None,
        alias="last_transition_time",
        description="Last time the condition transitioned from one status to another.",
    )
    lastUpdateTime: Optional[str] = Field(
        default=None,
        alias="last_update_time",
        description="The last time this condition was updated.",
    )
    message: Optional[str] = Field(
        default=None,
        description="A human readable message indicating details about the transition.",
    )
    reason: Optional[str] = Field(
        default=None, description="The reason for the condition's last transition."
    )
    status: str = Field(
        description="Status of the condition, one of True, False, Unknown."
    )
    type: str = Field(description="Type of deployment condition.")
    observedGeneration: Optional[int] = Field(
        default=None,
        alias="observed_generation",
        description="observedGeneration represents the .metadata.generation that the condition was set based upon. For instance, if .metadata.generation is currently 12, but the .status.conditions[x].observedGeneration is 9, the condition is out of date with respect to the current state of the instance.",
    )


class Status(BaseModel):
    """Status of the Deployment Object"""

    model_config = ConfigDict(extra="forbid")

    availableReplicas: Optional[int] = Field(
        default=None,
        alias="available_replicas",
        description="Total number of available pods (ready for at least minReadySeconds) targeted by this deployment.",
    )
    collisionCount: Optional[int] = Field(
        default=None,
        alias="collision_count",
        description="Count of hash collisions for the Deployment. The Deployment controller uses this field as a collision avoidance mechanism when it needs to create the name for the newest ReplicaSet.",
    )
    conditions: Optional[List[Conditions]] = Field(
        default=None,
        description="Represents the latest available observations of a deployment's current state.",
    )
    observedGeneration: Optional[int] = Field(
        default=None,
        alias="observed_generation",
        description="The generation observed by the deployment controller.",
    )
    readyReplicas: Optional[int] = Field(
        default=None,
        alias="ready_replicas",
        description="readyReplicas is the number of pods targeted by this Deployment with a Ready Condition.",
    )
    replicas: Optional[int] = Field(
        default=None,
        description="Total number of non-terminated pods targeted by this deployment (their labels match the selector).",
    )
    unavailableReplicas: Optional[int] = Field(
        default=None,
        alias="unavailable_replicas",
        description="Total number of unavailable pods targeted by this deployment. This is the total number of pods that are still required for the deployment to have 100% available capacity. They may either be pods that are running but not yet available or pods that still have not been created.",
    )
    updatedReplicas: Optional[int] = Field(
        default=None,
        alias="updated_replicas",
        description="Total number of non-terminated pods targeted by this deployment that have the desired template spec.",
    )


class DeploymentStatus(BaseModel):
    """Details of the native kubernetes deployment that hosts the model"""

    model_config = ConfigDict(extra="forbid")

    deploymentObjectOverallState: Optional[str] = Field(
        default=None,
        alias="deployment_object_overall_state",
        description="Overall State of the Deployment Object",
    )
    lastUpdated: str = Field(alias="last_updated", description="Last Update Time")
    message: Optional[str] = Field(
        default=None,
        description="Message populated in the root CRD while updating the status of underlying Deployment",
    )
    name: str = Field(description="Name of the Deployment Object")
    reason: Optional[str] = Field(
        default=None,
        description="Reason populated in the root CRD while updating the status of underlying Deployment",
    )
    status: Optional[Status] = Field(
        default=None, description="Status of the Deployment Object"
    )


class Sagemaker(BaseModel):
    """Status of the SageMaker endpoint"""

    model_config = ConfigDict(extra="forbid")

    configArn: Optional[str] = Field(
        default=None,
        alias="config_arn",
        description="The Amazon Resource Name (ARN) of the endpoint configuration.",
    )
    endpointArn: Optional[str] = Field(
        default=None,
        alias="endpoint_arn",
        description="The Amazon Resource Name (ARN) of the SageMaker endpoint",
    )
    modelArn: Optional[str] = Field(
        default=None,
        alias="model_arn",
        description="The ARN of the model created in SageMaker.",
    )
    state: str = Field(description="The current state of the SageMaker endpoint")


class Endpoints(BaseModel):
    """EndpointStatus contains the status of SageMaker endpoints"""

    model_config = ConfigDict(extra="forbid")

    sagemaker: Optional[Sagemaker] = Field(
        default=None, description="Status of the SageMaker endpoint"
    )


class ModelMetrics(BaseModel):
    """Status of model container metrics collection"""

    model_config = ConfigDict(extra="forbid")

    path: Optional[str] = Field(
        default=None, description="The path where metrics are available"
    )
    port: Optional[int] = Field(
        default=None, description="The port on which metrics are exposed"
    )


class MetricsStatus(BaseModel):
    """Status of metrics collection"""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(description="Whether metrics collection is enabled")
    errorMessage: Optional[str] = Field(
        default=None,
        alias="error_message",
        description="Error message if metrics collection is in error state",
    )
    metricsScrapeIntervalSeconds: Optional[int] = Field(
        default=None,
        alias="metrics_scrape_interval_seconds",
        description="Scrape interval in seconds for metrics collection from sidecar and model container.",
    )
    modelMetrics: Optional[ModelMetrics] = Field(
        default=None,
        alias="model_metrics",
        description="Status of model container metrics collection",
    )
    state: Optional[str] = Field(
        default=None, description="Current state of metrics collection"
    )


class TlsCertificate(BaseModel):
    """CertificateStatus represents the status of TLS certificates"""

    model_config = ConfigDict(extra="forbid")

    certificateARN: Optional[str] = Field(
        default=None,
        alias="certificate_arn",
        description="The Amazon Resource Name (ARN) of the ACM certificate",
    )
    certificateDomainNames: Optional[List[str]] = Field(
        default=None,
        alias="certificate_domain_names",
        description="The certificate domain names that is attached to the certificate",
    )
    certificateName: Optional[str] = Field(
        default=None,
        alias="certificate_name",
        description="The certificate name of cert manager",
    )
    importedCertificates: Optional[List[str]] = Field(
        default=None,
        alias="imported_certificates",
        description="Used for tracking the imported certificates to ACM",
    )
    issuerName: Optional[str] = Field(
        default=None, alias="issuer_name", description="The issuer name of cert manager"
    )
    lastCertExpiryTime: Optional[str] = Field(
        default=None,
        alias="last_cert_expiry_time",
        description="The last certificate expiry time",
    )
    tlsCertificateOutputS3Bucket: Optional[str] = Field(
        default=None,
        alias="tls_certificate_output_s3_bucket",
        description="S3 bucket that stores the certificate that needs to be trusted",
    )
    tlsCertificateS3Keys: Optional[List[str]] = Field(
        default=None,
        alias="tls_certificate_s3_keys",
        description="The output tls certificate S3 key that points to the .pem file",
    )


class JumpStartModelStatus(BaseModel):
    """ModelDeploymentStatus defines the observed state of ModelDeployment"""

    model_config = ConfigDict(extra="forbid")

    conditions: Optional[List[Conditions]] = Field(
        default=None,
        description="Detailed conditions representing the state of the deployment",
    )
    deploymentStatus: Optional[DeploymentStatus] = Field(
        default=None,
        alias="deployment_status",
        description="Details of the native kubernetes deployment that hosts the model",
    )
    endpoints: Optional[Endpoints] = Field(
        default=None,
        description="EndpointStatus contains the status of SageMaker endpoints",
    )
    metricsStatus: Optional[MetricsStatus] = Field(
        default=None, alias="metrics_status", description="Status of metrics collection"
    )
    observedGeneration: Optional[int] = Field(
        default=None,
        alias="observed_generation",
        description="Latest generation reconciled by controller",
    )
    replicas: Optional[int] = Field(
        default=None, description="The observed number of inference server replicas."
    )
    selector: Optional[str] = Field(
        default=None, description="LabelSelector for the deployment."
    )
    state: Optional[
        Literal[
            "DeploymentPending",
            "DeploymentInProgress",
            "DeploymentFailed",
            "DeploymentComplete",
            "DeletionPending",
            "DeletionInProgress",
            "DeletionFailed",
            "DeletionComplete",
        ]
    ] = Field(default=None, description="Current phase of the model deployment")
    tlsCertificate: Optional[TlsCertificate] = Field(
        default=None,
        alias="tls_certificate",
        description="CertificateStatus represents the status of TLS certificates",
    )
