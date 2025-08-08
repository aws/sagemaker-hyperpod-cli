from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    results_dir: Optional[str] = None
    time_limit: Optional[str] = None
    model_type: Optional[str] = None
    dependency: Optional[str] = None


class TrainerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    devices: Optional[int] = None
    num_nodes: Optional[int] = None
    accelerator: Optional[str] = None
    precision: Optional[str] = None
    max_steps: Optional[int] = None
    log_every_n_steps: Optional[int] = None
    val_check_interval: Optional[Union[int, float]] = None
    limit_val_batches: Optional[Union[int, float]] = None
    logger: Optional[bool] = None
    enable_checkpointing: Optional[bool] = None
    use_distributed_sampler: Optional[bool] = None
    max_epochs: Optional[int] = None
    max_time: Optional[str] = None
    limit_test_batches: Optional[int] = None
    accumulate_grad_batches: Optional[int] = None
    gradient_clip_val: Optional[float] = None


class CheckpointCallbackParamsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    save_top_k: Optional[int] = None
    every_n_train_steps: Optional[int] = None
    monitor: Optional[str] = None
    mode: Optional[str] = None
    save_last: Optional[bool] = None


class AutoCheckpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = None


class ExportFullModelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    every_n_train_steps: Optional[int] = None
    save_last: Optional[bool] = None


class TokenizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    library: Optional[str] = None
    type: Optional[str] = None
    model: Optional[str] = None
    delimiter: Optional[str] = None
    vocab_file: Optional[str] = None
    merge_file: Optional[str] = None
    sentencepiece_legacy: Optional[bool] = None


class StepTimingKwargsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sync_cuda: Optional[bool] = None
    buffer_size: Optional[int] = None


class ExpManagerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exp_dir: Optional[str] = None
    name: Optional[str] = None
    create_tensorboard_logger: Optional[bool] = None
    summary_writer_kwargs: Optional[Dict[str, Any]] = None
    create_mlflow_logger: Optional[bool] = None
    mlflow_logger_kwargs: Optional[Dict[str, Any]] = None
    create_wandb_logger: Optional[bool] = None
    wandb_logger_kwargs: Optional[Dict[str, Any]] = None
    create_checkpoint_callback: Optional[bool] = None
    checkpoint_callback_params: Optional[CheckpointCallbackParamsConfig] = None
    checkpoint_dir: Optional[str] = None
    resume_from_checkpoint: Optional[str] = None
    auto_checkpoint: Optional[AutoCheckpointConfig] = None
    export_full_model: Optional[ExportFullModelConfig] = None
    explicit_log_dir: Optional[str] = None
    resume_if_exists: Optional[bool] = None
    resume_ignore_no_checkpoint: Optional[bool] = None
    log_step_timing: Optional[bool] = None
    step_timing_kwargs: Optional[StepTimingKwargsConfig] = None


class RopeScalingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rope_type: Optional[str] = None
    factor: Optional[float] = None
    high_freq_factor: Optional[float] = None
    low_freq_factor: Optional[float] = None
    original_max_position_embeddings: Optional[int] = None


class PeftConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    peft_type: Optional[str] = None
    rank: Optional[int] = None
    alpha: Optional[int] = None
    dropout: Optional[float] = None
    target_modules: Optional[List[str]] = None


class SchedulerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    warmup_steps: Optional[int] = None
    constant_steps: Optional[int] = None
    min_lr: Optional[float] = None


class OptimizerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    lr: Optional[float] = None
    weight_decay: Optional[float] = None
    betas: Optional[List[float]] = None
    sched: Optional[SchedulerConfig] = None
    bucket_cap_mb: Optional[int] = None
    overlap_grad_sync: Optional[bool] = None
    overlap_param_sync: Optional[bool] = None
    contiguous_grad_buffer: Optional[bool] = None
    contiguous_param_buffer: Optional[bool] = None


class DataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    train_dir: Optional[str] = None
    val_dir: Optional[str] = None
    dataset_type: Optional[str] = None
    use_synthetic_data: Optional[bool] = None
    tokenizer_name: Optional[str] = None
    zipped_data: Optional[bool] = None
    data_impl: Optional[str] = None
    splits_string: Optional[str] = None
    seq_length: Optional[int] = None
    skip_warmup: Optional[bool] = None
    num_workers: Optional[int] = None
    dataloader_type: Optional[str] = None
    reset_position_ids: Optional[bool] = None
    reset_attention_mask: Optional[bool] = None
    eod_mask_loss: Optional[bool] = None
    index_mapping_dir: Optional[str] = None
    data_prefix: Optional[List[str]] = None


class VizTracerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = None


class DpoConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: Optional[bool] = None
    beta: Optional[float] = None
    label_smoothing: Optional[float] = None


class ModelConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_type: Optional[str] = None
    train_batch_size: Optional[int] = None
    val_batch_size: Optional[int] = None
    seed: Optional[int] = None
    grad_clip: Optional[float] = None
    log_reduced_training_loss: Optional[bool] = None

    # Additional model-specific fields found in recipes
    max_window_layers: Optional[int] = None
    rms_norm_eps: Optional[float] = None
    tie_word_embeddings: Optional[bool] = None
    use_sliding_window: Optional[bool] = None

    # Memory saving/distributed training configs
    tensor_model_parallel_degree: Optional[int] = None
    expert_model_parallel_degree: Optional[int] = None
    context_parallel_degree: Optional[int] = None
    moe: Optional[bool] = None
    sliding_window: Optional[int] = None
    num_experts_per_tok: Optional[int] = None
    num_local_experts: Optional[int] = None
    moe_load_balancing: Optional[str] = None
    global_token_shuffle: Optional[bool] = None
    moe_all_to_all_dispatcher: Optional[bool] = None
    activation_checkpointing: Optional[bool] = None
    activation_loading_horizon: Optional[int] = None
    delayed_param: Optional[bool] = None
    offload_activations: Optional[bool] = None
    multi_modal: Optional[bool] = None

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
    rope_scaling: Optional[RopeScalingConfig] = None

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
    dpo: Optional[DpoConfig] = None

    # Megatron-specific fields
    mcore_gpt: Optional[bool] = None
    micro_batch_size: Optional[int] = None
    global_batch_size: Optional[int] = None
    rampup_batch_size: Optional[int] = None
    pipeline_model_parallel_size: Optional[int] = None
    virtual_pipeline_model_parallel_size: Optional[int] = None
    encoder_seq_length: Optional[int] = None
    ffn_hidden_size: Optional[int] = None
    num_query_groups: Optional[int] = None
    init_method_std: Optional[float] = None
    use_scaled_init_method: Optional[bool] = None
    kv_channels: Optional[int] = None
    apply_query_key_layer_scaling: Optional[bool] = None
    normalization: Optional[str] = None
    do_layer_norm_weight_decay: Optional[bool] = None
    make_vocab_size_divisible_by: Optional[int] = None
    pre_process: Optional[bool] = None
    post_process: Optional[bool] = None
    persist_layer_norm: Optional[bool] = None
    bias: Optional[bool] = None
    activation: Optional[str] = None
    headscale: Optional[bool] = None
    transformer_block_type: Optional[str] = None
    openai_gelu: Optional[bool] = None
    normalize_attention_scores: Optional[bool] = None
    position_embedding_type: Optional[str] = None
    rotary_percentage: Optional[float] = None
    apply_rope_fusion: Optional[bool] = None
    cross_entropy_loss_fusion: Optional[bool] = None
    attention_type: Optional[str] = None
    share_embeddings_and_output_weights: Optional[bool] = None
    scale_positional_embedding: Optional[bool] = None
    tokenizer: Optional[TokenizerConfig] = None
    native_amp_init_scale: Optional[int] = None
    native_amp_growth_interval: Optional[int] = None
    hysteresis: Optional[int] = None
    fp32_residual_connection: Optional[bool] = None
    fp16_lm_cross_entropy: Optional[bool] = None
    megatron_amp_O2: Optional[bool] = None
    grad_allreduce_chunk_size_mb: Optional[int] = None
    grad_div_ar_fusion: Optional[bool] = None
    gradient_accumulation_fusion: Optional[bool] = None
    bias_activation_fusion: Optional[bool] = None
    bias_dropout_add_fusion: Optional[bool] = None
    masked_softmax_fusion: Optional[bool] = None
    resume_from_checkpoint: Optional[str] = None
    use_cpu_initialization: Optional[bool] = None
    onnx_safe: Optional[bool] = None
    apex_transformer_log_level: Optional[int] = None
    gradient_as_bucket_view: Optional[bool] = None
    sync_batch_comm: Optional[bool] = None
    activations_checkpoint_granularity: Optional[str] = None
    activations_checkpoint_method: Optional[str] = None
    activations_checkpoint_num_layers: Optional[int] = None
    num_micro_batches_with_partial_activation_checkpoints: Optional[int] = None
    activations_checkpoint_layers_per_pipeline: Optional[int] = None
    sequence_parallel: Optional[bool] = None
    deterministic_mode: Optional[bool] = None
    transformer_engine: Optional[bool] = None
    fp8_e4m3: Optional[bool] = None
    fp8_hybrid: Optional[bool] = None
    fp8_margin: Optional[int] = None
    fp8_interval: Optional[int] = None
    use_emha: Optional[bool] = None
    ub_tp_comm_overlap: Optional[bool] = None


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: Optional[str] = None
    strategy: Optional[str] = None
    metric: Optional[str] = None
    subtask: Optional[str] = None


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_new_tokens: Optional[int] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None


class HfRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
