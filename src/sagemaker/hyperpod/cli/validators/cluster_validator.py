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
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from sagemaker.hyperpod.cli.utils import setup_logger
from sagemaker.hyperpod.cli.validators.validator import (
    Validator,
)

logger = setup_logger(__name__)


class ClusterValidator(Validator):
    def __init__(self):
        super().__init__()

    def validate_cluster_and_get_eks_arn(
        self, cluster_name: str, sm_client: boto3.client
    ) -> Optional[str]:
        try:
            hp_cluster_details = sm_client.describe_cluster(ClusterName=cluster_name)
            if (
                "Orchestrator" not in hp_cluster_details
                or "Eks" not in hp_cluster_details["Orchestrator"]
            ):
                logger.warning(
                    f"HyperPod cluster {cluster_name} Orchestrator not exist or is not Eks."
                )
                return None
            return hp_cluster_details["Orchestrator"]["Eks"]["ClusterArn"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.error(f"HyperPod cluster {cluster_name} not found.")
            else:
                logger.error(f"Validate HyperPod cluster {cluster_name} error: {e}")
            return None
        except Exception as e:
            logger.error(f"Validate HyperPod cluster {cluster_name} error: {e}")
            return None
