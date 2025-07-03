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


class FsxStorage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dnsName: Optional[str] = Field(
        default=None, alias="dns_name", description="FSX File System DNS Name"
    )
    fileSystemId: str = Field(alias="file_system_id", description="FSX File System ID")
    mountName: Optional[str] = Field(
        default=None, alias="mount_name", description="FSX File System Mount Name"
    )


class S3Storage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucketName: str = Field(alias="bucket_name", description="S3 bucket location")
    region: str = Field(description="S3 bucket region")


class ModelSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fsxStorage: Optional[FsxStorage] = Field(default=None, alias="fsx_storage")
    modelLocation: Optional[str] = Field(
        default=None,
        alias="model_location",
        description="Sepcific location where the model data exists",
    )
    modelSourceType: Literal["fsx", "s3"] = Field(alias="model_source_type")
    prefetchEnabled: Optional[bool] = Field(
        default=False,
        alias="prefetch_enabled",
        description="In case the model seems to fit within the instance's memory (VRAM), this option can be used to pre-fetch the model to RAM and then the inference server will load to the GPU/CPU device thereafter.",
    )
    s3Storage: Optional[S3Storage] = Field(default=None, alias="s3_storage")


class Tags(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    value: str


class TlsConfig(BaseModel):
    """Configurations for TLS"""

    model_config = ConfigDict(extra="forbid")

    tlsCertificateOutputS3Uri: Optional[str] = Field(
        default=None, alias="tls_certificate_output_s3_uri"
    )


class ConfigMapKeyRef(BaseModel):
    """Selects a key of a ConfigMap."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(description="The key to select.")
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="Specify whether the ConfigMap or its key must be defined",
    )


class FieldRef(BaseModel):
    """Selects a field of the pod: supports metadata.name, metadata.namespace, `metadata.labels['<KEY>']`, `metadata.annotations['<KEY>']`, spec.nodeName, spec.serviceAccountName, status.hostIP, status.podIP, status.podIPs."""

    model_config = ConfigDict(extra="forbid")

    apiVersion: Optional[str] = Field(
        default=None,
        alias="api_version",
        description='Version of the schema the FieldPath is written in terms of, defaults to "v1".',
    )
    fieldPath: str = Field(
        alias="field_path",
        description="Path of the field to select in the specified API version.",
    )


class ResourceFieldRef(BaseModel):
    """Selects a resource of the container: only resources limits and requests (limits.cpu, limits.memory, limits.ephemeral-storage, requests.cpu, requests.memory and requests.ephemeral-storage) are currently supported."""

    model_config = ConfigDict(extra="forbid")

    containerName: Optional[str] = Field(
        default=None,
        alias="container_name",
        description="Container name: required for volumes, optional for env vars",
    )
    divisor: Optional[Union[int, str]] = Field(
        default=None,
        description='Specifies the output format of the exposed resources, defaults to "1"',
    )
    resource: str = Field(description="Required: resource to select")


class SecretKeyRef(BaseModel):
    """Selects a key of a secret in the pod's namespace"""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(
        description="The key of the secret to select from.  Must be a valid secret key."
    )
    name: Optional[str] = Field(
        default="",
        description="Name of the referent. This field is effectively required, but due to backwards compatibility is allowed to be empty. Instances of this type with an empty value here are almost certainly wrong. More info: https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#names",
    )
    optional: Optional[bool] = Field(
        default=None,
        description="Specify whether the Secret or its key must be defined",
    )


class ValueFrom(BaseModel):
    """Source for the environment variable's value. Cannot be used if value is not empty."""

    model_config = ConfigDict(extra="forbid")

    configMapKeyRef: Optional[ConfigMapKeyRef] = Field(
        default=None,
        alias="config_map_key_ref",
        description="Selects a key of a ConfigMap.",
    )
    fieldRef: Optional[FieldRef] = Field(
        default=None,
        alias="field_ref",
        description="Selects a field of the pod: supports metadata.name, metadata.namespace, `metadata.labels['<KEY>']`, `metadata.annotations['<KEY>']`, spec.nodeName, spec.serviceAccountName, status.hostIP, status.podIP, status.podIPs.",
    )
    resourceFieldRef: Optional[ResourceFieldRef] = Field(
        default=None,
        alias="resource_field_ref",
        description="Selects a resource of the container: only resources limits and requests (limits.cpu, limits.memory, limits.ephemeral-storage, requests.cpu, requests.memory and requests.ephemeral-storage) are currently supported.",
    )
    secretKeyRef: Optional[SecretKeyRef] = Field(
        default=None,
        alias="secret_key_ref",
        description="Selects a key of a secret in the pod's namespace",
    )


class EnvironmentVariables(BaseModel):
    """EnvVar represents an environment variable present in a Container."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name of the environment variable. Must be a C_IDENTIFIER."
    )
    value: Optional[str] = Field(
        default=None,
        description='Variable references $(VAR_NAME) are expanded using the previously defined environment variables in the container and any service environment variables. If a variable cannot be resolved, the reference in the input string will be unchanged. Double $$ are reduced to a single $, which allows for escaping the $(VAR_NAME) syntax: i.e. "$$(VAR_NAME)" will produce the string literal "$(VAR_NAME)". Escaped references will never be expanded, regardless of whether the variable exists or not. Defaults to "".',
    )
    valueFrom: Optional[ValueFrom] = Field(
        default=None,
        alias="value_from",
        description="Source for the environment variable's value. Cannot be used if value is not empty.",
    )


class ModelInvocationPort(BaseModel):
    """Defines the port at which the model server will listen to the invocation requests."""

    model_config = ConfigDict(extra="forbid")

    containerPort: int = Field(
        alias="container_port",
        description="Port on which the model server will be listening",
    )
    name: Optional[str] = Field(
        default="http",
        description="This is name for the port within the deployed container where the model will listen. This will be referred to by the Load Balancer Service. This must be an IANA_SVC_NAME (for eg. http) and unique within the pod.",
    )


class ModelVolumeMount(BaseModel):
    """Defines the volume where model will be loaded"""

    model_config = ConfigDict(extra="forbid")

    mountPath: Optional[str] = Field(
        default="/opt/ml/model",
        alias="mount_path",
        description="This is the path within the container where the model data will be available for the inference server to load it to GPU,CPU or other device",
    )
    name: str = Field(description="Name of the model volume mount")


class Claims(BaseModel):
    """ResourceClaim references one entry in PodSpec.ResourceClaims."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Name must match the name of one entry in pod.spec.resourceClaims of the Pod where this field is used. It makes that resource available inside a container."
    )
    request: Optional[str] = Field(
        default=None,
        description="Request is the name chosen for a request in the referenced claim. If empty, everything from the claim is made available, otherwise only the result of this request.",
    )


class Resources(BaseModel):
    """Defines the Resources in terms of CPU, GPU, Memory needed for the model to be deployed"""

    model_config = ConfigDict(extra="forbid")

    claims: Optional[List[Claims]] = Field(
        default=None,
        description="Claims lists the names of resources, defined in spec.resourceClaims, that are used by this container.  This is an alpha field and requires enabling the DynamicResourceAllocation feature gate.  This field is immutable. It can only be set for containers.",
    )
    limits: Optional[Dict[str, Union[int, str]]] = Field(
        default=None,
        description="Limits describes the maximum amount of compute resources allowed. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )
    requests: Optional[Dict[str, Union[int, str]]] = Field(
        default=None,
        description="Requests describes the minimum amount of compute resources required. If Requests is omitted for a container, it defaults to Limits if that is explicitly specified, otherwise to an implementation-defined value. Requests cannot exceed Limits. More info: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/",
    )


class Worker(BaseModel):
    """Details of the worker"""

    model_config = ConfigDict(extra="forbid")

    environmentVariables: Optional[List[EnvironmentVariables]] = Field(
        default=None,
        alias="environment_variables",
        description="List of environment variables to set in the container. Cannot be updated.",
    )
    image: str = Field(description="The name of the inference server image to be used")
    modelInvocationPort: ModelInvocationPort = Field(
        alias="model_invocation_port",
        description="Defines the port at which the model server will listen to the invocation requests.",
    )
    modelVolumeMount: ModelVolumeMount = Field(
        alias="model_volume_mount",
        description="Defines the volume where model will be loaded",
    )
    resources: Resources = Field(
        description="Defines the Resources in terms of CPU, GPU, Memory needed for the model to be deployed"
    )


class _HPEndpoint(BaseModel):
    """InferenceEndpointConfigSpec defines the desired state of InferenceEndpointConfig."""

    model_config = ConfigDict(extra="ignore")

    InitialReplicaCount: Optional[int] = Field(
        default=None,
        alias="initial_replica_count",
        description="Number of desired pods. This is a pointer to distinguish between explicit zero and not specified. Defaults to 1.",
    )
    autoScalingSpec: Optional[AutoScalingSpec] = Field(
        default=None, alias="auto_scaling_spec"
    )
    endpointName: Optional[str] = Field(
        default=None,
        alias="endpoint_name",
        description="Name used for Sagemaker Endpoint Name of sagemaker endpoint. Defaults to empty string which represents that Sagemaker endpoint will not be created.",
    )
    instanceType: str = Field(
        alias="instance_type", description="Instance Type to deploy the model on"
    )
    invocationEndpoint: Optional[str] = Field(
        default="invocations",
        alias="invocation_endpoint",
        description="The invocation endpoint of the model server. http://<host>:<port>/ would be pre-populated based on the other fields. Please fill in the path after http://<host>:<port>/ specific to your model server.",
    )
    metrics: Optional[Metrics] = Field(
        default=None, description="Configuration for metrics collection and exposure"
    )
    modelName: str = Field(
        alias="model_name",
        description="Name of model that will be created on Sagemaker",
    )
    modelSourceConfig: ModelSourceConfig = Field(alias="model_source_config")
    modelVersion: Optional[str] = Field(
        default=None,
        alias="model_version",
        description="Version of the model used in creating sagemaker endpoint",
    )
    replicas: Optional[int] = Field(
        default=1,
        description="The desired number of inference server replicas. Default 1.",
    )
    tags: Optional[List[Tags]] = Field(
        default=None,
        description="Mentions the tags to be added to the Sagemaker Endpoint",
    )
    tlsConfig: Optional[TlsConfig] = Field(
        default=None, alias="tls_config", description="Configurations for TLS"
    )
    worker: Worker = Field(description="Details of the worker")


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


class InferenceEndpointConfigStatus(BaseModel):
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
