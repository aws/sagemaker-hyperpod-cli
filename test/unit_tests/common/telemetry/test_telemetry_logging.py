import pytest
from unittest.mock import patch, MagicMock, Mock
import subprocess
from typing import Tuple

# Import your module
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    get_region_and_account_from_current_context,
    _send_telemetry_request,
    _hyperpod_telemetry_emitter,
    _requests_helper,
    _construct_url,
    DEFAULT_AWS_REGION,
    FEATURE_TO_CODE,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature, Status
import requests
import logging

from src.sagemaker.hyperpod.common.telemetry.telemetry_logging import STATUS_TO_CODE

# Test data
MOCK_CONTEXTS = {
    "eks_arn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster",
    "simple": "cluster-123456789012-us-east-1",
    "invalid": "invalid-context",
    "partial": "cluster-us-west-2-invalid",
}


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_requests():
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.mark.parametrize(
    "context,expected",
    [
        (MOCK_CONTEXTS["eks_arn"], ("us-west-2", "123456789012")),
        (MOCK_CONTEXTS["simple"], ("us-east-1", "123456789012")),
        (MOCK_CONTEXTS["invalid"], (DEFAULT_AWS_REGION, "unknown")),
        (MOCK_CONTEXTS["partial"], ("us-west-2", "unknown")),
    ],
)
def test_get_region_and_account_from_current_context(
    mock_subprocess, context, expected
):
    # Setup mock
    mock_subprocess.return_value = MagicMock(returncode=0, stdout=context)

    # Test
    result = get_region_and_account_from_current_context()
    assert result == expected


def test_get_region_and_account_subprocess_failure(mock_subprocess):
    # Setup mock to simulate failure
    mock_subprocess.return_value = MagicMock(returncode=1)

    # Test
    result = get_region_and_account_from_current_context()
    assert result == (DEFAULT_AWS_REGION, "unknown")


def test_get_region_and_account_exception(mock_subprocess):
    # Setup mock to raise exception
    mock_subprocess.side_effect = Exception("Command failed")

    # Test
    result = get_region_and_account_from_current_context()
    assert result == (DEFAULT_AWS_REGION, "unknown")


@pytest.fixture
def mock_get_region_account():
    with patch(
        "sagemaker.hyperpod.common.telemetry.telemetry_logging.get_region_and_account_from_current_context"
    ) as mock:
        mock.return_value = ("us-west-2", "123456789012")
        yield mock


def test_send_telemetry_request(mock_get_region_account, mock_requests):
    # Test successful telemetry request
    _send_telemetry_request(status=1, feature_list=[1], session=None, extra_info="test")

    # Verify request was made
    assert mock_requests.called


def test_send_telemetry_request_failure(mock_get_region_account, mock_requests):
    # Setup mock to simulate failure
    mock_requests.side_effect = Exception("Request failed")

    # Test
    _send_telemetry_request(status=1, feature_list=[1], session=None, extra_info="test")
    # Should not raise exception


# Test the decorator
def test_hyperpod_telemetry_emitter():
    # Create a mock function
    @_hyperpod_telemetry_emitter(feature="HYPERPOD", func_name="test_func")
    def test_function():
        return "success"

    # Mock the telemetry request
    with patch(
        "sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request"
    ) as mock_telemetry:
        # Test successful execution
        result = test_function()
        assert result == "success"
        assert mock_telemetry.called


def test_hyperpod_telemetry_emitter_failure():
    # Create a mock function that raises an exception
    @_hyperpod_telemetry_emitter(feature="HYPERPOD", func_name="test_func")
    def failing_function():
        raise ValueError("Test error")

    # Mock the telemetry request
    with patch(
        "sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request"
    ) as mock_telemetry:
        # Test exception handling
        with pytest.raises(ValueError):
            failing_function()
        assert mock_telemetry.called


# Test invalid region handling
def test_send_telemetry_request_invalid_region(mock_get_region_account, mock_requests):
    # Setup mock to return invalid region
    mock_get_region_account.return_value = ("invalid-region", "123456789012")

    # Test
    _send_telemetry_request(status=1, feature_list=[1], session=None, extra_info="test")

    # Verify no request was made due to invalid region
    assert not mock_requests.called


def test_telemetry_decorator_details():
    with patch(
        "sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request"
    ) as mock_telemetry:

        @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "test_func")
        def sample_function():
            return "success"

        result = sample_function()

        # Verify telemetry call details
        mock_telemetry.assert_called_once()
        args = mock_telemetry.call_args[0]

        # Check status
        assert args[0] == STATUS_TO_CODE[str(Status.SUCCESS)]

        # Check feature code
        assert args[1] == [FEATURE_TO_CODE[str(Feature.HYPERPOD)]]

        # Check extra info contains required fields
        extra_info = args[5]
        assert "test_func" in extra_info
        assert "x-sdkVersion" in extra_info
        assert "x-latency" in extra_info


def test_multiple_telemetry_calls():
    with patch(
        "sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request"
    ) as mock_telemetry:

        @_hyperpod_telemetry_emitter(Feature.HYPERPOD, "test_func")
        def sample_function(succeed: bool):
            if not succeed:
                raise ValueError("Failed")
            return "success"

        # Success case
        sample_function(True)

        # Failure case
        with pytest.raises(ValueError):
            sample_function(False)

        # Verify both calls
        assert mock_telemetry.call_count == 2

        # Check success call
        success_call = mock_telemetry.call_args_list[0]
        assert success_call[0][0] == STATUS_TO_CODE[str(Status.SUCCESS)]

        # Check failure call
        failure_call = mock_telemetry.call_args_list[1]
        assert failure_call[0][0] == STATUS_TO_CODE[str(Status.FAILURE)]


# Test _requests_helper
def test_requests_helper_success():
    """Test successful request"""
    with patch("requests.get") as mock_get:
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Make request
        response = _requests_helper("https://test.com", 2)

        # Verify
        assert response == mock_response
        mock_get.assert_called_once_with("https://test.com", 2)


def test_requests_helper_with_invalid_url(caplog):
    """Test requests helper with invalid URL"""
    with patch("requests.get") as mock_get:
        # Set up the mock to raise InvalidURL
        mock_get.side_effect = requests.exceptions.InvalidURL("Invalid URL")

        # Capture logs at DEBUG level
        with caplog.at_level(logging.DEBUG):
            response = _requests_helper("invalid://url", 2)

        # Verify response is None
        assert response is None

        # Verify log message
        assert "Request exception: Invalid URL" in caplog.text


def test_construct_url_basic():
    """Test basic URL construction"""
    url = _construct_url(
        accountId="123456789012",
        region="us-west-2",
        status="SUCCESS",
        feature="TEST",
        failure_reason=None,
        failure_type=None,
        extra_info=None,
    )

    expected = (
        "https://sm-pysdk-t-us-west-2.s3.us-west-2.amazonaws.com/telemetry?"
        "x-accountId=123456789012&x-status=SUCCESS&x-feature=TEST"
    )
    assert url == expected


def test_construct_url_with_failure():
    """Test URL construction with failure information"""
    url = _construct_url(
        accountId="123456789012",
        region="us-west-2",
        status="FAILURE",
        feature="TEST",
        failure_reason="Test failed",
        failure_type="TestError",
        extra_info=None,
    )

    expected = (
        "https://sm-pysdk-t-us-west-2.s3.us-west-2.amazonaws.com/telemetry?"
        "x-accountId=123456789012&x-status=FAILURE&x-feature=TEST"
        "&x-failureReason=Test failed&x-failureType=TestError"
    )
    assert url == expected


def test_construct_url_with_extra_info():
    """Test URL construction with extra information"""
    url = _construct_url(
        accountId="123456789012",
        region="us-west-2",
        status="SUCCESS",
        feature="TEST",
        failure_reason=None,
        failure_type=None,
        extra_info="additional=info",
    )

    expected = (
        "https://sm-pysdk-t-us-west-2.s3.us-west-2.amazonaws.com/telemetry?"
        "x-accountId=123456789012&x-status=SUCCESS&x-feature=TEST"
        "&x-extra=additional=info"
    )
    assert url == expected


def test_construct_url_all_parameters():
    """Test URL construction with all parameters"""
    url = _construct_url(
        accountId="123456789012",
        region="us-west-2",
        status="FAILURE",
        feature="TEST",
        failure_reason="Test failed",
        failure_type="TestError",
        extra_info="additional=info",
    )

    expected = (
        "https://sm-pysdk-t-us-west-2.s3.us-west-2.amazonaws.com/telemetry?"
        "x-accountId=123456789012&x-status=FAILURE&x-feature=TEST"
        "&x-failureReason=Test failed&x-failureType=TestError"
        "&x-extra=additional=info"
    )
    assert url == expected
