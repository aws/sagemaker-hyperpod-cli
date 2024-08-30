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
import logging
import unittest
from io import StringIO
from unittest import mock
from unittest.mock import patch, mock_open

from hyperpod_cli.utils import (
    get_name_from_arn,
    get_sagemaker_client,
    set_logging_level,
    setup_logger,
    get_cluster_console_url,
    store_current_hyperpod_context,
)

DATA_JSON = {
    "ClusterArn": "arn:aws:sagemaker:us-west-2:205812255177:cluster/jew43eabxr86",
    "ClusterName": "hyperpod-eks-test-1723857725",
    "ClusterStatus": "InService",
    "CreationTime": "2024-08-17 01:26:35.921000+00:00",
}

DATA = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west-2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west$2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_NONE_NAME = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west-2:1234567890:cluster/test",'
    ' "ClusterName": "" ,'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_LONGER_REGION_PREFIX = (
    '{"ClusterArn": "arn:aws:sagemaker:old-west-2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_SHORT_REGION_PREFIX = (
    '{"ClusterArn": "arn:aws:sagemaker:o-west-2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_SHORT_REGION = (
    '{"ClusterArn": "arn:aws:sagemaker:us-we-2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_LONGER_REGION = (
    '{"ClusterArn": "arn:aws:sagemaker:us-northwesteast-2:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_REGION_SUFFIX = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west-y:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_LONGER_REGION_SUFFIX = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west-98789:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)

INVALID_DATA_LONGER_CLUSTER_NAME = (
    '{"ClusterArn": "arn:aws:sagemaker:us-west-98789:1234567890:cluster/test",'
    ' "ClusterName": "hyperpod-eks-test-hyperpod-eks-test-hyperpod-eks-test-hyperpod-eks-test",'
    ' "ClusterStatus": "InService",'
    ' "CreationTime": "2024-08-17 01:26:35.921000+00:00"}'
)


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
        self.assertRegex(output, r"This is an error message")

        # Check the log level
        self.assertEqual(logger.level, logging.ERROR)

        # Check the formatter
        formatter = logger.handlers[0].formatter
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertEqual(
            formatter._style._fmt,
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @patch("logging.Logger")
    @patch("logging.Handler")
    def test_set_logging_level(
        self,
        mock_handler,
        mock_logger,
    ):
        mock_logger.handlers = [mock_handler]

        # Test setting the logging level to DEBUG
        set_logging_level(mock_logger, logging.DEBUG)
        mock_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_handler.setLevel.assert_called_with(logging.DEBUG)

        # Test setting the logging level to INFO
        set_logging_level(mock_logger, logging.INFO)
        mock_logger.setLevel.assert_called_with(logging.INFO)
        mock_handler.setLevel.assert_called_with(logging.INFO)

        # Test setting the logging level to ERROR
        set_logging_level(mock_logger, logging.ERROR)
        mock_logger.setLevel.assert_called_with(logging.ERROR)
        mock_handler.setLevel.assert_called_with(logging.ERROR)

    @patch("boto3.Session")
    def test_get_sagemaker_client(self, mock_boto_session: mock.Mock):
        mock_boto_session.client.return_value = None
        get_sagemaker_client(mock_boto_session)

    def test_store_current_hyperpod_context(self):
        with patch("builtins.open") as mock_write:
            store_current_hyperpod_context(DATA_JSON)
        mock_write.assert_called_once_with("/tmp/hyperpod_current_context.json", "w")

    def test_get_cluster_console_url(self):
        mock_read = mock_open(read_data=DATA)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertEqual(
            result,
            "https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/cluster-management/hyperpod-eks-test",
        )
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_invalid_data(self):
        mock_read = mock_open(read_data=INVALID_DATA)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_longer_region_prefix(self):
        mock_read = mock_open(read_data=INVALID_DATA_LONGER_REGION_PREFIX)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_shorter_region_prefix(self):
        mock_read = mock_open(read_data=INVALID_DATA_SHORT_REGION_PREFIX)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_short_region(self):
        mock_read = mock_open(read_data=INVALID_DATA_SHORT_REGION)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_long_region(self):
        mock_read = mock_open(read_data=INVALID_DATA_LONGER_REGION)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_invalid_char_region_suffix(self):
        mock_read = mock_open(read_data=INVALID_DATA_REGION_SUFFIX)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_longer_region_suffix(self):
        mock_read = mock_open(read_data=INVALID_DATA_LONGER_REGION_SUFFIX)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_longer_cluster_name(self):
        mock_read = mock_open(read_data=INVALID_DATA_LONGER_CLUSTER_NAME)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")

    def test_get_cluster_console_url_longer_cluster_name_null(self):
        mock_read = mock_open(read_data=INVALID_DATA_NONE_NAME)
        with patch("builtins.open", mock_read):
            result = get_cluster_console_url()
        self.assertIsNone(result)
        mock_read.assert_called_once_with("/tmp/hyperpod_current_context.json", "r")
