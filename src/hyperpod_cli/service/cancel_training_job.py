from typing import Optional

from hyperpod_cli.clients.kubernetes_client import KubernetesClient


class CancelTrainingJob:

    def __init__(self):
        return

    def cancel_training_job(self, job_name: str, namespace: Optional[str]):
        """
        Cancel training job provided by the user in the specified namespace.
        If namespace is not provided job is canceled from the default namespace in user context
        """

        k8s_client = KubernetesClient()

        if not namespace:
            namespace = k8s_client.get_current_context_namespace()

        result = k8s_client.delete_training_job(job_name=job_name, namespace=namespace)
        if result.get("status") and result.get("status") == 'Success':
            return None
        else:
            return result
