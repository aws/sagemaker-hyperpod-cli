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
from enum import Enum

GENERATED_LAUNCHER_CONFIG_FILE_PATH = "/tmp/"
HYPERPOD_KUBERNETES_JOB_PREFIX = "hyperpod-k8s-job"
HYPERPOD_CLUSTER_CONTEXT_FILE_NAME = "hyperpod_current_context.json"
NODE_AFFINITY_DICT = {
    "required": {"sagemaker.amazonaws.com/node-health-status": ["Schedulable"]},
    "preferred": {"sagemaker.amazonaws.com/deep-health-check-status": ["Passed"]},
    "weights": [100],
}
DEEP_HEALTH_CHECK_PASSED_ONLY_NODE_AFFINITY_DICT = {
    "required": {
        "sagemaker.amazonaws.com/deep-health-check-status": ["Passed"],
    },
}
KUEUE_QUEUE_NAME_LABEL_KEY = "kueue.x-k8s.io/queue-name"
HYPERPOD_AUTO_RESUME_ANNOTATION_KEY = "sagemaker.amazonaws.com/enable-job-auto-resume"
HYPERPOD_MAX_RETRY_ANNOTATION_KEY = "sagemaker.amazonaws.com/job-max-retry-count"
ENV_VARS_DICT = {"NCCL_DEBUG": "INFO"}
SAGEMAKER_HYPERPOD_NAME_LABEL = "sagemaker.amazonaws.com/cluster-name"
HP_HEALTH_STATUS_LABEL = "sagemaker.amazonaws.com/node-health-status"
INSTANCE_TYPE_LABEL = "node.kubernetes.io/instance-type"
DEEP_HEALTH_CHECK_STATUS_LABEL = "sagemaker.amazonaws.com/deep-health-check-status"
TEMP_KUBE_CONFIG_FILE = "/tmp/kubeconfig"


class PullPolicy(Enum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class RestartPolicy(Enum):
    ALWAYS = "Always"
    ON_FAILURE = "OnFailure"
    NEVER = "Never"
    EXIT_CODE = "ExitCode"


class Orchestrator(Enum):
    EKS = "eks"


class OutputFormat(Enum):
    JSON = "json"
    TABLE = "table"


class PersistentVolumeClaim:
    claim_name: str
    mount_path: str

    def __init__(self, claim_name, mount_path):
        self.claim_name = claim_name
        self.mount_path = mount_path


class Volume:
    volume_name: str
    host_path: str
    mount_path: str

    def __init__(self, volume_name, host_path, mount_path):
        self.host_path = host_path
        self.mount_path = mount_path
        self.volume_name = volume_name
