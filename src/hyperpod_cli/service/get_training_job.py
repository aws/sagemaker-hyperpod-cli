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
from typing import Optional

import json

from hyperpod_cli.clients.kubernetes_client import KubernetesClient

from hyperpod_cli import utils


class GetTrainingJob:
    def __init__(self):
        return

    def get_training_job(
        self, job_name: str, namespace: Optional[str], verbose: Optional[bool]
    ):
        """
        Describe training job provided by the user in the speified namespace.
        If namespace is not provided job is described from the default namespace in user context
        """

        k8s_client = KubernetesClient()

        if not namespace:
            namespace = k8s_client.get_current_context_namespace()

        result = k8s_client.get_job(job_name=job_name, namespace=namespace)

        if not verbose:
            return self._format_output_to_keep_needed_fields(result)
        else:
            return self._format_verbose_output(result)

    def _format_output_to_keep_needed_fields(self, output):
        result = {}
        if output:
            if output.get("metadata"):
                result = {
                    "Name": output.get("metadata").get("name"),
                    "Namespace": output.get("metadata").get("namespace"),
                    "Label": output.get("metadata").get("labels"),
                    "Creation Timestamp": output.get("metadata").get(
                        "creationTimestamp"
                    ),
                }
            result.update({"Status": output.get("status")})
            result.update({"Console URL": utils.get_cluster_console_url()})
        return json.dumps(result, indent=1, sort_keys=False)

    def _format_verbose_output(self, output):
        result = {}
        if output:
            if output.get("metadata"):
                result = {
                    "Name": output.get("metadata").get("name"),
                    "Namespace": output.get("metadata").get("namespace"),
                    "Label": output.get("metadata").get("labels"),
                    "Annotations": output.get("metadata").get("annotations"),
                    "Metadata": {
                        "Creation Timestamp": output.get("metadata").get(
                            "creationTimestamp"
                        ),
                        "Generation": output.get("metadata").get("generation"),
                        "Resource Version": output.get("metadata").get(
                            "resourceVersion"
                        ),
                        "UID": output.get("metadata").get("uid"),
                    },
                }
            result.update({"Kind": output.get("kind")})
            result.update({"API Version": output.get("apiVersion")})
            result.update({"Spec": output.get("spec")})
            result.update({"Status": output.get("status")})
            result.update({"Console URL": utils.get_cluster_console_url()})
        return json.dumps(result, indent=1, sort_keys=False)
