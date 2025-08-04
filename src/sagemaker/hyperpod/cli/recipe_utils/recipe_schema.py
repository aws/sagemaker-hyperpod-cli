from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class RunConfig(BaseModel):
    name: Optional[str] = None
    results_dir: Optional[str] = None
    time_limit: Optional[str] = None
    model_type: Optional[str] = None
    model_name_or_path: Optional[str] = None
    replicas: Optional[int] = None
    data_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None


class TrainerConfig(BaseModel):
    devices: Optional[int] = None
    num_nodes: Optional[int] = None
    accelerator: Optional[str] = None
    precision: Optional[str] = None
    max_steps: Optional[int] = None
    log_every_n_steps: Optional[int] = None
    val_check_interval: Optional[Union[int, float]] = None
    limit_val_batches: Optional[Union[int, float]] = None


class CheckpointCallbackParams(BaseModel):
    save_top_k: Optional[int] = None
    every_n_train_steps: Optional[int] = None
    monitor: Optional[str] = None
    mode: Optional[str] = None
    save_last: Optional[bool] = None


class AutoCheckpoint(BaseModel):
    enabled: Optional[bool] = None


class ExportFullModel(BaseModel):
    every_n_train_steps: Optional[int] = None
    save_last: Optional[bool] = None


class ExpManagerConfig(BaseModel):
    exp_dir: Optional[str] = None
    name: Optional[str] = None
    create_tensorboard_logger: Optional[bool] = None
    summary_writer_kwargs: Optional[Dict[str, Any]] = None
    create_mlflow_logger: Optional[bool] = None
    mlflow_logger_kwargs: Optional[Dict[str, Any]] = None
    create_wandb_logger: Optional[bool] = None
    wandb_logger_kwargs: Optional[Dict[str, Any]] = None
    create_checkpoint_callback: Optional[bool] = None
    checkpoint_callback_params: Optional[CheckpointCallbackParams] = None
    checkpoint_dir: Optional[str] = None
    resume_from_checkpoint: Optional[str] = None
    auto_checkpoint: Optional[AutoCheckpoint] = None
    export_full_model: Optional[ExportFullModel] = None


class RopeScaling(BaseModel):
    rope_type: Optional[str] = None
    factor: Optional[float] = None
    high_freq_factor: Optional[float] = None
    low_freq_factor: Optional[float] = None
    original_max_position_embeddings: Optional[int] = None


class PeftConfig(BaseModel):
    peft_type: Optional[str] = None
    rank: Optional[int] = None
    alpha: Optional[int] = None
    dropout: Optional[float] = None


class SchedulerConfig(BaseModel):
    name: Optional[str] = None
    warmup_steps: Optional[int] = None
    constant_steps: Optional[int] = None
    min_lr: Optional[float] = None


class OptimizerConfig(BaseModel):
    name: Optional[str] = None
    lr: Optional[float] = None
    weight_decay: Optional[float] = None
    betas: Optional[List[float]] = None
    sched: Optional[SchedulerConfig] = None


class DataConfig(BaseModel):
    train_dir: Optional[str] = None
    val_dir: Optional[str] = None
    dataset_type: Optional[str] = None
    use_synthetic_data: Optional[bool] = None


class VizTracerConfig(BaseModel):
    enabled: Optional[bool] = None


class ModelConfig(BaseModel):
    model_type: Optional[str] = None
    train_batch_size: Optional[int] = None
    val_batch_size: Optional[int] = None
    seed: Optional[int] = None
    grad_clip: Optional[float] = None
    log_reduced_training_loss: Optional[bool] = None
    
    # Memory saving/distributed training configs
    tensor_model_parallel_degree: Optional[int] = None
    expert_model_parallel_degree: Optional[int] = None
    context_parallel_degree: Optional[int] = None
    moe: Optional[bool] = None
    activation_checkpointing: Optional[bool] = None
    activation_loading_horizon: Optional[int] = None
    delayed_param: Optional[bool] = None
    offload_activations: Optional[bool] = None
    
    # FSDP Configs
    sharding_strategy: Optional[str] = None
    forward_prefetch: Optional[bool] = None
    shard_degree: Optional[int] = None
    backward_fetch_policy: Optional[str] = None
    auto_wrap_policy: Optional[str] = None
    limit_all_gathers: Optional[bool] = None
    use_orig_param: Optional[bool] = None
    
    # FP8 config
    fp8: Optional[bool] = None
    fp8_amax_history_len: Optional[int] = None
    fp8_amax_compute_algo: Optional[str] = None
    
    # Model architecture
    max_context_width: Optional[int] = None
    max_position_embeddings: Optional[int] = None
    num_hidden_layers: Optional[int] = None
    hidden_size: Optional[int] = None
    num_attention_heads: Optional[int] = None
    intermediate_size: Optional[int] = None
    initializer_range: Optional[float] = None
    layernorm_epsilon: Optional[float] = None
    vocab_size: Optional[int] = None
    num_key_value_heads: Optional[int] = None
    use_flash_attention: Optional[bool] = None
    rope_theta: Optional[float] = None
    rope_scaling: Optional[RopeScaling] = None
    tie_word_embeddings: Optional[bool] = None
    
    # Finetuning config
    do_finetune: Optional[bool] = None
    hf_model_name_or_path: Optional[str] = None
    hf_access_token: Optional[str] = None
    peft: Optional[PeftConfig] = None
    
    precision: Optional[str] = None
    lr_decay_iters: Optional[int] = None
    optim: Optional[OptimizerConfig] = None
    data: Optional[DataConfig] = None
    viztracer: Optional[VizTracerConfig] = None


class EvaluationConfig(BaseModel):
    task: Optional[str] = None
    strategy: Optional[str] = None
    metric: Optional[str] = None
    subtask: Optional[str] = None


class InferenceConfig(BaseModel):
    max_new_tokens: Optional[int] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None


class RecipeSchema(BaseModel):
    class Config:
        extra = 'forbid'
    """Unified schema for all SageMaker HyperPod recipe types."""
    
    # Common configurations
    run: RunConfig
    
    # Training and fine-tuning specific configurations
    trainer: Optional[TrainerConfig] = None
    exp_manager: Optional[ExpManagerConfig] = None
    use_smp_model: Optional[bool] = None
    distributed_backend: Optional[str] = None
    model: Optional[ModelConfig] = None
    
    # Evaluation specific configurations
    evaluation: Optional[EvaluationConfig] = None
    
    # Inference specific configurations
    inference: Optional[InferenceConfig] = None