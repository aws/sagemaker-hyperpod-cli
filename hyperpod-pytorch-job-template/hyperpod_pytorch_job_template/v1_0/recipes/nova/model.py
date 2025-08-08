from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    model_type: Optional[str] = None
    model_name_or_path: Optional[str] = None
    replicas: Optional[int] = None
    data_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None

    # PPO-specific replica configurations
    actor_train_replicas: Optional[int] = None
    rm_replicas: Optional[int] = None
    cm_replicas: Optional[int] = None
    actor_generation_replicas: Optional[int] = None
    am_replicas: Optional[int] = None


class TrainerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_epochs: Optional[int] = None
    num_nodes: Optional[int] = None


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warmup_steps: Optional[int] = None
    constant_steps: Optional[int] = None
    min_lr: Optional[float] = None


class OptimizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    lr: Optional[float] = None
    adam_w_mode: Optional[bool] = None
    eps: Optional[float] = None
    weight_decay: Optional[float] = None
    betas: Optional[List[float]] = None
    sched: Optional[SchedulerConfig] = None


class DpoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beta: Optional[float] = None


class LoraTuningConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    loraplus_lr_ratio: Optional[float] = None
    alpha: Optional[float] = None
    adapter_dropout: Optional[float] = None


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
    global_batch_size: Optional[int] = None
    ent_coeff: Optional[float] = None
    clip_ratio: Optional[float] = None
    lam: Optional[float] = None
    kl_loss_coeff: Optional[float] = None
    kl_loss_type: Optional[str] = None
    kl_reward_penalty_coeff: Optional[float] = None


class TrainingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int] = None
    global_batch_size: Optional[int] = None
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None

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


class PpoRewardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoCriticConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoAnchorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int]
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class PpoActorGenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_model_max_length: Optional[int]
    trainer: Optional[TrainerConfig] = None


class PpoActorTrainConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_length: Optional[int] = None
    max_steps: Optional[int] = None
    actor_model_max_length: Optional[int] = None
    reward_model_max_length: Optional[int] = None
    trajectory_buffer_scale: Optional[int] = None
    trainer: Optional[TrainerConfig] = None
    model: Optional[ModelConfig] = None


class NovaRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Common configurations
    run: RunConfig

    # Training and fine-tuning specific configurations
    training_config: Optional[TrainingConfig] = None

    # PPO-specific configurations
    ppo_reward: Optional[PpoRewardConfig] = None
    ppo_critic: Optional[PpoCriticConfig] = None
    ppo_anchor: Optional[PpoAnchorConfig] = None
    ppo_actor_generation: Optional[PpoActorGenerationConfig] = None
    ppo_actor_train: Optional[PpoActorTrainConfig] = None
