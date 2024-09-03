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

from hyperpod_cli.clients.kubernetes_client import KubernetesClient


class ListTrainingJobs:
    def __init__(self):
        return

    def list_training_jobs(
        self,
        namespace: Optional[str],
        all_namespaces: Optional[bool],
        selector: Optional[str],
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
                _jobs = k8s_client.list_training_jobs(
                    namespace=_namespace, label_selector=selector
                )
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
                    state = self._get_job_status(
                        job.get("status").get("conditions"))
                output_jobs["jobs"].append(
                    {
                        "Name": name,
                        "Namespace": namespace,
                        "Creation Time": creation_time,
                        "State": state,
                    }
                )

        return json.dumps(output_jobs, indent=1, sort_keys=False)

    def _get_job_status(self, status: List) -> Optional[str]:
        current_status = None
        last_date_time = datetime.strptime('2001-08-27T22:47:57Z', '%Y-%m-%dT%H:%M:%SZ')
        for state in status:
            state_date_time = datetime.strptime(state.get("lastTransitionTime"), '%Y-%m-%dT%H:%M:%SZ')
            if state_date_time > last_date_time:
                last_date_time = state_date_time
                current_status = state.get('type')
        return current_status
