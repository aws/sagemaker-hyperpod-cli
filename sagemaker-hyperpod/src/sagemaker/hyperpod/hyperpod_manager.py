import boto3
from tabulate import tabulate
from kubernetes import config
import yaml
from typing import Optional
from kubernetes.config import (
    KUBE_CONFIG_DEFAULT_LOCATION,
)
import os
import subprocess
import re

KUBE_CONFIG_PATH = os.path.expanduser(KUBE_CONFIG_DEFAULT_LOCATION)
TEMP_KUBE_CONFIG_FILE = "/tmp/kubeconfig"


class HyperPodManager:
    def _get_eks_name_from_arn(self, arn: str) -> str:

        pattern = r"arn:aws:eks:[\w-]+:\d+:cluster/([\w-]+)"
        match = re.match(pattern, arn)

        if match:
            return match.group(1)
        else:
            raise RuntimeError("cannot get EKS cluster name")

    def _is_eks_orchestrator(self, sagemaker_client, cluster_name: str):
        response = sagemaker_client.describe_cluster(ClusterName=cluster_name)
        return "Eks" in response["Orchestrator"]

    def _update_kube_config(
        self,
        eks_name: str,
        region: Optional[str] = None,
        config_file: Optional[str] = None,
    ) -> None:
        """
        Update the local kubeconfig with the specified EKS cluster details.

        Args:
            eks_name (str): The name of the EKS cluster to update in the kubeconfig.
            region (Optional[str]): The AWS region where the EKS cluster resides.
                If not provided, the default region from the AWS credentials will be used.
            config_file (Optional[str]): The path to the kubeconfig file.

        Raises:
            RuntimeError: If the `aws eks update-kubeconfig` command fails to execute.
        """

        # EKS doesn't provide boto3 API for this command
        command = ["aws", "eks", "update-kubeconfig", "--name", eks_name]

        if region:
            command.extend(["--region", region])

        if config_file:
            command.extend(["--kubeconfig", config_file])

        try:
            # Execute the command to update kubeconfig
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update kubeconfig: {e}")

    def _set_current_context(
        self,
        context_name: str,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Set the current context in the kubeconfig file.

        Args:
            context_name (str): The name of the context to set as current.
            namespace (str): The name of the namespace to use.
        """
        with open(KUBE_CONFIG_PATH, "r") as file:
            kubeconfig = yaml.safe_load(file)

        # Check if the context exists in the kubeconfig and update the context namespace
        # when namespace is specified in command line
        exist = False
        for context in kubeconfig["contexts"]:
            if context["name"] == context_name:
                if namespace is not None:
                    context["context"]["namespace"] = namespace
                else:
                    context["context"].pop("namespace", None)
                exist = True

        if not exist:
            raise ValueError(f"Context '{context_name}' not found in kubeconfig file")

        # Set the current context
        kubeconfig["current-context"] = context_name

        # Write the updated kubeconfig back to the file
        with open(KUBE_CONFIG_PATH, "w") as file:
            yaml.safe_dump(kubeconfig, file)

        # Load the updated kubeconfig
        config.load_kube_config(config_file=KUBE_CONFIG_PATH)

    def list_clusters(
        self,
        region: Optional[str] = None,
    ):
        client = boto3.client("sagemaker", region_name=region)
        clusters = client.list_clusters()

        eks_clusters = []
        slurm_clusters = []

        for cluster in clusters["ClusterSummaries"]:
            cluster_name = cluster["ClusterName"]

            if self._is_eks_orchestrator(client, cluster_name):
                eks_clusters.append(("EKS", cluster_name))
            else:
                slurm_clusters.append((cluster_name, "Slurm"))

        table_data = eks_clusters + slurm_clusters
        headers = ["Orchestrator", "Cluster Name"]

        print(tabulate(table_data, headers=headers))

    def set_context(
        self,
        cluster_name: str,
        region: Optional[str] = None,
        namespace: Optional[str] = None,
    ):
        client = boto3.client("sagemaker", region_name=region)

        response = client.describe_cluster(ClusterName=cluster_name)
        eks_cluster_arn = response["Orchestrator"]["Eks"]["ClusterArn"]
        eks_name = self._get_eks_name_from_arn(eks_cluster_arn)

        self._update_kube_config(eks_name, region, TEMP_KUBE_CONFIG_FILE)
        self._set_current_context(eks_cluster_arn, namespace)

        print(f"Successfully set current cluster: {cluster_name}")

    def get_context(self):
        try:
            current_context = config.list_kube_config_contexts()[1]["context"][
                "cluster"
            ]
            print(f"Current Eks context is: {current_context}")
        except Exception as e:
            print(
                f"Failed to get current context: {e}. Check your config file at {TEMP_KUBE_CONFIG_FILE}"
            )
