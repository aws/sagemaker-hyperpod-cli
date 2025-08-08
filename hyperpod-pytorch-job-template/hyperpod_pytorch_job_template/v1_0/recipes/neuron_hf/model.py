from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    results_dir: Optional[str] = None
    time_limit: Optional[str] = None
    model_type: Optional[str] = None
    compile: Optional[int] = None


class TrainerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    devices: Optional[int] = None
    num_nodes: Optional[int] = None
    max_epochs: Optional[int] = None
    max_steps: Optional[int] = None
    log_every_n_steps: Optional[int] = None
    val_check_interval: Optional[int] = None
    check_val_every_n_epoch: Optional[int] = None
    num_sanity_val_steps: Optional[int] = None
    limit_val_batches: Optional[float] = None
    limit_test_batches: Optional[float] = None
    gradient_clip_val: Optional[float] = None


class CheckpointCallbackParamsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monitor: Optional[str] = None
    save_top_k: Optional[int] = None
    mode: Optional[str] = None
    save_last: Optional[bool] = None
    filename: Optional[str] = None
    model_parallel_size: Optional[int] = None
    every_n_train_steps: Optional[int] = None


class ExpManagerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_local_rank_0_only: Optional[bool] = None
    create_tensorboard_logger: Optional[bool] = None
    summary_writer_kwargs: Optional[Dict[str, str]] = None
    create_mlflow_logger: Optional[bool] = None
    mlflow_logger_kwargs: Optional[Dict[str, str]] = None
    create_wandb_logger: Optional[bool] = None
    wandb_logger_kwargs: Optional[Dict[str, str]] = None
    explicit_log_dir: Optional[str] = None
    exp_dir: Optional[str] = None
    name: Optional[str] = None
    resume_if_exists: Optional[bool] = None
    resume_ignore_no_checkpoint: Optional[bool] = None
    create_checkpoint_callback: Optional[bool] = None
    checkpoint_callback_params: Optional[CheckpointCallbackParamsConfig] = None
    log_parameter_norm: Optional[bool] = None
    log_gradient_norm: Optional[bool] = None
    enable_recovery_time_instrumentation: Optional[bool] = None
    save_xser: Optional[bool] = None
    load_xser: Optional[bool] = None
    save_bf16: Optional[bool] = None
    async_checkpointing: Optional[bool] = None
    resume_from_checkpoint: Optional[str] = None


class DistributedStrategyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tensor_model_parallel_size: Optional[int] = None
    pipeline_model_parallel_size: Optional[int] = None
    virtual_pipeline_model_parallel_size: Optional[int] = None
    zero1: Optional[bool] = None
    sequence_parallel: Optional[bool] = None
    kv_replicator: Optional[int] = None


class TokenizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Optional[str] = None


class DataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    micro_batch_size: Optional[int] = None
    global_batch_size: Optional[int] = None
    train_dir: Optional[str] = None
    val_dir: Optional[str] = None
    packing: Optional[bool] = None
    use_sft_style_data_module: Optional[bool] = None
    dev_choose_samples: Optional[int] = None
    seq_length: Optional[int] = None
    tokenizer: Optional[TokenizerConfig] = None


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    warmup_steps: Optional[int] = None
    max_steps: Optional[int] = None


class OptimizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    lr: Optional[float] = None
    weight_decay: Optional[float] = None
    capturable: Optional[bool] = None
    betas: Optional[List[float]] = None
    sched: Optional[SchedulerConfig] = None


class FusionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    softmax: Optional[bool] = None
    flash_attention: Optional[bool] = None


class ModelConfig(BaseModel):
    # Allow additional field as some recipes have "model_config" field and
    # this name is not allowed in Pydantic
    model_config = ConfigDict(extra="allow")

    encoder_seq_length: Optional[int] = None
    max_position_embeddings: Optional[int] = None
    num_layers: Optional[int] = None
    hidden_size: Optional[int] = None
    qkv_linear: Optional[bool] = None
    rope_theta: Optional[float] = None
    use_cpu_initialization: Optional[bool] = None
    weight_init_only: Optional[bool] = None
    activations_checkpoint_granularity: Optional[str] = None
    fusions: Optional[FusionsConfig] = None
    do_layer_norm_weight_decay: Optional[bool] = None
    optim: Optional[OptimizerConfig] = None


class PrecisionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Optional[str] = None
    master_weights: Optional[bool] = None
    fp32_grad_acc: Optional[bool] = None
    xla_use_bf16: Optional[str] = None
    xla_downcast_bf16: Optional[str] = None
    neuron_rt_stochastic_rounding_en: Optional[str] = None


class NeuronHfRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    """Schema for neuron-hf SageMaker HyperPod recipes."""

    # Common configurations
    run: RunConfig
    name: Optional[str] = None
    model_source: Optional[str] = None
    seed: Optional[int] = None

    # Training configurations
    trainer: Optional[TrainerConfig] = None
    exp_manager: Optional[ExpManagerConfig] = None
    distributed_strategy: Optional[DistributedStrategyConfig] = None
    data: Optional[DataConfig] = None
    model: Optional[ModelConfig] = None
    precision: Optional[PrecisionConfig] = None

    # Neuron-specific configurations
    compiler_flags: Optional[str] = None
    compiler_cache_url: Optional[str] = None
    aync_exec_max_inflight_requests: Optional[int] = None
    bucket_size_collectives: Optional[int] = None
    neuron_rt_exec_timeout: Optional[int] = None
    neuron_experimental_compress_rg: Optional[bool] = None
