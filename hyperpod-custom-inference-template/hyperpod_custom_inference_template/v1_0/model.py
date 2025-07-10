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
    Dimensions,
    AutoScalingSpec,
    CloudWatchTrigger
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
    tls_certificate_output_s3_uri: Optional[str] = Field(
        None,
        alias="tls_certificate_output_s3_uri",
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

    # Dimensions
    dimensions: Optional[Dict[str, str]] = Field(
        None,
        alias="dimensions",
        description="CloudWatch Metric dimensions as key–value pairs"
    )

    # CloudWatch Trigger
    metric_collection_period: Optional[int] = Field(
        300,
        description="Defines the Period for CloudWatch query"
    )
    metric_collection_start_time: Optional[int] = Field(
        300,
        description="Defines the StartTime for CloudWatch query"
    )
    metric_name: Optional[str] = Field(
        None,
        description="Metric name to query for CloudWatch trigger"
    )
    metric_stat: Optional[str] = Field(
        "Average",
        description=(
            "Statistics metric to be used by Trigger. "
            "Defines the Stat for the CloudWatch query. Default is Average."
        )
    )
    metric_type: Optional[Literal["Value", "Average"]] = Field(
        "Average",
        description=(
            "The type of metric to be used by HPA. "
            "`Average` – Uses average value per pod; "
            "`Value` – Uses absolute metric value."
        )
    )
    min_value: Optional[float] = Field(
        0,
        description=(
            "Minimum metric value used in case of empty response "
            "from CloudWatch. Default is 0."
        )
    )
    cloud_watch_trigger_name: Optional[str] = Field(
        None,
        description="Name for the CloudWatch trigger"
    )
    cloud_watch_trigger_namespace: Optional[str] = Field(
        None,
        description="AWS CloudWatch namespace for the metric"
    )
    target_value: Optional[float] = Field(
        None,
        description="Target value for the CloudWatch metric"
    )
    use_cached_metrics: Optional[bool] = Field(
        True,
        description=(
            "Enable caching of metric values during polling interval. "
            "Default is true."
        )
    )

    invocation_endpoint: Optional[str] = Field(
        default="invocations",
        description=(
            "The invocation endpoint of the model server. "
            "http://<host>:<port>/ would be pre-populated based on the other fields. "
            "Please fill in the path after http://<host>:<port>/ specific to your model server.",
        )
    )

    def to_domain(self) -> HPEndpoint:
        env_vars = None
        if self.env:
            env_vars = [
                EnvironmentVariables(name=k, value=v)
                for k, v in self.env.items()
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

        auto_scaling_spec = AutoScalingSpec(
            cloud_watch_trigger = cloud_watch_trigger
        )

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

        tls = TlsConfig(tls_certificate_output_s3_uri=self.tls_certificate_output_s3_uri)

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
            metrics=metrics,
            model_name=self.model_name,
            model_source_config=source,
            model_version=self.model_version,
            tls_config=tls,
            worker=worker,
            invocation_endpoint=self.invocation_endpoint,
            auto_scaling_spec=auto_scaling_spec
        )
