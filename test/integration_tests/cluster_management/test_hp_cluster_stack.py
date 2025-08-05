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

import os
import uuid
import time
import pytest
import boto3

from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack
from test.integration_tests.abstract_integration_tests import AbstractIntegrationTests


class TestHpClusterStackIntegration(AbstractIntegrationTests):
    """Integration tests for HpClusterStack class."""

    @pytest.fixture(scope="class")
    def stack_name(self):
        """Generate a unique stack name for testing."""
        return f"hyperpod-test-stack-{str(uuid.uuid4())[:8]}"

    def test_create_stack(self, stack_name):
        """Test creating a CloudFormation stack using HpClusterStack."""
        # Create a minimal stack configuration
        cluster_stack = HpClusterStack(
            stage="gamma",
            resource_name_prefix=f"hyperpod-test-{str(uuid.uuid4())[:8]}",
            eks_cluster_name="test-eks-cluster",
            create_eks_cluster_stack=True,
            create_vpc_stack=False,
            create_private_subnet_stack=False,
            create_security_group_stack=False,
            create_s3_bucket_stack=True,
            create_s3_endpoint_stack=False,
            create_life_cycle_script_stack=False,
            create_sagemaker_iam_role_stack=False,
            create_helm_chart_stack=False,
            create_hyperpod_cluster_stack=False,
            create_fsx_stack=False,
        )
        
        cf_client = boto3.client('cloudformation')
        stack_exists = False
        
        try:
            # Create the stack
            cluster_stack.create("stack-009", region ="us-west-2")
            
            # Wait for stack to be created (with timeout)
            # max_attempts = 10
            # for attempt in range(max_attempts):
            #     try:
            #         response = cf_client.describe_stacks(StackName=stack_name)
            #         stack_exists = True
            #         print(f"Stack found after {attempt + 1} attempts")
            #         break
            #     except Exception as e:
            #         if "does not exist" in str(e):
            #             print(f"Waiting for stack to be created (attempt {attempt + 1}/{max_attempts})")
            #             time.sleep(3)  # Wait before retrying
            #         else:
            #             raise
            
        #     # Verify the stack was created
        #     assert stack_exists, f"Stack {stack_name} was not created within the timeout period"
        #
        #     # Get the latest stack information
        #     response = cf_client.describe_stacks(StackName=stack_name)
        #     assert len(response['Stacks']) == 1
        #     assert response['Stacks'][0]['StackName'] == stack_name
        #     assert response['Stacks'][0]['StackStatus'] in [
        #         'CREATE_IN_PROGRESS',
        #         'CREATE_COMPLETE'
        #     ]
        #
        #     # Verify tags were applied
        #     stack_tags = response['Stacks'][0]['Tags']
        #     assert any(tag['Key'] == 'Environment' and tag['Value'] == 'Test' for tag in stack_tags)
        #     assert any(tag['Key'] == 'Project' and tag['Value'] == 'HyperPod' for tag in stack_tags)
        #
        finally:
            # Clean up - delete the stack if it exists
            if stack_exists:
                try:
                    cf_client.delete_stack(StackName=stack_name)
                    print(f"Stack {stack_name} deletion initiated")
                except Exception as e:
                    print(f"Error deleting stack: {e}")

    @pytest.mark.dependency(name="list_stacks")
    def test_list_stacks(self):
        """Test listing CloudFormation stacks using HpClusterStack.list."""
        # Test listing stacks - should return a response with StackSummaries
        response = HpClusterStack.list()
        
        # Verify response structure
        assert isinstance(response, dict)
        assert 'StackSummaries' in response
        assert isinstance(response['StackSummaries'], list)
        
        # If there are stacks, verify they have expected fields
        if response['StackSummaries']:
            stack = response['StackSummaries'][0]
            assert 'StackName' in stack
            assert 'StackStatus' in stack
            assert 'CreationTime' in stack

    def test_list_stacks_with_region(self):
        """Test listing stacks with explicit region parameter."""
        # Test with us-east-1 region
        response = HpClusterStack.list(region="us-east-1")
        
        assert isinstance(response, dict)
        assert 'StackSummaries' in response
        assert isinstance(response['StackSummaries'], list)

    @pytest.mark.dependency(depends=["list_stacks"])
    def test_describe_stack(self):
        """Test describing CloudFormation stacks using HpClusterStack.describe."""
        # First get a list of existing stacks to test with
        list_response = HpClusterStack.list()
        
        if list_response['StackSummaries']:
            # Test with an existing stack
            existing_stack_name = list_response['StackSummaries'][0]['StackName']
            
            response = HpClusterStack.describe(existing_stack_name)
            
            # Verify response structure
            assert isinstance(response, dict)
            assert 'Stacks' in response
            assert len(response['Stacks']) == 1
            
            stack = response['Stacks'][0]
            assert stack['StackName'] == existing_stack_name
            assert 'StackStatus' in stack
            assert 'CreationTime' in stack
            assert 'StackId' in stack
        
        # Test with a non-existent stack - should raise ValueError
        with pytest.raises(ValueError):
            HpClusterStack.describe("non-existent-stack-12345")