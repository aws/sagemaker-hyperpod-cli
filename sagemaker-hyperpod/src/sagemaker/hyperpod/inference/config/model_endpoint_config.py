from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union, Literal


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


class InferenceEndpointConfigSpec(BaseModel):
    """InferenceEndpointConfigSpec defines the desired state of InferenceEndpointConfig."""

    model_config = ConfigDict(extra="forbid")

    InitialReplicaCount: Optional[int] = Field(
        default=None,
        alias="initial_replica_count",
        description="Number of desired pods. This is a pointer to distinguish between explicit zero and not specified. Defaults to 1.",
    )
    endpointName: str = Field(
        alias="endpoint_name", description="Name used for Sagemaker Endpoint"
    )
    instanceType: str = Field(
        alias="instance_type", description="Instance Type to deploy the model on"
    )
    invocationEndpoint: Optional[str] = Field(
        default="invoke",
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
