"""
Cluster utilities for EKS access validation and management.
"""

import logging
from typing import Optional, Tuple, Dict, Any

import boto3
import botocore
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def _get_current_aws_identity(session: boto3.Session) -> Tuple[str, str]:
    """
    Get the current AWS identity (ARN and type).
    
    Args:
        session: Boto3 session
        
    Returns:
        Tuple of (principal_arn, identity_type)
    """
    sts_client = session.client('sts')
    identity = sts_client.get_caller_identity()

    arn = identity['Arn']
    
    # Determine identity type
    if ':user/' in arn:
        identity_type = 'user'
    elif ':role/' in arn:
        identity_type = 'role'
    elif ':assumed-role/' in arn:
        identity_type = 'assumed-role'
        # For assumed roles, we need to get the base role ARN
        # arn:aws:sts::123456789012:assumed-role/MyRole/session-name
        # becomes arn:aws:iam::123456789012:role/MyRole
        parts = arn.split('/')
        if len(parts) >= 3:
            role_name = parts[1]  # Extract role name from ARN
        
            # Try IAM API first (preferred method)
            try:
                iam_client = session.client('iam')
                role_response = iam_client.get_role(RoleName=role_name)
                # Use actual ARN from IAM API
                arn = role_response['Role']['Arn']
                logger.debug(f"Retrieved base role ARN from IAM API: {arn}")
            except Exception as e:
                logger.debug(f"IAM API failed, falling back to string replacement: {e}")
                arn = arn.replace(':sts:', ':iam:').replace(':assumed-role/', ':role/').rsplit('/', 1)[0]
    else:
        identity_type = 'unknown'

    logger.debug(f"Resolved identity - ARN: {arn}, Type: {identity_type}")
    
    return arn, identity_type


def _check_access_entry_exists(
    eks_client: botocore.client.BaseClient,
    cluster_name: str,
    principal_arn: str
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Check if the given principal has an access entry for the EKS cluster.
    
    Args:
        eks_client: Boto3 EKS client
        cluster_name: Name of the EKS cluster
        principal_arn: ARN of the principal to check
        
    Returns:
        Tuple of (has_access, access_entry_details, error_message)
    """
    try:
        response = eks_client.describe_access_entry(
            clusterName=cluster_name,
            principalArn=principal_arn
        )
        return True, response.get('accessEntry'), None
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'ResourceNotFoundException':
            # No access entry found for this principal
            return False, None, f"No access entry found for principal: {principal_arn}"
        elif error_code == 'AccessDeniedException':
            # User doesn't have permission to check access entries
            return False, None, f"Access denied when checking access entries. You may not have eks:DescribeAccessEntry permission."
        elif error_code == 'ClusterNotFoundException':
            # Cluster doesn't exist
            return False, None, f"EKS cluster '{cluster_name}' not found."
        else:
            # Other error
            return False, None, f"Error checking access entry: {e.response['Error']['Message']}"
    
    except Exception as e:
        return False, None, f"Unexpected error checking access entry: {str(e)}"


def validate_eks_access_before_kubeconfig_update(
    session: boto3.Session,
    cluster_name: str,
    eks_name: str
) -> Tuple[bool, str]:
    """
    Validate that the current user has EKS access before attempting kubeconfig update.
    
    Args:
        session: Boto3 session
        cluster_name: Name of the HyperPod cluster (for error messages)
        eks_name: Name of the EKS cluster
        
    Returns:
        Tuple of (has_access, message)
    """
    try:
        # Get current AWS identity
        principal_arn, identity_type = _get_current_aws_identity(session)
        logger.debug(f"Current AWS identity: {principal_arn} (type: {identity_type})")
        
        # Create EKS client
        eks_client = session.client('eks')
        
        # Check if the principal has an access entry
        has_access, access_entry, error_msg = _check_access_entry_exists(
            eks_client, eks_name, principal_arn
        )
        
        if has_access:
            success_msg = f"✓ Access confirmed for {principal_arn}"
            if access_entry:
                kubernetes_groups = access_entry.get('kubernetesGroups', [])
                username = access_entry.get('username', 'N/A')
                success_msg += f"\n  - Username: {username}"
                success_msg += f"\n  - Kubernetes Groups: {', '.join(kubernetes_groups) if kubernetes_groups else 'None'}"
            return True, success_msg
        else:
            # Access validation failed - provide clear error message
            error_message = (
                f"✗ Cannot connect to EKS cluster '{eks_name}': {error_msg}\n\n"
                f"Your AWS identity '{principal_arn}' (type: {identity_type}) does not have an access entry "
                f"for this EKS cluster.\n\n"
                f"To resolve this issue:\n"
                f"1. Contact your cluster administrator to add your identity to the EKS access entries\n"
                f"2. Refer to this documentation to create an access entry: https://docs.aws.amazon.com/cli/latest/reference/eks/create-access-entry.html\n"
                f"3. Verify your AWS credentials and region are correct\n"
                f"4. Ensure you have the necessary EKS permissions (eks:DescribeAccessEntry)"
            )
            return False, error_message
            
    except Exception as e:
        return False, f"Unexpected error validating EKS access: {str(e)}"
