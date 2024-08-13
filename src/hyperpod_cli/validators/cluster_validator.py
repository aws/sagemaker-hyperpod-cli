from typing import Optional

import boto3
from botocore.exceptions import ClientError

from hyperpod_cli.utils import setup_logger
from hyperpod_cli.validators.validator import Validator

logger = setup_logger(__name__)


class ClusterValidator(Validator):
    def __init__(self):
        super().__init__()

    def validate_cluster_and_get_eks_arn(
        self, cluster_name: str, sm_client: boto3.client
    ) -> Optional[str]:

        try:
            hp_cluster_details = sm_client.describe_cluster(ClusterName=cluster_name)
            if "Eks" not in hp_cluster_details["Orchestrator"]:
                logger.error(f"HyperPod cluster {cluster_name} Orchestrator is not Eks.")
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
