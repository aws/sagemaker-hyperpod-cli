import math
import os
import sys

from .validations_wrapper import validate_config

LAUNCHER_SCRIPT_PATH = (
    f"{os.path.dirname(os.path.abspath(__file__))}/launcher/nemo/nemo_framework_launcher/launcher_scripts/"
)
sys.path.append(LAUNCHER_SCRIPT_PATH)

import hydra
import omegaconf
from nemo_launcher.core.data_curation_stages import QualityFiltering
from nemo_launcher.core.data_stages import (
    CustomDataPreparation,
    MC4DataPreparation,
    PileDataPreparation,
)
from nemo_launcher.core.export_stages import Export
from nemo_launcher.core.rlhf_stages import RLHFPPO, RLHFRewardModel
from nemo_launcher.core.stages import (
    PEFT,
    AdapterLearning,
    Conversion,
    EvalHarnessEvaluation,
    FineTuning,
    IA3Learning,
    NeMoEvaluation,
    PromptLearning,
)

from .launcher.accelerator_devices import (
    get_num_accelerator_devices,
    get_num_cores_per_accelerator,
)
from .launcher.nemo.stages import (
    SMCustomTrainingCPU,
    SMCustomTrainingGPU,
    SMCustomTrainingTrainium,
    get_instance_type,
)

omegaconf.OmegaConf.register_new_resolver("multiply", lambda x, y: x * y, replace=True)
omegaconf.OmegaConf.register_new_resolver("divide_ceil", lambda x, y: int(math.ceil(x / y)), replace=True)
omegaconf.OmegaConf.register_new_resolver("divide_floor", lambda x, y: int(math.floor(x / y)), replace=True)

STR2STAGECLASS = {
    "fine_tuning": FineTuning,
    "peft": PEFT,
    "prompt_learning": PromptLearning,
    "adapter_learning": AdapterLearning,
    "ia3_learning": IA3Learning,
    "conversion": Conversion,
    "export": Export,
    "evaluation": {
        EvalHarnessEvaluation: ["gpt3", "prompt_gpt3", "llama", "prompt_llama"],
        NeMoEvaluation: [
            "t5",
            "mt5",
            "prompt_t5",
            "prompt_mt5",
            "adapter_t5",
            "adapter_gpt3",
            "ia3_t5",
            "ia3_gpt3",
            "peft_llama",
        ],
    },
    "data_preparation": {
        PileDataPreparation: ["gpt3", "t5", "bert", "llama"],
        MC4DataPreparation: ["mt5"],
        CustomDataPreparation: ["generic"],
    },
    "rlhf_rm": RLHFRewardModel,
    "rlhf_ppo": RLHFPPO,
    "quality_filtering": QualityFiltering,
}


def get_training_stage(cfg):
    """
    Get the right training stage based on the device type and if it is custom training
    """
    instance_type = get_instance_type(cfg)
    # p and g instances are GPU instances
    if instance_type.startswith("p") or instance_type.startswith("g"):
        device_type = "gpu"
    elif instance_type.startswith("trn"):
        device_type = "trainium"
    else:
        device_type = "cpu"
    if cfg.get("training_cfg") is None:
        raise ValueError("Please provide training_cfg in the YAML file")
    else:
        if device_type == "gpu":
            return SMCustomTrainingGPU
        if device_type == "trainium":
            return SMCustomTrainingTrainium
        return SMCustomTrainingCPU


def preprocess_config(cfg):
    with omegaconf.open_dict(cfg):
        cfg.launcher_scripts_path = LAUNCHER_SCRIPT_PATH
    # Override the cluster type to align with NeMo
    if cfg.get("cluster_type") is None:
        assert cfg.get("cluster") is not None
        cluster_type = cfg.cluster.cluster_type
    else:
        cluster_type = cfg.cluster_type

    with omegaconf.open_dict(cfg):
        if cluster_type == "slurm":
            cfg.cluster_type = "bcm"
        else:
            cfg.cluster_type = cluster_type

    if cfg.get("wandb_api_key_file") is None:
        with omegaconf.open_dict(cfg):
            cfg.wandb_api_key_file = None

    if cfg.get("wandb_api_bcp_secret_key") is None:
        with omegaconf.open_dict(cfg):
            cfg.wandb_api_bcp_secret_key = None

    if cfg.get("training_cfg") is not None:
        assert cfg.get("stages") is None, "training_cfg and stages should not set together"
        stage_cfg = cfg.get("training_cfg")
        assert stage_cfg.get("run") is not None, "run config should be set"
        run_config = stage_cfg.get("run")
        if run_config.get("ntasks_per_node") is not None:
            ntasks_per_node = run_config.get("ntasks_per_node")
        else:
            instance_type = cfg.cluster.get("instance_type")
            if instance_type is not None and get_num_accelerator_devices(instance_type) is not None:
                ntasks_per_node = get_num_accelerator_devices(instance_type) * get_num_cores_per_accelerator(
                    instance_type
                )
            else:
                ntasks_per_node = 8
        # To align with https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L721
        with omegaconf.open_dict(stage_cfg):
            stage_cfg.trainer = {"devices": ntasks_per_node}
            with omegaconf.open_dict(run_config):
                run_config.ntasks_per_node = ntasks_per_node
                run_config.results_dir = f"{cfg.base_results_dir}/{run_config.name}"
        # To align with https://github.com/NVIDIA/NeMo-Framework-Launcher/blob/23.11/launcher_scripts/nemo_launcher/core/stages.py#L313C54-L313C72
        with omegaconf.open_dict(cfg):
            cfg.training = {"model": {"ub_tp_comm_overlap": False}}
        print(cfg)
        return True
    return False


@hydra.main(config_path="conf", config_name="config", version_base="1.2")
@validate_config
def main(cfg):
    custom_script = preprocess_config(cfg)

    if custom_script:
        stage_class = get_training_stage(cfg)
        stage = stage_class(cfg)
        job_id = stage.run()
    else:
        requested_stages = cfg.get("stages")

        dependency = None
        for stage_name in requested_stages:
            # Get our training stages
            if stage_name == "training":
                stage_class = get_training_stage(cfg)
            else:
                stage_class = STR2STAGECLASS[stage_name]
            if isinstance(stage_class, dict):
                stage_config_choice = cfg.get(f"{stage_name}_config")
                choice_model_type = stage_config_choice.rsplit("/", 1)[0]
                for cls, model_types in stage_class.items():
                    if choice_model_type in model_types:
                        stage_class = cls
                        break

            if dependency is not None:
                cfg[stage_name]["run"]["dependency"] = dependency
            stage = stage_class(cfg)
            job_id = stage.run()

            job_path = stage.get_job_path()
            command = " \\\n  ".join(sys.argv)
            with open(job_path.folder / "launcher_cmd.log", "w") as f:
                f.write(command)

            if job_id:
                dependency = f"afterany:{job_id}"


if __name__ == "__main__":
    main()
