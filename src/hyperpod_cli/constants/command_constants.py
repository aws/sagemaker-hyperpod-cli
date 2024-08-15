from enum import Enum

GENERATED_LAUNCHER_CONFIG_FILE_PATH = "/tmp/"
HYPERPOD_KUBERNETES_JOB_PREFIX = "hyperpod-k8s-job"
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
DEEP_HEALTH_CHECK_STATUS_LABEL = "sagemaker.amazonaws.com/deep-health-check-status "
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
