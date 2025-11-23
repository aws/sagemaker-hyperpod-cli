from typing import Optional
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    model_type: Optional[str] = None
    model_name_or_path: Optional[str] = None
    replicas: Optional[int|str] = None
    data_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None
    mlflow_tracking_uri: Optional[str] = None
    mlflow_experiment_name: Optional[str] = None
    mlflow_run_name: Optional[str] = None


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: Optional[str] = None
    strategy: Optional[str] = None
    metric: Optional[str] = None
    subtask: Optional[str] = None


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_k: Optional[int|str] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    max_new_tokens: Optional[int|str] = None
    max_model_len: Optional[int|str] = None
    top_logprobs: Optional[int] = None
    reasoning_effort: Optional[str] = None


class RlEnvConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class ProcessorConfig(BaseModel):
    model_config = ConfigDict(extra="allow")


class NovaEvaluationRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: Optional[str] = None
    versions: Optional[list] = None
    instance_types: Optional[list] = None

    run: RunConfig
    evaluation: EvaluationConfig
    inference: Optional[InferenceConfig] = None
    rl_env: Optional[RlEnvConfig] = None
    processor: Optional[ProcessorConfig] = None
