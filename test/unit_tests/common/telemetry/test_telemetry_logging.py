import pytest
from unittest.mock import patch, MagicMock
import subprocess
from typing import Tuple

# Import your module
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    get_region_and_account_from_current_context,
    _send_telemetry_request,
    _hyperpod_telemetry_emitter,
    DEFAULT_AWS_REGION,
)

# Test data
MOCK_CONTEXTS = {
    "eks_arn": "arn:aws:eks:us-west-2:123456789012:cluster/my-cluster",
    "simple": "cluster-123456789012-us-east-1",
    "invalid": "invalid-context",
    "partial": "cluster-us-west-2-invalid",
}

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_requests():
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.mark.parametrize("context,expected", [
    (MOCK_CONTEXTS["eks_arn"], ("us-west-2", "123456789012")),
    (MOCK_CONTEXTS["simple"], ("us-east-1", "123456789012")),
    (MOCK_CONTEXTS["invalid"], (DEFAULT_AWS_REGION, "unknown")),
    (MOCK_CONTEXTS["partial"], ("us-west-2", "unknown")),
])
def test_get_region_and_account_from_current_context(mock_subprocess, context, expected):
    # Setup mock
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout=context
    )

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
    with patch('sagemaker.hyperpod.common.telemetry.telemetry_logging.get_region_and_account_from_current_context') as mock:
        mock.return_value = ("us-west-2", "123456789012")
        yield mock

def test_send_telemetry_request(mock_get_region_account, mock_requests):
    # Test successful telemetry request
    _send_telemetry_request(
        status=1,
        feature_list=[1],
        session=None,
        extra_info="test"
    )

    # Verify request was made
    assert mock_requests.called

def test_send_telemetry_request_failure(mock_get_region_account, mock_requests):
    # Setup mock to simulate failure
    mock_requests.side_effect = Exception("Request failed")

    # Test
    _send_telemetry_request(
        status=1,
        feature_list=[1],
        session=None,
        extra_info="test"
    )
    # Should not raise exception

# Test the decorator
def test_hyperpod_telemetry_emitter():
    # Create a mock function
    @_hyperpod_telemetry_emitter(feature="HYPERPOD", func_name="test_func")
    def test_function():
        return "success"

    # Mock the telemetry request
    with patch('sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request') as mock_telemetry:
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
    with patch('sagemaker.hyperpod.common.telemetry.telemetry_logging._send_telemetry_request') as mock_telemetry:
        # Test exception handling
        with pytest.raises(ValueError):
            failing_function()
        assert mock_telemetry.called

# Test invalid region handling
def test_send_telemetry_request_invalid_region(mock_get_region_account, mock_requests):
    # Setup mock to return invalid region
    mock_get_region_account.return_value = ("invalid-region", "123456789012")

    # Test
    _send_telemetry_request(
        status=1,
        feature_list=[1],
        session=None,
        extra_info="test"
    )

    # Verify no request was made due to invalid region
    assert not mock_requests.called

# Performance test
def test_get_region_and_account_performance():
    import time
    start_time = time.time()
    get_region_and_account_from_current_context()
    duration = time.time() - start_time
    assert duration < 1.0  # Should complete within 1 second
