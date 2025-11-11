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

"""
Unit tests for cluster_utils module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

from sagemaker.hyperpod.cli.cluster_utils import (
    _get_current_aws_identity,
    _check_access_entry_exists,
    validate_eks_access_before_kubeconfig_update,
)


class TestGetCurrentAwsIdentity:
    """Test cases for _get_current_aws_identity function."""

    def test_user_identity(self):
        """Test getting current AWS identity for IAM user."""
        # Mock session and STS client
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        
        # Mock STS response for IAM user
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:iam::123456789012:user/testuser'
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:user/testuser'
        assert identity_type == 'user'
        mock_session.client.assert_called_once_with('sts')
        mock_sts_client.get_caller_identity.assert_called_once()

    def test_role_identity(self):
        """Test getting current AWS identity for IAM role."""
        # Mock session and STS client
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        
        # Mock STS response for IAM role
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:iam::123456789012:role/MyRole'
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:role/MyRole'
        assert identity_type == 'role'

    def test_assumed_role_identity(self):
        """Test getting current AWS identity for assumed role."""
        # Mock session and STS client
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        
        # Mock STS response for assumed role
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/MyRole/session-name'
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:role/MyRole'
        assert identity_type == 'assumed-role'

    def test_assumed_role_identity_short_arn(self):
        """Test getting current AWS identity for assumed role with short ARN."""
        # Mock session and STS client
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        
        # Mock STS response for assumed role with short ARN (edge case)
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/MyRole'
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions - should still work but not transform the ARN
        assert arn == 'arn:aws:sts::123456789012:assumed-role/MyRole'
        assert identity_type == 'assumed-role'

    def test_unknown_identity_type(self):
        """Test getting current AWS identity for unknown identity type."""
        # Mock session and STS client
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_session.client.return_value = mock_sts_client
        
        # Mock STS response for unknown identity type
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:iam::123456789012:unknown/something'
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:unknown/something'
        assert identity_type == 'unknown'


class TestCheckAccessEntryExists:
    """Test cases for _check_access_entry_exists function."""

    def test_access_entry_exists(self):
        """Test when access entry exists for the principal."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.return_value = {
            'accessEntry': {
                'principalArn': 'arn:aws:iam::123456789012:role/MyRole',
                'username': 'my-role',
                'kubernetesGroups': ['system:masters']
            }
        }
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is True
        assert access_entry is not None
        assert access_entry['username'] == 'my-role'
        assert access_entry['kubernetesGroups'] == ['system:masters']
        assert error_msg is None
        mock_eks_client.describe_access_entry.assert_called_once_with(
            clusterName='test-cluster',
            principalArn='arn:aws:iam::123456789012:role/MyRole'
        )

    def test_access_entry_not_found(self):
        """Test when access entry does not exist for the principal."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException'}},
            operation_name='DescribeAccessEntry'
        )
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is False
        assert access_entry is None
        assert 'No access entry found for principal' in error_msg

    def test_access_denied_error(self):
        """Test when access is denied to check access entries."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDeniedException'}},
            operation_name='DescribeAccessEntry'
        )
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is False
        assert access_entry is None
        assert 'Access denied when checking access entries' in error_msg

    def test_cluster_not_found_error(self):
        """Test when EKS cluster does not exist."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.side_effect = ClientError(
            error_response={'Error': {'Code': 'ClusterNotFoundException'}},
            operation_name='DescribeAccessEntry'
        )
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is False
        assert access_entry is None
        assert "EKS cluster 'test-cluster' not found" in error_msg

    def test_other_client_error(self):
        """Test when other AWS client error occurs."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.side_effect = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
            operation_name='DescribeAccessEntry'
        )
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is False
        assert access_entry is None
        assert 'Error checking access entry: Rate exceeded' in error_msg

    def test_unexpected_exception(self):
        """Test when unexpected exception occurs."""
        # Mock EKS client
        mock_eks_client = Mock()
        mock_eks_client.describe_access_entry.side_effect = Exception('Network error')
        
        # Call function
        has_access, access_entry, error_msg = _check_access_entry_exists(
            mock_eks_client, 'test-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Assertions
        assert has_access is False
        assert access_entry is None
        assert 'Unexpected error checking access entry: Network error' in error_msg


class TestValidateEksAccessBeforeKubeconfigUpdate:
    """Test cases for validate_eks_access_before_kubeconfig_update function."""

    @patch('sagemaker.hyperpod.cli.cluster_utils._get_current_aws_identity')
    @patch('sagemaker.hyperpod.cli.cluster_utils._check_access_entry_exists')
    def test_successful_validation(self, mock_check_access, mock_get_identity):
        """Test successful EKS access validation."""
        # Mock session
        mock_session = Mock()
        mock_eks_client = Mock()
        mock_session.client.return_value = mock_eks_client
        
        # Mock identity function
        mock_get_identity.return_value = ('arn:aws:iam::123456789012:role/MyRole', 'role')
        
        # Mock access check function
        mock_check_access.return_value = (
            True,
            {
                'username': 'my-role',
                'kubernetesGroups': ['system:masters']
            },
            None
        )
        
        # Call function
        has_access, message = validate_eks_access_before_kubeconfig_update(
            mock_session, 'hyperpod-cluster', 'eks-cluster'
        )
        
        # Assertions
        assert has_access is True
        assert '✓ Access confirmed' in message
        assert 'my-role' in message
        assert 'system:masters' in message
        mock_get_identity.assert_called_once_with(mock_session)
        mock_check_access.assert_called_once_with(
            mock_eks_client, 'eks-cluster', 'arn:aws:iam::123456789012:role/MyRole'
        )

    @patch('sagemaker.hyperpod.cli.cluster_utils._get_current_aws_identity')
    @patch('sagemaker.hyperpod.cli.cluster_utils._check_access_entry_exists')
    def test_failed_validation(self, mock_check_access, mock_get_identity):
        """Test failed EKS access validation."""
        # Mock session
        mock_session = Mock()
        mock_eks_client = Mock()
        mock_session.client.return_value = mock_eks_client
        
        # Mock identity function
        mock_get_identity.return_value = ('arn:aws:iam::123456789012:role/MyRole', 'role')
        
        # Mock access check function (access denied)
        mock_check_access.return_value = (
            False,
            None,
            'No access entry found for principal: arn:aws:iam::123456789012:role/MyRole'
        )
        
        # Call function
        has_access, message = validate_eks_access_before_kubeconfig_update(
            mock_session, 'hyperpod-cluster', 'eks-cluster'
        )
        
        # Assertions
        assert has_access is False
        assert '✗ Cannot connect to EKS cluster' in message
        assert 'does not have an access entry' in message
        assert 'Contact your cluster administrator' in message
        assert 'https://docs.aws.amazon.com/cli/latest/reference/eks/create-access-entry.html' in message

    @patch('sagemaker.hyperpod.cli.cluster_utils._get_current_aws_identity')
    def test_unexpected_error(self, mock_get_identity):
        """Test handling of unexpected errors."""
        # Mock session
        mock_session = Mock()
        mock_session.client.side_effect = Exception('Unexpected error')
        
        # Mock identity function
        mock_get_identity.return_value = ('arn:aws:iam::123456789012:role/MyRole', 'role')
        
        # Call function
        has_access, message = validate_eks_access_before_kubeconfig_update(
            mock_session, 'hyperpod-cluster', 'eks-cluster'
        )
        
        # Assertions
        assert has_access is False
        assert 'Unexpected error validating EKS access' in message
        assert 'Unexpected error' in message

    def test_assumed_role_with_iam_api_success(self):
        """Test assumed role with successful IAM API call (IDC role case)."""
        # Mock session with both STS and IAM clients
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_iam_client = Mock()
        
        def mock_client(service):
            if service == 'sts':
                return mock_sts_client
            elif service == 'iam':
                return mock_iam_client
        
        mock_session.client.side_effect = mock_client
        
        # Mock STS response for IDC assumed role
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_AdministratorAccess_abc123/user-session'
        }
        
        # Mock IAM response with correct base role ARN
        mock_iam_client.get_role.return_value = {
            'Role': {
                'Arn': 'arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_AdministratorAccess_abc123'
            }
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/us-west-2/AWSReservedSSO_AdministratorAccess_abc123'
        assert identity_type == 'assumed-role'
        mock_iam_client.get_role.assert_called_once_with(RoleName='AWSReservedSSO_AdministratorAccess_abc123')

    def test_assumed_role_with_iam_api_access_denied(self):
        """Test assumed role with IAM API access denied (fallback to string replacement)."""
        # Mock session with both STS and IAM clients
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_iam_client = Mock()
        
        def mock_client(service):
            if service == 'sts':
                return mock_sts_client
            elif service == 'iam':
                return mock_iam_client
        
        mock_session.client.side_effect = mock_client
        
        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/MyRole/session-name'
        }
        
        # Mock IAM API failure (access denied)
        mock_iam_client.get_role.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
            operation_name='GetRole'
        )
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions - should fall back to string replacement
        assert arn == 'arn:aws:iam::123456789012:role/MyRole'
        assert identity_type == 'assumed-role'
        mock_iam_client.get_role.assert_called_once_with(RoleName='MyRole')

    def test_assumed_role_with_iam_api_role_not_found(self):
        """Test assumed role with IAM API role not found (fallback to string replacement)."""
        # Mock session with both STS and IAM clients
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_iam_client = Mock()
        
        def mock_client(service):
            if service == 'sts':
                return mock_sts_client
            elif service == 'iam':
                return mock_iam_client
        
        mock_session.client.side_effect = mock_client
        
        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/CrossAccountRole/session-name'
        }
        
        # Mock IAM API failure (role not found - cross-account case)
        mock_iam_client.get_role.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchEntity', 'Message': 'Role not found'}},
            operation_name='GetRole'
        )
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions - should fall back to string replacement
        assert arn == 'arn:aws:iam::123456789012:role/CrossAccountRole'
        assert identity_type == 'assumed-role'
        mock_iam_client.get_role.assert_called_once_with(RoleName='CrossAccountRole')

    def test_assumed_role_with_iam_api_unexpected_error(self):
        """Test assumed role with IAM API unexpected error (fallback to string replacement)."""
        # Mock session with both STS and IAM clients
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_iam_client = Mock()
        
        def mock_client(service):
            if service == 'sts':
                return mock_sts_client
            elif service == 'iam':
                return mock_iam_client
        
        mock_session.client.side_effect = mock_client
        
        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/MyRole/session-name'
        }
        
        # Mock IAM API unexpected error
        mock_iam_client.get_role.side_effect = Exception('Network timeout')
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions - should fall back to string replacement
        assert arn == 'arn:aws:iam::123456789012:role/MyRole'
        assert identity_type == 'assumed-role'
        mock_iam_client.get_role.assert_called_once_with(RoleName='MyRole')

    def test_assumed_role_with_custom_path_success(self):
        """Test assumed role with custom path retrieved via IAM API."""
        # Mock session with both STS and IAM clients
        mock_session = Mock()
        mock_sts_client = Mock()
        mock_iam_client = Mock()
        
        def mock_client(service):
            if service == 'sts':
                return mock_sts_client
            elif service == 'iam':
                return mock_iam_client
        
        mock_session.client.side_effect = mock_client
        
        # Mock STS response
        mock_sts_client.get_caller_identity.return_value = {
            'Arn': 'arn:aws:sts::123456789012:assumed-role/MyCustomRole/session-name'
        }
        
        # Mock IAM response with custom path
        mock_iam_client.get_role.return_value = {
            'Role': {
                'Arn': 'arn:aws:iam::123456789012:role/custom/path/MyCustomRole'
            }
        }
        
        # Call function
        arn, identity_type = _get_current_aws_identity(mock_session)
        
        # Assertions
        assert arn == 'arn:aws:iam::123456789012:role/custom/path/MyCustomRole'
        assert identity_type == 'assumed-role'
        mock_iam_client.get_role.assert_called_once_with(RoleName='MyCustomRole')

