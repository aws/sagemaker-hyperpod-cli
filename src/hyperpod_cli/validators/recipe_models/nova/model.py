from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    model_type: Optional[str] = None
    model_name_or_path: Optional[str] = None
    replicas: Optional[int|str] = None
    data_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None
    validation_data_s3_path: Optional[str] = None

    # PPO-specific replica configurations
    actor_train_replicas: Optional[int|str] = None
    rm_replicas: Optional[int|str] = None
    cm_replicas: Optional[int|str] = None
    actor_generation_replicas: Optional[int|str] = None
    am_replicas: Optional[int|str] = None


    # MLFlow optional parameters
    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: Optional[str] = None
    mlflow_run_name: Optional[str] = None


class TrainerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_epochs: Optional[int|str] = None
    num_nodes: Optional[int|str] = None
    max_steps: Optional[int|str] = None
    val_check_interval: Optional[int|float|str] = None
    limit_val_batches: Optional[int|float|str] = None


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warmup_steps: Optional[int|str] = None
    constant_steps: Optional[int|str] = None
    min_lr: Optional[float] = None


class OptimizerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    lr: Optional[float] = None
    adam_w_mode: Optional[bool] = None
    eps: Optional[float] = None
    weight_decay: Optional[float] = None
    betas: Optional[List[float]] = None
    sched: Optional[SchedulerConfig] = None
    adam_beta1: Optional[float] = None
    adam_beta2: Optional[float] = None


class DpoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beta: Optional[float] = None


class LoraTuningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    loraplus_lr_ratio: Optional[float] = None
    alpha: Optional[float] = None
    adapter_dropout: Optional[float] = None
    lora_plus_lr_ratio: Optional[float] = None


class PeftConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peft_scheme: Optional[str] = None
    lora_tuning: Optional[LoraTuningConfig] = None


class ModelConfig(BaseModel):
    hidden_dropout: Optional[float] = None
    attention_dropout: Optional[float] = None
    ffn_dropout: Optional[float] = None
    optim: Optional[OptimizerConfig] = None
    dpo_cfg: Optional[DpoConfig] = None
    peft: Optional[PeftConfig] = None
    global_batch_size: Optional[int|str] = None
    ent_coeff: Optional[float] = None
    clip_ratio: Optional[float] = None
    lam: Optional[float] = None
    kl_loss_coeff: Optional[float] = None
    kl_loss_type: Optional[str] = None
    kl_reward_penalty_coeff: Optional[float] = None


class ModelImportanceScore(BaseModel):
    fine_tuned_model: Optional[float] = None


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_length: Optional[int|str] = None
    global_batch_size: Optional[int|str] = None
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None
    max_steps: Optional[int|str] = None
    save_steps: Optional[int | str] = None
    save_top_k: Optional[int | str] = None
    reasoning_enabled: Optional[int | str] = None
    lr_scheduler: Optional[SchedulerConfig] = None

    # Distillation-specific fields
    distillation_data: Optional[str] = None
    maxNumberOfPrompts: Optional[str] = None
    maxResponseLength: Optional[str] = None
    minNumberOfPrompts: Optional[str] = None
    maxInputFileSizeInGB: Optional[str] = None
    maxLineLengthInKB: Optional[str] = None
    maxStudentModelFineTuningContextLengthInTokens: Optional[str] = None
    teacherModelId: Optional[str] = None
    temperature: Optional[str] = None
    top_p: Optional[str] = None
    customer_bucket: Optional[str] = None
    kms_key: Optional[str] = None
    task_type: Optional[str] = None
    optim: Optional[OptimizerConfig] = None

    optim_config: Optional[OptimizerConfig] = None
    peft: Optional[PeftConfig] = None

    # RAI vector merge
    model_importance_score: Optional[ModelImportanceScore] = None


class PpoRewardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int|str]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoCriticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int|str]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoAnchorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int|str]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoActorGenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_model_max_length: Optional[int|str]
    trainer: Optional[TrainerConfig] = None


class PpoActorTrainConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int|str] = None
    max_steps: Optional[int|str] = None
    actor_model_max_length: Optional[int|str] = None
    reward_model_max_length: Optional[int|str] = None
    trajectory_buffer_scale: Optional[int|str] = None
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class NovaRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = None
    versions: Optional[list] = None
    instance_types: Optional[list] = None

    # Common configurations
    run: RunConfig

    # Training and fine-tuning specific configurations
    training_config: Optional[TrainingConfig] = None

    # Enable skipping recipe validation in the container
    # This is controlled by an allowlist in the container
    skip_recipe_validation: Optional[bool] = None

    # PPO-specific configurations
    ppo_reward: Optional[PpoRewardConfig] = None
    ppo_critic: Optional[PpoCriticConfig] = None
    ppo_anchor: Optional[PpoAnchorConfig] = None
    ppo_actor_generation: Optional[PpoActorGenerationConfig] = None
    ppo_actor_train: Optional[PpoActorTrainConfig] = None