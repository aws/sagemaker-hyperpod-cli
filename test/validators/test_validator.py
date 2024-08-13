import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError, NoCredentialsError

from hyperpod_cli.validators.validator import Validator


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = Validator()

    def test_validate_need_implement(self):
        self.validator.validate()

    @patch("boto3.Session")
    def test_validate_aws_credential_success(self, mock_session):
        mock_session.get_credentials.return_value = True
        mock_sts_client = MagicMock()
        mock_session.client.return_value = mock_sts_client
        result = self.validator.validate_aws_credential(mock_session)
        self.assertTrue(result)

    @patch("boto3.Session")
    def test_validate_aws_credential_no_credentials(self, mock_session):
        mock_session.get_credentials.return_value = None
        result = self.validator.validate_aws_credential(mock_session)
        self.assertFalse(result)

    @patch("boto3.Session")
    def test_validate_aws_credential_no_credentials_error(self, mock_session):
        mock_session.get_credentials.side_effect = NoCredentialsError()
        result = self.validator.validate_aws_credential(mock_session)
        self.assertFalse(result)

    @patch("boto3.Session")
    def test_validate_aws_credential_expired_token_error(self, mock_session):
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "ExpiredToken"}}, "operation"
        )
        mock_session.client.return_value = mock_sts_client
        result = self.validator.validate_aws_credential(mock_session)
        self.assertFalse(result)

    @patch("boto3.Session")
    def test_validate_aws_credential_other_client_error(self, mock_session):
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = ClientError(
            {"Error": {"Code": "SomeOtherError"}}, "operation"
        )
        mock_session.client.return_value = mock_sts_client
        result = self.validator.validate_aws_credential(mock_session)
        self.assertFalse(result)

    @patch("boto3.Session")
    def test_validate_aws_credential_unexpected_error(self, mock_session):
        mock_sts_client = MagicMock()
        mock_sts_client.get_caller_identity.side_effect = Exception("Unexpected")
        mock_session.client.return_value = mock_sts_client
        result = self.validator.validate_aws_credential(mock_session)
        self.assertFalse(result)
