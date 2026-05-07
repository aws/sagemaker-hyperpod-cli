# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Optional, List, Dict, Union, Literal, Any

from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    Metrics,
    ModelMetrics,
    FsxStorage,
    S3Storage,
    HuggingFaceModel,
    TokenSecretRef,
    ModelSourceConfig,
    TlsConfig,
    CustomCertificateConfig,
    EnvironmentVariables,
    ModelInvocationPort,
    ModelVolumeMount,
    Resources,
    Worker,
    Dimensions,
    AutoScalingSpec,
    CloudWatchTrigger,
    IntelligentRoutingSpec,
    KvCacheSpec,
    L2CacheSpec,
    LoadBalancer,
    Kubernetes,
    Probes,
    Probe,
    RequestLimits,
    Tags,
    NodeAffinity,
    DataCapture,
    DnsConfig,
)
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint
from sagemaker.hyperpod.common.config.metadata import Metadata


class FlatHPEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: Optional[str] = Field(
        default=None, description="Kubernetes namespace", min_length=1
    )

    metadata_name: Optional[str] = Field(
        None,
        alias="metadata_name",
        description="Name of the custom endpoint object",
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    # endpoint_name
    endpoint_name: Optional[str] = Field(
        None,
        alias="endpoint_name",
        description="Name of SageMaker endpoint; empty string means no creation",
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    # Environment variables map
    env: Optional[Dict[str, str]] = Field(
        None,
        alias="env",
        description="Map of environment variable names to their values",
    )

    instance_type: Optional[str] = Field(
        None,
        alias="instance_type",
        description="EC2 instance type for the inference server. Mutually exclusive with instance_types.",
        pattern=r"^ml\..*",
    )

    instance_types: Optional[str] = Field(
        None,
        alias="instance_types",
        description="Comma-separated list of instance types in order of preference",
    )

    # metrics.*
    metrics_enabled: Optional[bool] = Field(
        None,
        alias="metrics_enabled",
        description="Enable metrics collection",
    )

    # model_name and version
    model_name: str = Field(
        ...,
        alias="model_name",
        description="Name of model to create on SageMaker",
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    model_version: Optional[str] = Field(
        None,
        alias="model_version",
        description="Version of the model for the endpoint",
        min_length=5,
        max_length=14,
        pattern=r"^\d{1,4}\.\d{1,4}\.\d{1,4}$",
    )

    # model_source_config.*
    model_source_type: Literal["fsx", "s3", "huggingface", "kubernetesVolume"] = Field(
        ...,
        alias="model_source_type",
        description="Source type: fsx, s3, huggingface, or kubernetesVolume",
    )
    model_location: Optional[str] = Field(
        None,
        alias="model_location",
        description="Specific model data location",
    )
    prefetch_enabled: Optional[bool] = Field(
        False,
        alias="prefetch_enabled",
        description="Whether to pre-fetch model data",
    )

    # tls_config
    tls_certificate_output_s3_uri: Optional[str] = Field(
        None,
        alias="tls_certificate_output_s3_uri",
        description="S3 URI for TLS certificate output",
        pattern=r"^s3://([^/]+)/?(.*)$",
    )

    # worker.*
    image_uri: str = Field(
        ...,
        alias="image_uri",
        description="Inference server image name",
    )
    container_port: int = Field(
        ...,
        alias="container_port",
        description="Port on which the model server listens",
        ge=1,
        le=65535,
    )
    model_volume_mount_path: Optional[str] = Field(
        "/opt/ml/model",
        alias="model_volume_mount_path",
        description="Path inside container for model volume",
    )
    model_volume_mount_name: str = Field(
        ...,
        alias="model_volume_mount_name",
        description="Name of the model volume mount",
    )

    # FSXStorage
    fsx_dns_name: Optional[str] = Field(
        None,
        alias="fsx_dns_name",
        description="FSX File System DNS Name",
    )
    fsx_file_system_id: Optional[str] = Field(
        None,
        alias="fsx_file_system_id",
        description="FSX File System ID",
    )
    fsx_mount_name: Optional[str] = Field(
        None,
        alias="fsx_mount_name",
        description="FSX File System Mount Name",
    )

    # S3Storage
    s3_bucket_name: Optional[str] = Field(
        None,
        alias="s3_bucket_name",
        description="S3 bucket location",
    )
    s3_region: Optional[str] = Field(
        None,
        alias="s3_region",
        description="S3 bucket region",
    )

    # Resources
    resources_limits: Optional[Dict[str, Union[int, str]]] = Field(
        None,
        alias="resources_limits",
        description="Resource limits for the worker",
    )
    resources_requests: Optional[Dict[str, Union[int, str]]] = Field(
        None,
        alias="resources_requests",
        description="Resource requests for the worker",
    )

    # Dimensions
    dimensions: Optional[Dict[str, str]] = Field(
        None,
        alias="dimensions",
        description="CloudWatch Metric dimensions as key–value pairs",
    )

    # CloudWatch Trigger
    metric_collection_period: Optional[int] = Field(
        300, description="Defines the Period for CloudWatch query"
    )
    metric_collection_start_time: Optional[int] = Field(
        300, description="Defines the StartTime for CloudWatch query"
    )
    metric_name: Optional[str] = Field(
        None, description="Metric name to query for CloudWatch trigger"
    )
    metric_stat: Optional[str] = Field(
        "Average",
        description=(
            "Statistics metric to be used by Trigger. "
            "Defines the Stat for the CloudWatch query. Default is Average."
        ),
    )
    metric_type: Optional[Literal["Value", "Average"]] = Field(
        "Average",
        description=(
            "The type of metric to be used by HPA. "
            "`Average` – Uses average value per pod; "
            "`Value` – Uses absolute metric value."
        ),
    )
    min_value: Optional[float] = Field(
        0,
        description=(
            "Minimum metric value used in case of empty response "
            "from CloudWatch. Default is 0."
        ),
    )
    cloud_watch_trigger_name: Optional[str] = Field(
        None, description="Name for the CloudWatch trigger"
    )
    cloud_watch_trigger_namespace: Optional[str] = Field(
        None, description="AWS CloudWatch namespace for the metric"
    )
    target_value: Optional[float] = Field(
        None, description="Target value for the CloudWatch metric"
    )
    use_cached_metrics: Optional[bool] = Field(
        True,
        description=(
            "Enable caching of metric values during polling interval. "
            "Default is true."
        ),
    )

    invocation_endpoint: Optional[str] = Field(
        default="invocations",
        description=(
            "The invocation endpoint of the model server. http://<host>:<port>/ would be pre-populated based on the other fields. "
            "Please fill in the path after http://<host>:<port>/ specific to your model server."
        ),
    )

    # Intelligent Routing flattened fields
    intelligent_routing_enabled: Optional[bool] = Field(
        None,
        alias="intelligent_routing_enabled",
        description="Enable intelligent routing",
    )
    routing_strategy: Optional[
        Literal["prefixaware", "kvaware", "session", "roundrobin"]
    ] = Field(
        None,
        alias="routing_strategy",
        description="Routing strategy for intelligent routing",
    )

    # KV Cache flattened fields
    enable_l1_cache: Optional[bool] = Field(
        None,
        alias="enable_l1_cache",
        description="Enable L1 cache (CPU offloading)",
    )
    enable_l2_cache: Optional[bool] = Field(
        None,
        alias="enable_l2_cache",
        description="Enable L2 cache",
    )
    l2_cache_backend: Optional[str] = Field(
        None,
        alias="l2_cache_backend",
        description="L2 cache backend type",
    )
    l2_cache_local_url: Optional[str] = Field(
        None,
        alias="l2_cache_local_url",
        description="L2 cache URL to local storage",
    )
    cache_config_file: Optional[str] = Field(
        None,
        alias="cache_config_file",
        description="KV cache configuration file path",
    )

    # maxDeployTimeInSeconds
    max_deploy_time_in_seconds: Optional[int] = Field(
        3600,
        alias="max_deploy_time_in_seconds",
        description="Maximum deployment time in seconds. Defaults to 3600.",
    )

    # customCertificateConfig
    custom_certificate_acm_arn: Optional[str] = Field(
        None,
        alias="custom_certificate_acm_arn",
        description="ACM certificate ARN for custom TLS certificate",
        pattern=r"^arn:aws:acm:[a-z0-9-]+:[0-9]{12}:certificate/[a-fA-F0-9-]+$",
    )
    custom_certificate_domain_name: Optional[str] = Field(
        None,
        alias="custom_certificate_domain_name",
        description="Domain name for the custom TLS certificate",
        max_length=253,
        pattern=r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$",
    )

    # LoadBalancer
    load_balancer_health_check_path: Optional[str] = Field(
        None,
        alias="load_balancer_health_check_path",
        description="Health check path for the ALB target group",
    )
    load_balancer_routing_algorithm: Optional[str] = Field(
        None,
        alias="load_balancer_routing_algorithm",
        description="Routing algorithm: least_outstanding_requests or round_robin",
    )

    # RequestLimits
    max_concurrent_requests: Optional[int] = Field(
        None,
        alias="max_concurrent_requests",
        description="Maximum concurrent requests per pod for nginx sidecar proxy",
    )
    max_queue_size: Optional[int] = Field(
        None,
        alias="max_queue_size",
        description="Maximum request queue size when concurrent limit is reached",
    )

    # Kubernetes customizations
    kubernetes: Optional[Dict[str, Any]] = Field(
        None,
        alias="kubernetes",
        description="Kubernetes customizations for the inference pod (initContainers, volumes, schedulerName)",
    )

    # Replicas
    replicas: Optional[int] = Field(
        1, alias="replicas", description="Number of inference server replicas. Default 1."
    )
    initial_replica_count: Optional[int] = Field(
        None, alias="initial_replica_count",
        description="Number of desired pods. Defaults to 1.",
    )

    # Worker args/command/workingDir
    worker_args: Optional[str] = Field(
        None, alias="worker_args",
        description="Comma-separated arguments to the entrypoint",
    )
    worker_command: Optional[str] = Field(
        None, alias="worker_command",
        description="Comma-separated entrypoint command array",
    )
    working_dir: Optional[str] = Field(
        None, alias="working_dir",
        description="Working directory of the container",
    )

    # Overflow status code (requestLimits)
    overflow_status_code: Optional[int] = Field(
        None, alias="overflow_status_code",
        description="HTTP status code when request limits exceeded. Default 429.",
    )

    # Metrics sub-fields
    metrics_scrape_interval_seconds: Optional[int] = Field(
        None, alias="metrics_scrape_interval_seconds",
        description="Scrape interval in seconds for metrics collection",
    )
    model_metrics_path: Optional[str] = Field(
        None, alias="model_metrics_path",
        description="Path where the model exposes metrics",
    )
    model_metrics_port: Optional[int] = Field(
        None, alias="model_metrics_port",
        description="Port where the model exposes metrics",
    )

    # JSON flags for complex objects
    node_affinity: Optional[Dict[str, Any]] = Field(
        None, alias="node_affinity",
        description="Node affinity JSON for advanced scheduling",
    )
    tags: Optional[Dict[str, str]] = Field(
        None, alias="tags",
        description="Tags as key-value pairs to add to the SageMaker Endpoint",
    )
    probes: Optional[Dict[str, Any]] = Field(
        None, alias="probes",
        description="Container probes JSON (livenessProbe, readinessProbe, startupProbe)",
    )
    auto_scaling_spec: Optional[Dict[str, Any]] = Field(
        None, alias="auto_scaling_spec",
        description="Full autoScalingSpec JSON (overrides individual cloudwatch fields if provided)",
    )

    # HuggingFace model source fields
    huggingface_model_id: Optional[str] = Field(
        None, alias="huggingface_model_id",
        description="HuggingFace Hub model identifier in org/model format",
    )
    huggingface_commit_sha: Optional[str] = Field(
        None, alias="huggingface_commit_sha",
        description="Git commit SHA for the model revision (40-char hex)",
    )
    huggingface_token_secret_name: Optional[str] = Field(
        None, alias="huggingface_token_secret_name",
        description="Name of the K8s Secret containing the HuggingFace API token",
    )
    huggingface_token_secret_key: Optional[str] = Field(
        None, alias="huggingface_token_secret_key",
        description="Key in the K8s Secret for the HuggingFace API token",
    )

    # DNS config
    dns_hosted_zone_id: Optional[str] = Field(
        None, alias="dns_hosted_zone_id",
        description="Route53 Hosted Zone ID for DNS automation",
        pattern=r"^Z[A-Z0-9]+$",
    )

    # Data capture (JSON flag)
    data_capture: Optional[Dict[str, Any]] = Field(
        None, alias="data_capture",
        description="Data capture configuration JSON for SageMaker, LoadBalancer, and Model Pod tiers",
    )

    @model_validator(mode="after")
    def validate_model_source_config(self):
        """Validate that required fields are provided based on model_source_type"""
        if self.model_source_type == "s3":
            if not self.s3_bucket_name or not self.s3_region:
                raise ValueError(
                    "s3_bucket_name and s3_region are required when model_source_type is 's3'"
                )
        elif self.model_source_type == "fsx":
            if not self.fsx_file_system_id:
                raise ValueError(
                    "fsx_file_system_id is required when model_source_type is 'fsx'"
                )
        elif self.model_source_type == "huggingface":
            if not self.huggingface_model_id:
                raise ValueError(
                    "huggingface_model_id is required when model_source_type is 'huggingface'"
                )
        return self

    @model_validator(mode="after")
    def validate_name(self):
        if not self.metadata_name and not self.endpoint_name:
            raise ValueError("Either metadata_name or endpoint_name must be provided")
        return self

    @model_validator(mode="after")
    def validate_instance_type_fields(self):
        has_instance = self.instance_type or self.instance_types
        if self.instance_type and self.instance_types:
            raise ValueError("instance_type and instance_types are mutually exclusive")
        if self.node_affinity and has_instance:
            raise ValueError("node_affinity cannot be specified with instance_type or instance_types simultaneously")
        if not has_instance and not self.node_affinity:
            raise ValueError("Either instance_type, instance_types, or node_affinity must be provided")
        return self

    @model_validator(mode="after")
    def validate_certificate_and_dns(self):
        has_acm = self.custom_certificate_acm_arn is not None
        has_domain = self.custom_certificate_domain_name is not None
        has_dns = self.dns_hosted_zone_id is not None
        if has_acm != has_domain:
            raise ValueError(
                "custom_certificate_acm_arn and custom_certificate_domain_name must both be provided together"
            )
        if has_dns and not (has_acm and has_domain):
            raise ValueError(
                "dns_hosted_zone_id requires both custom_certificate_acm_arn and custom_certificate_domain_name"
            )
        return self

    def to_domain(self) -> HPEndpoint:
        if self.endpoint_name and not self.metadata_name:
            self.metadata_name = self.endpoint_name

        metadata = Metadata(name=self.metadata_name, namespace=self.namespace)

        env_vars = None
        if self.env:
            env_vars = [
                EnvironmentVariables(name=k, value=v) for k, v in self.env.items()
            ]

        dim_vars: list[Dimensions] = []
        if self.dimensions:
            for name, value in self.dimensions.items():
                dim_vars.append(Dimensions(name=name, value=value))

        cloud_watch_trigger = CloudWatchTrigger(
            dimensions=dim_vars,
            metric_collection_period=self.metric_collection_period,
            metric_collection_start_time=self.metric_collection_start_time,
            metric_name=self.metric_name,
            metric_stat=self.metric_stat,
            metric_type=self.metric_type,
            min_value=self.min_value,
            name=self.cloud_watch_trigger_name,
            namespace=self.cloud_watch_trigger_namespace,
            target_value=self.target_value,
            use_cached_metrics=self.use_cached_metrics,
        )

        auto_scaling_spec = AutoScalingSpec(**self.auto_scaling_spec) if self.auto_scaling_spec else AutoScalingSpec(cloud_watch_trigger=cloud_watch_trigger)

        # nested metrics
        model_metrics = None
        if self.model_metrics_path or self.model_metrics_port:
            model_metrics = ModelMetrics(
                path=self.model_metrics_path,
                port=self.model_metrics_port,
            )
        metrics = None
        if self.metrics_enabled is not None or self.metrics_scrape_interval_seconds is not None or model_metrics is not None:
            metrics = Metrics(
                enabled=self.metrics_enabled,
                metrics_scrape_interval_seconds=self.metrics_scrape_interval_seconds,
                model_metrics=model_metrics,
            )

        # Validate storage choice and build nested storage config
        if self.model_source_type == "s3":
            s3 = S3Storage(
                bucket_name=self.s3_bucket_name,
                region=self.s3_region,
            )
            fsx = None
            hf_model = None
        elif self.model_source_type == "fsx":
            fsx = FsxStorage(
                dns_name=self.fsx_dns_name,
                file_system_id=self.fsx_file_system_id,
                mount_name=self.fsx_mount_name,
            )
            s3 = None
            hf_model = None
        elif self.model_source_type == "huggingface":
            s3 = None
            fsx = None
            token_ref = None
            if self.huggingface_token_secret_name and self.huggingface_token_secret_key:
                token_ref = TokenSecretRef(
                    name=self.huggingface_token_secret_name,
                    key=self.huggingface_token_secret_key,
                )
            hf_model = HuggingFaceModel(
                model_id=self.huggingface_model_id,
                commit_sha=self.huggingface_commit_sha,
                token_secret_ref=token_ref,
            )
        elif self.model_source_type == "kubernetesVolume":
            s3 = None
            fsx = None
            hf_model = None
        else:
            raise ValueError(f"Unsupported model_source_type: {self.model_source_type}")

        source = ModelSourceConfig(
            model_location=self.model_location,
            model_source_type=self.model_source_type,
            prefetch_enabled=self.prefetch_enabled,
            s3_storage=s3,
            fsx_storage=fsx,
            hugging_face_model=hf_model,
        )

        tls = TlsConfig(
            tls_certificate_output_s3_uri=self.tls_certificate_output_s3_uri,
            custom_certificate_config=CustomCertificateConfig(
                acm_arn=self.custom_certificate_acm_arn,
                domain_name=self.custom_certificate_domain_name,
            ) if self.custom_certificate_acm_arn and self.custom_certificate_domain_name else None,
        )

        invocation_port = ModelInvocationPort(
            container_port=self.container_port,
        )
        volume_mount = ModelVolumeMount(
            mount_path=self.model_volume_mount_path,
            name=self.model_volume_mount_name,
        )
        resources = Resources(
            limits=self.resources_limits,
            requests=self.resources_requests,
        )
        request_limits = None
        if self.max_concurrent_requests is not None or self.max_queue_size is not None or self.overflow_status_code is not None:
            request_limits = RequestLimits(
                max_concurrent_requests=self.max_concurrent_requests,
                max_queue_size=self.max_queue_size,
                overflow_status_code=self.overflow_status_code,
            )

        # Parse worker args/command from comma-separated strings
        worker_args = [a.strip() for a in self.worker_args.split(",")] if self.worker_args else None
        worker_command = [c.strip() for c in self.worker_command.split(",")] if self.worker_command else None

        # Build probes from JSON
        worker_probes = Probes(**self.probes) if self.probes else None

        worker = Worker(
            environment_variables=env_vars,
            image=self.image_uri,
            model_invocation_port=invocation_port,
            model_volume_mount=volume_mount,
            resources=resources,
            request_limits=request_limits,
            args=worker_args,
            command=worker_command,
            working_dir=self.working_dir,
            probes=worker_probes,
        )
        # Build intelligent routing spec from flattened fields
        intelligent_routing_spec = None
        if self.intelligent_routing_enabled is not None:
            intelligent_routing_spec = IntelligentRoutingSpec(
                enabled=self.intelligent_routing_enabled,
                routing_strategy=self.routing_strategy,
            )

        # Build KV cache spec from flattened fields
        kv_cache_spec = None
        if any([self.enable_l1_cache, self.enable_l2_cache, self.cache_config_file]):
            l2_cache_spec = None
            if self.l2_cache_backend or self.l2_cache_local_url:
                l2_cache_spec = L2CacheSpec(
                    l2_cache_backend=self.l2_cache_backend,
                    l2_cache_local_url=self.l2_cache_local_url,
                )

            kv_cache_spec = KvCacheSpec(
                enable_l1_cache=self.enable_l1_cache,
                enable_l2_cache=self.enable_l2_cache,
                l2_cache_spec=l2_cache_spec,
                cache_config_file=self.cache_config_file,
            )

        # Build load balancer config
        load_balancer = None
        if self.load_balancer_health_check_path or self.load_balancer_routing_algorithm:
            load_balancer = LoadBalancer(
                health_check_path=self.load_balancer_health_check_path,
                routing_algorithm=self.load_balancer_routing_algorithm,
            )

        # Parse instance_types from comma-separated string
        instance_types_list = None
        if self.instance_types:
            instance_types_list = [t.strip() for t in self.instance_types.split(",")]

        # Build kubernetes config
        kubernetes = None
        if self.kubernetes:
            kubernetes = Kubernetes(**self.kubernetes)

        # Build tags
        tags_list = None
        if self.tags:
            tags_list = [Tags(name=k, value=v) for k, v in self.tags.items()]

        # Build node affinity from JSON
        node_affinity = NodeAffinity(**self.node_affinity) if self.node_affinity else None

        # Build DNS config
        dns_config = None
        if self.dns_hosted_zone_id:
            dns_config = DnsConfig(hosted_zone_id=self.dns_hosted_zone_id)

        # Build data capture from JSON
        data_capture = DataCapture(**self.data_capture) if self.data_capture else None

        return HPEndpoint(
            metadata=metadata,
            endpoint_name=self.endpoint_name,
            instance_type=self.instance_type,
            instance_types=instance_types_list,
            metrics=metrics,
            model_name=self.model_name,
            model_source_config=source,
            model_version=self.model_version,
            tls_config=tls,
            worker=worker,
            invocation_endpoint=self.invocation_endpoint,
            auto_scaling_spec=auto_scaling_spec,
            intelligent_routing_spec=intelligent_routing_spec,
            kv_cache_spec=kv_cache_spec,
            max_deploy_time_in_seconds=self.max_deploy_time_in_seconds,
            load_balancer=load_balancer,
            kubernetes=kubernetes,
            replicas=self.replicas,
            initial_replica_count=self.initial_replica_count,
            tags=tags_list,
            node_affinity=node_affinity,
            dns_config=dns_config,
            data_capture=data_capture,
        )
