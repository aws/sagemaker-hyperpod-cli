from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Union


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

    name: str


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


class JumpStartModelSpec(BaseModel):
    """JumpStartModelSpec defines the desired state of JumpStartModel."""

    model_config = ConfigDict(extra="forbid")

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
    sageMakerEndpoint: SageMakerEndpoint = Field(alias="sage_maker_endpoint")
    server: Server
    tlsConfig: Optional[TlsConfig] = Field(default=None, alias="tls_config")
