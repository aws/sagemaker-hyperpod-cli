import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

from hyperpod_cli.utils import setup_logger

logger = setup_logger(__name__)


class Validator:
    def __init__(self):
        return

    def validate(self):
        """
        Abstract validate method to be implemented in subclasses.
        """
        return NotImplementedError()

    def validate_aws_credential(self, session: boto3.Session) -> bool:
        """
        Validate AWS credentials to ensure AWS credentials configured
        a valida credential exist in current session

        Returns:
            bool: True aws credentials are valid, False otherwise.
        """
        try:
            # Check if credentials are available
            credentials = session.get_credentials()
            if not credentials:
                logger.error("No AWS credentials found. Please configure your AWS credentials.")
                return False

            # Get an STS client to check the credentials
            sts = session.client("sts")

            # Call get_caller_identity to validate credentials
            sts.get_caller_identity()

            logger.debug("AWS credentials are valid.")
            return True
        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"No AWS credentials or partial AWS credentials provided: {e}")
            return False
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ExpiredToken":
                logger.error("AWS credentials have expired. Please refresh your AWS " "credentials")
            else:
                logger.error(f"Get credentials AWS client error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error to get AWS credentials: {e}")
            return False
