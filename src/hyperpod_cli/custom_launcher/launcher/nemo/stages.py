import os
import shutil
from pathlib import Path
from typing import Dict, List

import omegaconf
from urllib.parse import urlparse
from nemo_launcher.core.stages import Training
from nemo_launcher.utils.job_utils import JobPaths
from omegaconf import OmegaConf

from ..accelerator_devices import get_num_accelerator_devices
from ..efa import (
    efa_supported_instance,
    instanceWithMultipleEFAs,
    instanceWithRDMASupport,
)
from .launchers import SMAutoLauncher

# Predefined distributed args for torchrun
PROCESSES_PER_NODE = "PROCESSES_PER_NODE"
NNODES = "NNODES"
NODEID = "NODEID"
MASTER_ADDR = "MASTER_ADDR"
MASTER_PORT = "MASTER_PORT"
DISTRIBUTED_ARGS = "DISTRIBUTED_ARGS"


def set_multinode_envs(env_vars, instance_type):
    # https://github.com/aws/aws-ofi-nccl/blob/master/doc/efa-env-var.md
    if get_num_efa_devices(instance_type) > 0:
        env_vars["FI_PROVIDER"] = "efa"
        env_vars["NCCL_PROTO"] = "simple"
        if allow_rdma(instance_type):
            env_vars["FI_EFA_USE_DEVICE_RDMA"] = "1"
    env_vars["NCCL_SOCKET_IFNAME"] = "^lo,docker0"
    env_vars["NCCL_IGNORE_DISABLED_P2P"] = "1"
    env_vars["TORCH_NCCL_ASYNC_ERROR_HANDLING"] = "1"
    env_vars["TORCH_DIST_INIT_BARRIER"] = "1"
    env_vars["CUDA_DEVICE_MAX_CONNECTIONS"] = "1"
    env_vars["FI_EFA_FORK_SAFE"] = "1"
    return env_vars


def allow_rdma(instance_type):
    return instance_type in instanceWithRDMASupport


def get_instance_type(cfg):
    instance_type = None
    if cfg.get("instance_type"):
        instance_type = cfg.instance_type
    else:
        # custom path
        instance_type = cfg.cluster.instance_type
    assert instance_type is not None, "instance type is required from config"
    if instance_type.startswith("ml."):
        instance_type = instance_type[3:]
    return instance_type.lower()


def get_num_efa_devices(instance_type):
    # If not a EFA instance, return 0
    if instance_type not in efa_supported_instance:
        return 0
    # If multi-EFA, return from mapping
    if instance_type in instanceWithMultipleEFAs:
        return instanceWithMultipleEFAs[instance_type]
    # Only a single EFA device
    return 1


def get_ntasks_per_node(stage_cfg):
    """
    Get the number of processes per node used for training
    When running with custom script it will be stage_cfg.run.ntasks_per_node
    """
    run_cfg = stage_cfg.get("run")
    ntasks = run_cfg.get("ntasks_per_node")
    if ntasks is None:
        ntasks = stage_cfg.get("trainer").get("devices")
    return ntasks


def get_num_nodes(stage_cfg):
    """
    Get the number of nodes used for training
    When running with custom script it will be stage_cfg.run.nodes
    """
    run_cfg = stage_cfg.get("run")
    nodes = run_cfg.get("nodes")
    if nodes is None:
        nodes = stage_cfg.get("trainer").get("num_nodes")
    return nodes


class SMTraining(Training):
    """
    Base stage class for doing training on Sagemaker
    """

    def __init__(self, cfg):
        super().__init__(cfg)
        # Use GPU device for default flow for NeMo runs
        self.device = "gpu"
        self.instance_type = get_instance_type(cfg)
        self.num_efa_devices = get_num_efa_devices(self.instance_type)

    @property
    def _default_repo(self):
        # Default repo to mount script from
        return None

    def _make_torchrun_string(self):
        """
        Create torchrun string based on single/multi-node job
        """
        ntasks_per_node = get_ntasks_per_node(self.stage_cfg)
        if int(get_num_nodes(self.stage_cfg)) > 1:
            return f"torchrun ${DISTRIBUTED_ARGS} "
        else:
            return f"torchrun --nproc_per_node {ntasks_per_node} "

    def _make_custom_call_string(self, stage_cfg_path=None):
        """
        Create the training command with torchrun, script and args
        """
        script_path = str(self._entry_script_path)
        torchrun_cmd = self._make_torchrun_string()
        script_args_str = self.get_script_args_str(stage_cfg_path)
        command = [torchrun_cmd, script_path, script_args_str]
        command_string = " \\\n  ".join(command)
        return command_string

    def _get_hostfile_location(self):
        """
        Get the file location to store the hostnames
        """
        job_path = self.get_job_path()
        hostfile_location = Path(job_path.folder / "hostname")
        return hostfile_location

    def _get_nodeid_location(self):
        """
        Get the file location to store the nodeid, which will be used for node_rank in torchrun arg
        """
        job_path = self.get_job_path()
        nodeid_location = Path(job_path.folder / "node_id")
        return nodeid_location

    def _make_train_script_text(self, stage_cfg_path=None, port=41000) -> str:
        """
        The custom train entry script, it will be responsible for following
        - Handle resolving hostname and create torch distribtued args
        - Pull from github if required
        - Launch torchrun command
        """
        nodes = get_num_nodes(self.stage_cfg)
        ntasks_per_node = get_ntasks_per_node(self.stage_cfg)
        script_text = ["/bin/bash", "set -ex"]
        # Prepare for the host information to create the torchrun command
        if nodes > 1:
            script_text.extend(
                [
                    f"{MASTER_ADDR}=$(head -n 1 {str(self._get_hostfile_location())})",
                    f"{NODEID}=$(head -n 1 {str(self._get_nodeid_location())})",
                    f"{NNODES}={nodes}",
                    f"{PROCESSES_PER_NODE}={ntasks_per_node}",
                    f"{MASTER_PORT}={port}",
                    "",
                ]
            )
            if self.device == "trainium":
                script_text.append(
                    f'{DISTRIBUTED_ARGS}="--nproc_per_node ${PROCESSES_PER_NODE} --nnodes ${NNODES} --node_rank ${NODEID} --master_addr ${MASTER_ADDR} --master_port ${MASTER_PORT}"'
                )
            else:
                script_text.append(
                    f'{DISTRIBUTED_ARGS}="--nproc_per_node ${PROCESSES_PER_NODE} --nnodes ${NNODES} --rdzv_endpoint=${MASTER_ADDR} --rdzv_id=100 --rdzv_backend=c10d"'
                )
        else:
            script_text = [f'{DISTRIBUTED_ARGS}="--nproc_per_node {ntasks_per_node}"']

        # Prepare github pull
        # Aligns with the train-script preparition in launcher/nemo/k8s_templates/training.yaml
        script_text.append("")
        if self.cfg.get("git", None) is not None or self._default_repo is not None:
            repo_url = self._default_repo
            if self.cfg.git.get("repo_url", None) is not None:
                repo_url = str(self.cfg.git.get("repo_url"))
            if repo_url is not None:
                if self.cfg.git.get("token", None) is not None:
                    repo_url = self.insert_git_token(repo_url, self.cfg.git.token)

                script_text.extend(
                    [
                        "mkdir -p $HOME/tmp",
                        "GIT_CLONE_DIR=$HOME/tmp/$HOSTNAME",
                        "[[ -d $GIT_CLONE_DIR ]] && rm -rf $GIT_CLONE_DIR",
                        f"git clone {repo_url} $GIT_CLONE_DIR",
                        "GIT_CLONE_DIR=${GIT_CLONE_DIR}/",
                        "cd $GIT_CLONE_DIR",
                    ]
                )
            if self.cfg.git.get("branch", None) is not None:
                script_text.append(f"git checkout {self.cfg.git.branch}")
            if self.cfg.git.get("commit", None) is not None:
                script_text.append(f"git fetch origin {self.cfg.git.commit}")
                script_text.append(f"git reset --hard {self.cfg.git.commit}")
        else:
            script_text.append('GIT_CLONE_DIR=""')

        script_text.append("")
        script_text.append("unset SLURM_NTASKS")

        script_text.append("")
        script_text.append(self._make_custom_call_string(stage_cfg_path))
        return "\n".join(script_text)

    def make_stage_command_groups(self, stage_cfg_path: Path) -> List[List[str]]:
        """
        Custom run stage which will invoke the entry script only
        [TODO] Make this compatiable with NeMo flow as well
        """
        # There will be only a single command group
        command_groups = [[f"bash {stage_cfg_path.parents[0]}/train_script.sh"]]
        return command_groups

    def run(self) -> str:
        """
        Run current stage
        """
        # Setup folders and datasets
        self.setup_folder_and_data()
        # Save stage hydra config
        job_path = self.get_job_path()

        is_custom = self.cfg.get("training_cfg") is not None
        if not is_custom:
            stage_cfg_path = Training.save_stage_hydra_config(self.stage_cfg, job_path, self.cfg)
        else:
            stage_cfg_path = job_path.config_file

        # Make cluster parameters
        cluster_parameters = self._make_cluster_parameters(self.cluster)

        cluster_parameters["train_script_text"] = self._make_train_script_text(stage_cfg_path)
        cluster_parameters["hostfile"] = self._get_hostfile_location()
        cluster_parameters["nodeid"] = self._get_nodeid_location()

        # Make k8s config file if necessary
        if self.cluster == "k8s":
            # template_root will be overrided to use local ones
            template_root = None
            self._make_k8s_spec_file(template_root, cluster_parameters, job_path, stage_cfg_path)
            self._copy_k8s_helm_chart(template_root, job_path)

            # k8s does not need command groups
            command_groups = None
        else:
            command_groups = self.make_stage_command_groups(stage_cfg_path)
        # Create launcher, using SM cutomized launcher
        launcher = SMAutoLauncher(
            folder=job_path.folder,
            cluster=self.cluster,
            **cluster_parameters,
        )
        job_id = launcher.launch(command_groups=command_groups)

        return job_id

    def get_script_args_str(self, stage_cfg_path: Path) -> str:
        """
        Based on https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L608
        """
        if self.cluster == "k8s":
            return "--config-path=/config --config-name=config.yaml"
        return f"--config-path={stage_cfg_path.parents[0]} --config-name={stage_cfg_path.name}"

    def insert_git_token(self, repo_url: str, token: str) -> str:
        """
        Insert git token to git repo url. Currently only support github repo
        """

        host_name = urlparse(repo_url).hostname
        if "github.com" == host_name:
            splitted_url = repo_url.split("github.com", 1)
            repo_url = splitted_url[0] + self.cfg.git.token + "@github.com" + splitted_url[1]
        return repo_url

    def _make_nemo_path_command(self) -> List[str]:
        """Extend nemo path to python path"""
        # [TODO] clone the nemo/SFA/NxTT repo and handle point to the right path
        return super()._make_nemo_path_command()

    def _make_container_mounts_string(self) -> str:
        mounts_string = super()._make_container_mounts_string()
        # https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L264
        # We do not have data dir for custom launching
        mounts_string = mounts_string.replace(",None:None", "")
        return mounts_string

    def generate_default_k8s_value_template(self, template_root, cluster_parameters, stage_cfg_path=None):
        """
        Setting the general k8s configs that will be applicable for all device types and training methods
        """
        with open(os.path.join(template_root, "values.yaml")) as value_file:
            values_template = OmegaConf.load(value_file)
        values_template.image.trainingImage = cluster_parameters["container_image"]
        values_template.trainingConfig.jobName = self.stage_cfg.run.name
        # Cluster configs
        if "pullPolicy" in cluster_parameters:
            values_template.image.pullPolicy = cluster_parameters["pullPolicy"]
        values_template.trainingConfig.numEFADevices = self.num_efa_devices
        if "env_vars" in cluster_parameters:
            values_template.trainingConfig.envVars = cluster_parameters["env_vars"]
        if "restartPolicy" in cluster_parameters:
            values_template.trainingConfig.restartPolicy = cluster_parameters["restartPolicy"]
        if "persistent_volume_claims" in cluster_parameters:
            values_template.trainingConfig.persistentVolumeClaims = cluster_parameters["persistent_volume_claims"]
        if "volumes" in cluster_parameters:
            values_template.trainingConfig.volumes = cluster_parameters["volumes"]
        if cluster_parameters.get("namespace", None) is not None:
            values_template.trainingConfig.namespace = cluster_parameters["namespace"]
        if cluster_parameters.get("annotations", None) is not None:
            values_template.trainingConfig.annotations = cluster_parameters["annotations"]
        if cluster_parameters.get("priority_class_name", None) is not None:
            values_template.trainingConfig.priorityClassName = cluster_parameters["priority_class_name"]
        if cluster_parameters.get("service_account_name") is not None:
            values_template.trainingConfig.serviceAccountName = cluster_parameters["service_account_name"]
        if cluster_parameters.get("custom_labels", None) is not None:
            values_template.trainingConfig.customLabels = cluster_parameters["custom_labels"]
        if cluster_parameters.get("label_selector", None) is not None:
            values_template.trainingConfig.labelSelector = cluster_parameters["label_selector"]

        if self._default_repo is not None:
            values_template.trainingConfig.git.repo_url = self._default_repo

        # Git configs
        if self.cfg.get("git", None) is not None:
            if self.cfg.git.get("repo_url", None) is not None:
                repo_url = str(self.cfg.git.repo_url)
                if self.cfg.git.get("token", None) is not None:
                    repo_url = self.insert_git_token(repo_url, self.cfg.git.token)
                values_template.trainingConfig.git.repo_url = repo_url
            if self.cfg.git.get("branch", None) is not None:
                values_template.trainingConfig.git.branch = self.cfg.git.branch
            if self.cfg.git.get("commit", None) is not None:
                values_template.trainingConfig.git.commit = self.cfg.git.commit

        values_template.trainingConfig.device = self.device
        values_template.trainingConfig.scriptArgs = self.get_script_args_str(stage_cfg_path)
        return values_template

    def write_value_template(self, values_template, job_path):
        """
        Write the value template into disk
        """
        k8s_template_path = job_path.folder
        k8s_template_file = Path(k8s_template_path / "k8s_template" / "values.yaml")
        k8s_template_file.parent.mkdir(parents=True, exist_ok=True)

        conf = OmegaConf.create(values_template)
        OmegaConf.save(conf, k8s_template_file)

    def update_stage_specific_k8s_values(self, values_template):
        """
        Update the k8s configs that is related to the current stage
        """
        values_template.trainingConfig.ntasksPerNode = self.stage_cfg.trainer.devices
        values_template.trainingConfig.nodes = self.stage_cfg.trainer.num_nodes
        choice_model_type, _ = self.get_stage_config_choice()
        if self.cfg.git.get("entry_script", None) is not None:
            # Override with customer fed entry script
            values_template.trainingConfig.scriptPath = self.cfg.git.entry_script
        else:
            values_template.trainingConfig.scriptPath = str(self._entry_script_path)
        return values_template

    def _make_k8s_spec_file(
        self, template_root: str, cluster_parameters: Dict, job_path: JobPaths, stage_cfg_path=None
    ):
        """
        Referring from https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L669
        Break the function into 3 parts so we can easily override in different stages
        - Create general k8s configs that will be applicable for all device types and training methods
        - Update stage specific k8s configs
        - Write k8s configs to disk as value.yaml, which will be consumed by helm
        """
        #  Need to override the template_root to use our templates
        # [TODO] Currently hard-code it to do the stage as training
        template_root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            f"k8s_templates/training",
        )
        values_template = self.generate_default_k8s_value_template(template_root, cluster_parameters, stage_cfg_path)
        values_template = self.update_stage_specific_k8s_values(values_template)
        self.write_value_template(values_template, job_path)

    def _copy_k8s_helm_chart(self, template_root: str, job_path: JobPaths):
        #  Need to override the template_root to use our templates
        # [TODO] Currently hard-code it to do the stage as training
        template_root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            f"k8s_templates/training",
        )
        super()._copy_k8s_helm_chart(template_root, job_path)

    def get_env_vars(self) -> Dict:
        """
        Set up dictionary for environment variables
        By default injecting the EFA env variable when doing multi-node training
        The environment variables from hydra config will be set inside the job scripts.
        For Example:
            Set `env_vars.NVTE_BIAS_DROPOUT_FUSION=1` while calling nemo_launcherlauncher-scripts,
            `NVTE_BIAS_DROPOUT_FUSION=1` will be set while running the job.

        :return: a dictionary of env vars while running the job.
        :rtype: Dict
        """
        env_vars = super().get_env_vars()
        stage_cfg = self.stage_cfg
        nodes = get_num_nodes(stage_cfg)
        if int(nodes) > 1:
            env_vars = set_multinode_envs(env_vars, self.instance_type)
        return env_vars


class SMCustomTraining(SMTraining):
    """
    Base stage for the custom training on Sagemaker.
    """

    @property
    def _entry_script_path(self) -> Path:
        return Path(self.stage_cfg.entry_script)

    def setup_stage_vars(self, cfg):
        """Setup the stage vars, i.e. stage name and stage cfg"""
        self.stage_name = "custom_training_sm"
        self.stage_cfg = cfg.get("training_cfg")

    def get_script_args_str(self, stage_cfg_path=None):
        """
        Getting all script args and make it as a str
        """
        arg_str = []
        if self.stage_cfg.get("script_args", None) is not None:
            # script_args will be a list of dict which has key of arg_name and value of arg_value
            for arg in list(self.stage_cfg.script_args):
                for key, val in arg.items():
                    arg_str.append(f"{key} {val} ")
        return "".join(arg_str)

    def update_stage_specific_k8s_values(self, values_template):
        """
        Custom training specifc k8s values
        """
        values_template.trainingConfig.ntasksPerNode = get_ntasks_per_node(self.stage_cfg)
        values_template.trainingConfig.nodes = get_num_nodes(self.stage_cfg)
        values_template.trainingConfig.scriptPath = self.stage_cfg.entry_script
        values_template.trainingConfig.customScript = True
        return values_template

    def _copy_k8s_helm_chart(self, template_root: str, job_path: JobPaths):
        #  Need to override the template_root to use our templates
        # [TODO] Currently hard-code it to do the stage as training
        template_root = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            f"k8s_templates/training",
        )
        # For custom run, there is no need for training config files
        # Only creating training.yaml, Chart.yaml
        template_file = os.path.join(template_root, "training.yaml")
        chart_file = os.path.join(template_root, "Chart.yaml")
        training_path = Path(job_path.folder / "k8s_template" / "templates" / "training.yaml")
        training_path.parent.mkdir(parents=True, exist_ok=True)
        chart_path = Path(job_path.folder / "k8s_template" / "Chart.yaml")

        shutil.copy2(template_file, training_path)
        shutil.copy2(chart_file, chart_path)

    def _make_cluster_parameters(self, cluster: str) -> Dict:
        """
        Make a cluster-specific parameters for jobs on different clusters.

        :param str cluster: i.e. `bcm`, `bcp`, `interactive`, etc.
        :return: a dictionary of cluster parameters, e.g. `ntasks_per_node`
        :rtype: Dict
        """
        with omegaconf.open_dict(self.cfg):
            # Patch self.cfg.cluster to align with
            # https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L312
            origin_cluster = self.cfg.cluster
            self.cfg.cluster = self.cfg.cluster.cluster_config
            cluster_parameters = super()._make_cluster_parameters(cluster)
            cluster_type = origin_cluster.get("cluster_type")
            if cluster_type == "k8s":
                env_vars = cluster_parameters.get("env_vars")
                if env_vars and "SLURM_NTASKS_PER_NODE" in env_vars:
                    env_vars.pop("SLURM_NTASKS_PER_NODE")
            self.cfg.cluster = origin_cluster
        return cluster_parameters


class SMCustomTrainingGPU(SMCustomTraining):
    """
    Stage for training with custom stage on GPU
    """

    @property
    def _cuda_visible_devices(self) -> str:
        ntasks_per_node = get_ntasks_per_node(self.stage_cfg)
        if ntasks_per_node is None:
            ntasks_per_node = 8
        return (
            "CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7"
            if ntasks_per_node == 8
            else f"CUDA_VISIBLE_DEVICES={','.join(map(str, range(ntasks_per_node)))}"
        )

    @property
    def _set_ln_sm_margin(self) -> str:
        return ""

    @property
    def _skip_ag_overlap(self) -> str:
        return ""


class SMCustomTrainingCPU(SMCustomTrainingGPU):
    """
    Stage for custom training on CPU
    """

    def __init__(self, cfg):
        super().__init__(cfg)
        self.device = "cpu"

    @property
    def _cuda_visible_devices(self) -> str:
        return ""


class SMCustomTrainingTrainium(SMCustomTraining):
    """
    Stage for custom training on Trainium
    """

    def __init__(self, cfg):
        super().__init__(cfg)
        self.device = "trainium"

    def make_stage_command_groups(self, stage_cfg_path: Path) -> List[List[str]]:
        """
        Make the command groups for current stage
        Command groups is a list of command group. A command group is defined as:
              0. Command group is a list of command strings
              1. Each command group occupies one bcprun, srun or bash
              2. Each command group eventually has multiple commands connected by ";"

        :param Path stage_cfg_path: path to interpolated and saved configuration
        :return: command groups for current stage
        :rtype: List[List[str]]
        """

    def update_stage_specific_k8s_values(self, values_template):
        """
        Custom training specifc k8s values for trainum
        """
        super().update_stage_specific_k8s_values(values_template)
        values_template.trainingConfig.numNeuronDevices = get_num_accelerator_devices(self.instance_type)
        return values_template
