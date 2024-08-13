import logging
import unittest
from io import StringIO
from unittest import mock
from unittest.mock import patch

from hyperpod_cli.utils import get_name_from_arn, get_sagemaker_client, log_level, setup_logger


class TestUtils(unittest.TestCase):
    def test_get_name_from_arn_success(self):
        arn = "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster"
        cluster_name = get_name_from_arn(arn)
        self.assertEqual(cluster_name, "my-cluster")

    def test_get_name_from_arn_failure(self):
        arn = "invalid-arn"
        with self.assertRaises(RuntimeError):
            get_name_from_arn(arn)

    def test_setup_logger(self):
        logger = setup_logger(__name__)
        # Capture log messages from the logger's handlers
        log_stream = StringIO()
        logger.handlers[0].stream = log_stream

        logger.debug("This is a debug message")
        logger.info("This is an info message")
        logger.warning("This is a warning message")
        logger.error("This is an error message")

        output = log_stream.getvalue()
        self.assertRegex(output, r"This is an info message")
        self.assertRegex(output, r"This is a warning message")
        self.assertRegex(output, r"This is an error message")

        # Check the log level
        self.assertEqual(logger.level, log_level)

        # Check the formatter
        formatter = logger.handlers[0].formatter
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertEqual(
            formatter._style._fmt, "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    @patch("boto3.Session")
    def test_get_sagemaker_client(self, mock_boto_session: mock.Mock):
        mock_boto_session.client.return_value = None
        get_sagemaker_client(mock_boto_session)
