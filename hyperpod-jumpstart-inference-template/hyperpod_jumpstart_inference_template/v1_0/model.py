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
from pydantic import BaseModel, Field, constr
from typing import Optional

# reuse the nested types
from sagemaker.hyperpod.inference.config.hp_jumpstart_endpoint_config import (
    Model,
    SageMakerEndpoint,
    Server,
    TlsConfig,
)
from sagemaker.hyperpod.inference.hp_jumpstart_endpoint import HPJumpStartEndpoint

class FlatHPJumpStartEndpoint(BaseModel):
    accept_eula: bool = Field(
        False, alias="accept_eula", description="Whether model terms of use have been accepted"
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

    endpoint_name: Optional[str] = Field(
        "",
        alias="endpoint_name",
        description="Name of SageMaker endpoint; empty string means no creation",
        max_length=63,
        pattern=r"^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$",
    )

    tls_certificate_output_s3_uri: Optional[str] = Field(
        None,
        alias="tls_certificate_output_s3_uri",
        description="S3 URI to write the TLS certificate (optional)",
        pattern=r"^s3://([^/]+)/?(.*)$",
    )

    def to_domain(self) -> HPJumpStartEndpoint:
        # Build nested domain (pydantic) objects
        model = Model(
            accept_eula=self.accept_eula,
            model_id=self.model_id,
            model_version=self.model_version,
        )
        server = Server(
            instance_type=self.instance_type,
        )
        sage_ep = SageMakerEndpoint(name=self.endpoint_name)
        tls = (
            TlsConfig(tls_certificate_output_s3_uri=self.tls_certificate_output_s3_uri)
        )
        return HPJumpStartEndpoint(
            model=model,
            server=server,
            sage_maker_endpoint=sage_ep,
            tls_config=tls,
        )
