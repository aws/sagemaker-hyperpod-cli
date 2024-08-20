from typing import List, Optional

import json

from hyperpod_cli.clients.kubernetes_client import KubernetesClient


class ListTrainingJobs:
    def __init__(self):
        return

    def list_training_jobs(
        self, namespace: Optional[str], all_namespaces: Optional[bool], selector: Optional[str]
    ) -> str:
        """
        List training job provided by the user in the specified namespace.
        If namespace is not provided job are listed the default namespace in user context
        If all_namespace is true we will list training job from all namespaces that user has access
        Selector when specified will filter list of job addisional based on labels filter provided
        """

        k8s_client = KubernetesClient()

        jobs: List = []

        if all_namespaces:
            namespaces: List[str] = k8s_client.list_namespaces()
            for _namespace in namespaces:
                _jobs = k8s_client.list_training_jobs(namespace=_namespace, label_selector=selector)
                if _jobs.get("items") and len(_jobs.get("items")) > 0:
                    for _job in _jobs.get("items"):
                        jobs.append(_job)
        else:
            if not namespace:
                namespace = k8s_client.get_current_context_namespace()

            namespace_jobs = k8s_client.list_training_jobs(
                namespace=namespace, label_selector=selector
            )
            if namespace_jobs.get("items") and len(namespace_jobs.get("items")) > 0:
                for namespace_job in namespace_jobs.get("items"):
                    jobs.append(namespace_job)

        return self._generate_list_training_job_output(jobs)

    def _generate_list_training_job_output(self, jobs: List):
        output_jobs = {"jobs": []}
        for job in jobs:
            if job.get("metadata"):
                name = job.get("metadata").get("name")
                namespace = job.get("metadata").get("namespace")
                creation_time = None
                state = None
                if job.get("status"):
                    creation_time = job.get("status").get("startTime")
                    state = self._get_job_status(job.get("status").get("conditions"), name)
                output_jobs["jobs"].append({"Name":name, "Namespace":namespace, "Creation Time": creation_time, "State":state})

        return json.dumps(output_jobs, indent=1, sort_keys=False)

    def _get_job_status(self, status: List, job_name: str) -> Optional[str]:
        current_status = None
        for state in status:
            if state.get("type") == "Succeeded":
                current_status = "Succeeded"
            elif state.get("type") == "Running" and current_status != "Succeeded":
                current_status = "Running"
            elif state.get("type") == "Created" and (
                current_status != "Running" or current_status != "Succeeded"
            ):
                current_status = "Created"
            else:
                raise RuntimeError(f"Unknown status {state.get('type')} for job {job_name}")
        return current_status
