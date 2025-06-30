from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union, Literal

from sagemaker.hyperpod.inference.config.hp_endpoint_config import (
    Metrics,
    FsxStorage,
    S3Storage,
    ModelSourceConfig,
    TlsConfig,
    EnvironmentVariables,
    ModelInvocationPort,
    ModelVolumeMount,
    Resources,
    Worker,
)
from sagemaker.hyperpod.inference.hp_endpoint import HPEndpoint

class FlatHPEndpoint(BaseModel):
    # endpoint_name
    endpoint_name: Optional[str] = Field(
        "",
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

    instance_type: str = Field(
        ...,
        alias="instance_type",
        description="EC2 instance type for the inference server",
        pattern=r"^ml\..*",
    )

    # metrics.*
    metrics_enabled: Optional[bool] = Field(
        False, alias="metrics_enabled",
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
    model_source_type: Literal["fsx", "s3"] = Field(
        ..., alias="model_source_type",
        description="Source type: fsx or s3",
    )
    model_location: Optional[str] = Field(
        None, alias="model_location",
        description="Specific model data location",
    )
    prefetch_enabled: Optional[bool] = Field(
        False, alias="prefetch_enabled",
        description="Whether to pre-fetch model data",
    )

    # tls_config
    tls_output_s3_uri: Optional[str] = Field(
        None,
        alias="tls_output_s3_uri",
        description="S3 URI for TLS certificate output",
        pattern=r"^s3://([^/]+)/?(.*)$",
    )

    # worker.*
    image_uri: str = Field(
        ..., alias="image_uri",
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
        ..., alias="model_volume_mount_name",
        description="Name of the model volume mount",
    )

    # FSXStorage
    fsx_dns_name: Optional[str] = Field(
        None,
        alias="fsx_dns_name",
        description="FSX File System DNS Name",
    )
    fsx_file_system_id: Optional[str] = Field(
        ...,  
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
        ..., 
        alias="s3_bucket_name",
        description="S3 bucket location",
    )
    s3_region: Optional[str] = Field(
        ..., 
        alias="s3_region",
        description="S3 bucket region",
    )

    # Resources
    resources_limits: Optional[Dict[str, Union[int,str]]] = Field(
        None,
        alias="resources_limits",
        description="Resource limits for the worker",
    )
    resources_requests: Optional[Dict[str, Union[int,str]]] = Field(
        None,
        alias="resources_requests",
        description="Resource requests for the worker",
    )

    def to_domain(self) -> HPEndpoint:
        env_vars = None
        if self.env:
            env_vars = [
                EnvironmentVariables(name=k, value=v)
                for k, v in self.env.items()
            ]
        # nested metrics
        metrics = Metrics(
            enabled=self.metrics_enabled,
        )

        # Validate storage choice and build nested storage config
        if self.model_source_type == "s3":
            s3 = S3Storage(
                bucket_name=self.s3_bucket_name,
                region=self.s3_region,
            )
            fsx = None
        elif self.model_source_type == "fsx":
            fsx = FsxStorage(
                dns_name=self.fsx_dns_name,
                file_system_id=self.fsx_file_system_id,
                mount_name=self.fsx_mount_name,
            )
            s3 = None
        else:
            raise ValueError(f"Unsupported model_source_type: {self.model_source_type}")

        source = ModelSourceConfig(
            model_location=self.model_location,
            model_source_type=self.model_source_type,
            prefetch_enabled=self.prefetch_enabled,
            s3_storage=s3,
            fsx_storage=fsx,
        )

        # nested TLS
        tls = TlsConfig(tls_certificate_output_s3_uri=self.tls_output_s3_uri)
        # nested worker
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
        worker = Worker(
            environment_variables=env_vars,
            image=self.image_uri,
            model_invocation_port=invocation_port,
            model_volume_mount=volume_mount,
            resources=resources,
        )
        return HPEndpoint(
            endpoint_name=self.endpoint_name,
            instance_type=self.instance_type,
            **({"metrics": metrics} if self.metrics_enabled else {}),
            model_name=self.model_name,
            model_source_config=source,
            model_version=self.model_version,
            tls_config=tls,
            worker=worker,
        )
