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
from typing import Optional, Literal, Dict, Any, List

# reuse the nested types
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model,
    SageMakerEndpoint,
    Server,
    TlsConfig,
    CustomCertificateConfig,
    Validations,
    IntelligentRoutingSpec,
    KvCacheSpec,
    L2CacheSpec,
    LoadBalancer,
    AutoScalingSpec,
    Metrics,
    ModelMetrics,
    EnvironmentVariables,
    DataCapture,
    DnsConfig,
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint
from sagemaker.hyperpod.common.config.metadata import Metadata


class FlatHPJumpStartEndpoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    namespace: Optional[str] = Field(
        default=None, description="Kubernetes namespace", min_length=1
    )

    accept_eula: bool = Field(
        False,
        alias="accept_eula",
        description="Whether model terms of use have been accepted",
    )

    metadata_name: Optional[str] = Field(
        None,
        alias="metadata_name",
        description="Name of the jumpstart endpoint object",
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    model_id: str = Field(
        ...,
        alias="model_id",
        description="Unique identifier of the model within the hub",
        min_length=1,
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    model_version: Optional[str] = Field(
        None,
        alias="model_version",
        description="Semantic version of the model to deploy (e.g. 1.0.0)",
        min_length=5,
        max_length=14,
        pattern=r"^\d{1,4}\.\d{1,4}\.\d{1,4}$",
    )

    instance_type: str = Field(
        ...,
        alias="instance_type",
        description="EC2 instance type for the inference server",
        pattern=r"^ml\..*",
    )

    accelerator_partition_type: Optional[str] = Field(
        None, 
        alias="accelerator_partition_type", 
        description="MIG profile to use for GPU partitioning",
        pattern=r"^mig-.*$",
    )

    accelerator_partition_validation: Optional[bool] = Field(
        True,
        alias="accelerator_partition_validation",
        description="Enable MIG validation for GPU partitioning. Default is true."
    )

    endpoint_name: Optional[str] = Field(
        None,
        alias="endpoint_name",
        description="Name of SageMaker endpoint; empty string means no creation",
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )
    tls_certificate_output_s3_uri: Optional[str] = Field(
        None,
        alias="tls_certificate_output_s3_uri",
        description="S3 URI to write the TLS certificate",
        pattern=r"^s3://([^/]+)/?(.*)$",
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

    # Intelligent Routing
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

    # KV Cache
    enable_l1_cache: Optional[bool] = Field(
        None, alias="enable_l1_cache", description="Enable L1 cache (CPU offloading)"
    )
    enable_l2_cache: Optional[bool] = Field(
        None, alias="enable_l2_cache", description="Enable L2 cache"
    )
    l2_cache_backend: Optional[str] = Field(
        None, alias="l2_cache_backend", description="L2 cache backend type"
    )
    l2_cache_local_url: Optional[str] = Field(
        None, alias="l2_cache_local_url", description="L2 cache URL to local storage"
    )
    cache_config_file: Optional[str] = Field(
        None, alias="cache_config_file", description="KV cache configuration file path"
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

    # Replicas
    replicas: Optional[int] = Field(
        1, alias="replicas", description="Number of inference server replicas. Default 1."
    )

    # Max deploy time
    max_deploy_time_in_seconds: Optional[int] = Field(
        3600, alias="max_deploy_time_in_seconds",
        description="Maximum deployment time in seconds. Defaults to 3600.",
    )

    # Environment variables
    env: Optional[Dict[str, str]] = Field(
        None, alias="env",
        description="Map of environment variable names to their values",
    )

    # Metrics
    metrics_enabled: Optional[bool] = Field(
        None, alias="metrics_enabled", description="Enable metrics collection"
    )
    metrics_scrape_interval_seconds: Optional[int] = Field(
        None, alias="metrics_scrape_interval_seconds",
        description="Scrape interval in seconds for metrics collection",
    )
    model_metrics_path: Optional[str] = Field(
        None, alias="model_metrics_path", description="Path where the model exposes metrics"
    )
    model_metrics_port: Optional[int] = Field(
        None, alias="model_metrics_port", description="Port where the model exposes metrics"
    )

    # Model sub-fields
    additional_configs: Optional[Dict[str, str]] = Field(
        None, alias="additional_configs", description="Additional model configs as key-value pairs"
    )
    gated_model_download_role: Optional[str] = Field(
        None, alias="gated_model_download_role",
        description="IAM role ARN for downloading gated models",
    )
    model_hub_name: Optional[str] = Field(
        None, alias="model_hub_name", description="Name of the model hub"
    )

    # Server execution role
    execution_role: Optional[str] = Field(
        None, alias="execution_role",
        description="IAM role ARN for deploying and managing the inference server",
    )

    # Full autoScalingSpec JSON override
    auto_scaling_spec: Optional[Dict[str, Any]] = Field(
        None, alias="auto_scaling_spec",
        description="Full autoScalingSpec JSON for autoscaling configuration",
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
    def validate_name(self):
        if not self.metadata_name and not self.endpoint_name:
            raise ValueError("Either metadata_name or endpoint_name must be provided")
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

    def to_domain(self) -> HPJumpStartEndpoint:
        if self.endpoint_name and not self.metadata_name:
            self.metadata_name = self.endpoint_name

        metadata = Metadata(name=self.metadata_name, namespace=self.namespace)

        model = Model(
            accept_eula=self.accept_eula,
            model_id=self.model_id,
            model_version=self.model_version,
            additional_configs=[{"name": k, "value": v} for k, v in self.additional_configs.items()] if self.additional_configs else None,
            gated_model_download_role=self.gated_model_download_role,
            model_hub_name=self.model_hub_name,
        )
        validations = Validations(
            accelerator_partition_validation=self.accelerator_partition_validation,
        )
        server = Server(
            instance_type=self.instance_type,
            accelerator_partition_type=self.accelerator_partition_type,
            validations=validations,
            execution_role=self.execution_role,
        )
        sage_ep = SageMakerEndpoint(name=self.endpoint_name)
        tls = TlsConfig(
            tls_certificate_output_s3_uri=self.tls_certificate_output_s3_uri,
            custom_certificate_config=CustomCertificateConfig(
                acm_arn=self.custom_certificate_acm_arn,
                domain_name=self.custom_certificate_domain_name,
            ) if self.custom_certificate_acm_arn and self.custom_certificate_domain_name else None,
        )

        # Build intelligent routing spec
        intelligent_routing_spec = None
        if self.intelligent_routing_enabled is not None:
            intelligent_routing_spec = IntelligentRoutingSpec(
                enabled=self.intelligent_routing_enabled,
                routing_strategy=self.routing_strategy,
            )

        # Build KV cache spec
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

        # Build env vars
        env_vars = None
        if self.env:
            env_vars = [EnvironmentVariables(name=k, value=v) for k, v in self.env.items()]

        # Build metrics
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

        # Build autoScalingSpec from JSON
        auto_scaling_spec = AutoScalingSpec(**self.auto_scaling_spec) if self.auto_scaling_spec else None

        # Build DNS config
        dns_config = None
        if self.dns_hosted_zone_id:
            dns_config = DnsConfig(hosted_zone_id=self.dns_hosted_zone_id)

        # Build data capture from JSON
        data_capture = DataCapture(**self.data_capture) if self.data_capture else None

        return HPJumpStartEndpoint(
            metadata=metadata,
            model=model,
            server=server,
            sage_maker_endpoint=sage_ep,
            tls_config=tls,
            intelligent_routing_spec=intelligent_routing_spec,
            kv_cache_spec=kv_cache_spec,
            load_balancer=load_balancer,
            replicas=self.replicas,
            max_deploy_time_in_seconds=self.max_deploy_time_in_seconds,
            environment_variables=env_vars,
            metrics=metrics,
            auto_scaling_spec=auto_scaling_spec,
            dns_config=dns_config,
            data_capture=data_capture,
        )
