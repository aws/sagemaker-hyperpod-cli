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
from typing import List, Optional

import json
from datetime import datetime

from sagemaker.hyperpod.cli.clients.kubernetes_client import (
    KubernetesClient,
)
from sagemaker.hyperpod.cli.utils import setup_logger
from kubernetes.client.rest import ApiException
from kubernetes.client import (
    V1ResourceAttributes
)

from sagemaker.hyperpod.cli.constants.command_constants import KUEUE_WORKLOAD_PRIORITY_CLASS_LABEL_KEY, OutputFormat
from sagemaker.hyperpod.cli.constants.pytorch_constants import PYTORCH_CUSTOM_OBJECT_GROUP, PYTORCH_CUSTOM_OBJECT_PLURAL
from sagemaker.hyperpod.cli.service.discover_namespaces import DiscoverNamespaces
from tabulate import tabulate


class ListTrainingJobs:
    def __init__(self):
        return

    def list_training_jobs(
        self,
        namespace: Optional[str],
        all_namespaces: Optional[bool],
        selector: Optional[str],
        output: Optional[str],
    ) -> str:
        """
        List training job provided by the user in the specified namespace.
        If namespace is not provided job are listed the default namespace in user context
        If all_namespace is true we will list training job from all namespaces that user has access
        Selector when specified will filter list of job addisional based on labels filter provided
        """
        k8s_client = KubernetesClient()

        jobs: List = []
        logger = setup_logger(__name__)
        logger.debug(namespace)
        try:
            if all_namespaces:
                namespaces: List[str] = k8s_client.list_namespaces()
                for _namespace in namespaces:
                    _jobs = k8s_client.list_training_jobs(
                        namespace=_namespace,
                        label_selector=selector,
                    )
                    if _jobs.get("items") and len(_jobs.get("items")) > 0:
                        for _job in _jobs.get("items"):
                            jobs.append(_job)
            else:
                if not namespace:
                    resource_attributes_template = V1ResourceAttributes(
                        verb="list",
                        group=PYTORCH_CUSTOM_OBJECT_GROUP,
                        resource=PYTORCH_CUSTOM_OBJECT_PLURAL,
                    )
                    namespace = DiscoverNamespaces().discover_accessible_namespace(
                        resource_attributes_template
                    )
                else:
                    if not k8s_client.check_if_namespace_exists(namespace):
                        raise ValueError(f"Namespace {namespace} does not exist!")

                namespace_jobs = k8s_client.list_training_jobs(
                    namespace=namespace,
                    label_selector=selector,
                )
                if namespace_jobs.get("items") and len(namespace_jobs.get("items")) > 0:
                    for namespace_job in namespace_jobs.get("items"):
                        jobs.append(namespace_job)
        except ApiException as e:
            raise RuntimeError(f"Unexpected API error: {e.reason} ({e.status})")

        return self._generate_list_training_job_output(jobs, output)

    def _generate_list_training_job_output(self, jobs: List, output: Optional[str]):
        output_jobs = {"jobs": []}
        priority_header_required = False

        for job in jobs:
            if job.get("metadata"):
                name = job.get("metadata").get("name")
                namespace = job.get("metadata").get("namespace")
                creation_time = None
                state = None
                priority = self._get_job_priority(job)
                if job.get("status"):
                    creation_time = job.get("status").get("startTime")
                    state = self._get_job_status(job.get("status").get("conditions"))

                job_summary = {
                    "Name": name,
                    "Namespace": namespace,
                    "CreationTime": creation_time,
                    "State": state,
                }

                if priority is not None:
                    job_summary["priority"] = priority
                    priority_header_required = True

                output_jobs["jobs"].append(job_summary)

        if output == OutputFormat.TABLE.value:
            return self._generate_table(output_jobs, priority_header_required)
        return json.dumps(output_jobs, indent=4, sort_keys=False)

    def _generate_table(self, output_jobs, priority_header_required):
        headers = [
                "Name",
                "Namespace",
                "CreationTime",
                "State"
            ]

        if priority_header_required:
            headers.append("Priority")

        jobs = []
        if "jobs" in output_jobs and isinstance(output_jobs["jobs"], list):
            for job in output_jobs["jobs"]:
                job_values = list(job.values())
                if priority_header_required and len(job_values) == 4:
                    job_values.append("NA")
                jobs.append(job_values)

        return tabulate(jobs, headers=headers, tablefmt="presto")

    def _get_job_status(self, status: List) -> Optional[str]:
        current_status = None
        last_date_time = datetime.strptime(
            "2001-08-27T22:47:57Z",
            "%Y-%m-%dT%H:%M:%SZ",
        )
        for state in status:
            state_date_time = datetime.strptime(
                state.get("lastTransitionTime"),
                "%Y-%m-%dT%H:%M:%SZ",
            )
            if state_date_time >= last_date_time:
                last_date_time = state_date_time
                current_status = state.get("type")
        return current_status

    def _get_job_priority(self, job) -> Optional[str]:
        worker_template = job.get("spec", {}).get("pytorchReplicaSpecs", {}).get("Worker", {}).get("template", {})
        wl_priority_cls = worker_template.get("metadata", {}).get("labels", {}).get(KUEUE_WORKLOAD_PRIORITY_CLASS_LABEL_KEY, None)
        spec_priority_cls = worker_template.get("spec", {}).get("priorityClassName", None)

        # For reference: https://kueue.sigs.k8s.io/docs/concepts/workload_priority_class/
        # The workload priority class takes precedence over the k8s priority class.
        # Because the cli focuses on the job level which means workload priority is more essential.
        # There is possibility that these two priorities coexist at the same time. In this case,
        # the k8s priority class will be used as pod priority. cli should still take workload
        # priority in this scenario.

        if wl_priority_cls is not None:
            return wl_priority_cls
        elif spec_priority_cls is not None:
            return spec_priority_cls
        
        return None
