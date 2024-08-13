from collections import defaultdict
from typing import List, Optional
import json

from kubernetes.client import V1Pod, V1PodList

from hyperpod_cli.clients.kubernetes_client import KubernetesClient


class ListPods:
    def __init__(self):
        return

    def list_pods_for_training_job(
        self, job_name: str, namespace: Optional[str], pretty: Optional[bool]
    ):
        """
        List pods associated with a training job
        """
        k8s_client = KubernetesClient()

        if not namespace:
            namespace = k8s_client.get_current_context_namespace()

        label_filter = f"training.kubeflow.org/job-name={job_name}"
        _pods: V1PodList = k8s_client.list_pods_with_labels(namespace, label_filter)

        if pretty:
            return self._generate_list_pods_output(_pods)
        else:
            return self._generate_pods_list(_pods)

    def list_pods_and_get_requested_resources_group_by_node_name(self):
        """
        List pods for all namespaces and initialized by kubeflow.
        Group by the node_name of the pod and the value is the
        accelerator devices resources requested
        """
        k8s_client = KubernetesClient()

        label_filter = f"training.kubeflow.org/job-name"
        pods = k8s_client.list_pods_in_all_namespaces_with_labels(label_filter)

        # Dictionary to hold total GPU/Neuron requests per node
        accelerator_devices_requests_by_node = defaultdict(int)

        # Loop through each pod and aggregate the GPU resource requests per node
        for pod in pods:
            node_name = pod.spec.node_name
            # Check if the pod has a node_name assigned, if pod is not scheduled, it may not have node_name
            if node_name:
                for container in pod.spec.containers:
                    if container.resources and container.resources.requests:
                        gpu_request = container.resources.requests.get("nvidia.com/gpu")
                        neuron_request = container.resources.requests.get(
                            "aws.amazon.com/neurondevice"
                        )
                        if gpu_request:
                            accelerator_devices_requests_by_node[node_name] += int(gpu_request)
                        if neuron_request:
                            accelerator_devices_requests_by_node[node_name] += int(neuron_request)

        return accelerator_devices_requests_by_node

    def _generate_list_pods_output(self, pods: V1PodList) -> Optional[str]:
        output_pods = {"pods": []}
        if pods.items and len(pods.items) > 0:
            _pod: V1Pod
            for _pod in pods.items:
                if _pod.metadata and _pod.metadata.name and _pod.metadata.namespace:
                    name = _pod.metadata.name
                    namespace = _pod.metadata.namespace
                    status = None
                    creation_timestamp = None
                    if _pod.status and _pod.status.phase:
                        status = _pod.status.phase
                    if _pod.metadata.creation_timestamp:
                        creation_timestamp = str(_pod.metadata.creation_timestamp)
                    output_pods["pods"].append({"Pod Name": name, "Namespace": namespace, "Status": status, "Creation Time": creation_timestamp})

        return json.dumps(output_pods, indent=1, sort_keys=False)

    def _generate_pods_list(self, pods: V1PodList) -> List:
        output_pods = []
        if pods.items and len(pods.items) > 0:
            _pod: V1Pod
            for _pod in pods.items:
                if _pod.metadata and _pod.metadata.name:
                    name = _pod.metadata.name
                    output_pods.append(name)
        return output_pods
