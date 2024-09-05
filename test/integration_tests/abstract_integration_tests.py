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
import subprocess
import time
import uuid
import re

import boto3
from botocore.exceptions import ClientError

from hyperpod_cli.utils import setup_logger

logger = setup_logger(__name__)


class AbstractIntegrationTests:
    cfn_output_map = {}
    hyperpod_cluster_terminal_state = ["Failed", "InService"]
    suffix = str(uuid.uuid4())[:8]
    hyperpod_cli_cluster_name = "hyperpod-cli-cluster-" + suffix
    vpc_eks_stack_name = "hyperpod-cli-stack-" + suffix
    s3_roles_stack_name = "hyperpod-cli-resource-stack"
    vpc_stack_name = "hyperpod-cli-vpc-stack"
    eks_cluster_name = "hyperpod-cli-cluster-" + suffix
    bucket_name = "hyperpod-cli-s3-" + suffix

    def _create_session(self):
        session = boto3.Session()
        return session

    def create_test_resorces(self, session):
        cfn = session.client("cloudformation")

        # Get static resources from static-resource stack
        self.describe_constant_resources_stack_and_set_values(cfn)

        # Get static resources from static-resource stack
        self.describe_vpc_stack_and_set_values(cfn)

        # Create VPC, EKS cluster and roles
        with open("test/integration_tests/cloudformation/resources.yaml", "r") as fh:
            template = fh.read()
            cfn.create_stack(
                StackName=self.vpc_eks_stack_name,
                TemplateBody=template,
                Capabilities=["CAPABILITY_NAMED_IAM"],
                Parameters=[
                    {
                        "ParameterKey": "ClusterName",
                        "ParameterValue": self.eks_cluster_name,
                        "ResolvedValue": "string",
                    },
                    {
                        "ParameterKey": "EKSClusterRoleArn",
                        "ParameterValue": self.cfn_output_map.get("EKSClusterRoleArn"),
                        "ResolvedValue": "string",
                    },
                    {
                        "ParameterKey": "SubnetId1",
                        "ParameterValue": self.cfn_output_map.get("PrivateSubnet1"),
                        "ResolvedValue": "string",
                    },
                    {
                        "ParameterKey": "SubnetId2",
                        "ParameterValue": self.cfn_output_map.get("PrivateSubnet2"),
                        "ResolvedValue": "string",
                    },
                    {
                        "ParameterKey": "SecurityGroupId",
                        "ParameterValue": self.cfn_output_map.get("SecurityGroup"),
                        "ResolvedValue": "string",
                    },
                ],
            )
        waiter = cfn.get_waiter("stack_create_complete")
        waiter.wait(
            StackName=self.vpc_eks_stack_name,
            WaiterConfig={"Delay": 30, "MaxAttempts": 40},
        )
        describe = cfn.describe_stacks(StackName=self.vpc_eks_stack_name)
        if describe:
            cfn_output = describe.get("Stacks")[0]
            if cfn_output and cfn_output.get("Outputs"):
                for output in cfn_output.get("Outputs"):
                    self.cfn_output_map[output.get("OutputKey")] = output.get(
                        "OutputValue"
                    )

    def delete_cloudformation_stack(self, session):
        cfn = session.client("cloudformation")
        cfn.delete_stack(StackName=self.vpc_eks_stack_name)

    def upload_lifecycle_script(self, session):
        s3_client = session.client("s3")
        try:
            response = s3_client.upload_file(
                "test/integration_tests/lifecycle_script/on_create_noop.sh",
                self.cfn_output_map.get("Bucket"),
                "on_create_noop.sh",
            )
        except ClientError as e:
            logger.error(f"Error uploading lifecycle script to s3 {e}")

    def get_hyperpod_cluster_status(self, sagemaker_client):
        return sagemaker_client.describe_cluster(
            ClusterName=self.hyperpod_cli_cluster_name
        )

    def create_hyperpod_cluster(self, session):
        # Create HyperPod cluster using eks cluster from stack above
        # TODO: removing dev endpoint
        sagemaker_client = session.client("sagemaker")
        sagemaker_client.create_cluster(
            ClusterName=self.hyperpod_cli_cluster_name,
            Orchestrator={"Eks": {"ClusterArn": self.cfn_output_map.get("ClusterArn")}},
            InstanceGroups=[
                {
                    "InstanceGroupName": "group2",
                    "InstanceType": "ml.c5.2xlarge",
                    "InstanceCount": 2,
                    "LifeCycleConfig": {
                        "SourceS3Uri": f's3://{self.cfn_output_map.get("Bucket")}',
                        "OnCreate": "on_create_noop.sh",
                    },
                    "ExecutionRole": self.cfn_output_map.get("ExecutionRole"),
                    "ThreadsPerCore": 1,
                }
            ],
            VpcConfig={
                "SecurityGroupIds": [self.cfn_output_map.get("SecurityGroup")],
                "Subnets": [self.cfn_output_map.get("PrivateSubnet1")],
            },
        )

        time.sleep(1)
        # Wait for sagemkaer stack to create complete
        try:
            result = self.get_hyperpod_cluster_status(sagemaker_client)
            while (
                result.get("ClusterStatus") not in self.hyperpod_cluster_terminal_state
            ):
                time.sleep(30)
                result = self.get_hyperpod_cluster_status(sagemaker_client)
        except Exception as e:
            logger.error(e)
        logger.info(f"Hyperpod cluster created {self.hyperpod_cli_cluster_name}")

    def delete_hyperpod_cluster(self, session):
        # delete HyperPod cluster using eks cluster from stack above
        # TODO: removing dev endpoint
        sagemaker_client = session.client("sagemaker")
        sagemaker_client.delete_cluster(ClusterName=self.hyperpod_cli_cluster_name)

        time.sleep(10)
        # Wait for sagemkaer stack to create complete
        try:
            result = self.get_hyperpod_cluster_status(sagemaker_client)
            while result.get("ClusterStatus") == "Deleting":
                time.sleep(30)
                result = self.get_hyperpod_cluster_status(sagemaker_client)
        except Exception as e:
            logger.info(
                f"Caught exception while trying to describe cluster during teardown {e}"
            )
            return
        raise Exception(
            f"Hyperpod Cluster {self.hyperpod_cli_cluster_name} fail to delete"
        )

    def create_kube_context(self):
        eks_cluster_name = self.cfn_output_map.get("ClusterArn").split(":")[-1]
        eks_cluster_name = eks_cluster_name.split("/")[-1]
        command = ["aws", "eks", "update-kubeconfig", "--name", eks_cluster_name]

        try:
            # Execute the command to update kubeconfig
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update kubeconfig: {e}")

    def describe_constant_resources_stack_and_set_values(self, cfn_client):
        describe_s3_stack = cfn_client.describe_stacks(
            StackName=self.s3_roles_stack_name
        )
        if describe_s3_stack:
            cfn_output = describe_s3_stack.get("Stacks")[0]
            if cfn_output and cfn_output.get("Outputs"):
                for output in cfn_output.get("Outputs"):
                    self.cfn_output_map[output.get("OutputKey")] = output.get(
                        "OutputValue"
                    )

    def describe_vpc_stack_and_set_values(self, cfn_client):
        describe_vpc_stack = cfn_client.describe_stacks(StackName=self.vpc_stack_name)
        if describe_vpc_stack:
            cfn_output = describe_vpc_stack.get("Stacks")[0]
            if cfn_output and cfn_output.get("Outputs"):
                for output in cfn_output.get("Outputs"):
                    self.cfn_output_map[output.get("OutputKey")] = output.get(
                        "OutputValue"
                    )

    def update_cluster_auth(self):
        with open(
            "test/integration_tests/charts/hp-node-auth.yaml", "r"
        ) as hyperpod_current_context:
            template = hyperpod_current_context.read()

        template = re.sub(
            "SAGEMAKER_EXECUTION_ROLE",
            self.cfn_output_map.get("ExecutionRole"),
            template,
        )
        template = re.sub(
            "SAGEMAKER_SERVICE_ROLE", self.cfn_output_map.get("ServiceRole"), template
        )

        with open("/tmp/hp-node-auth.yaml", "w") as hyperpod_current_context:
            hyperpod_current_context.write(template)

        command = ["kubectl", "apply", "-f", "/tmp/hp-node-auth.yaml"]

        try:
            # Execute the command to update kubeconfig
            logger.info(
                subprocess.run(command, check=True, capture_output=True, text=True)
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to apply auth charts: {e}")

    def install_training_operator(self):
        command = [
            "kubectl",
            "apply",
            "-k",
            "github.com/kubeflow/training-operator/manifests/overlays/standalone?ref=v1.7.0",
        ]

        try:
            # Execute the command to update kubeconfig
            logger.info(
                subprocess.run(command, check=True, capture_output=True, text=True)
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install training operator: {e}")

    def setup(self):
        self.new_session = self._create_session()
        self.create_test_resorces(self.new_session)
        self.create_kube_context()
        self.update_cluster_auth()
        self.create_hyperpod_cluster(self.new_session)
        self.install_training_operator()

    def tearDown(self):
        self.delete_hyperpod_cluster(self.new_session)
        self.delete_cloudformation_stack(self.new_session)
