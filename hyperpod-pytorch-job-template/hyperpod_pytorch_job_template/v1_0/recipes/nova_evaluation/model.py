from typing import Optional
from pydantic import BaseModel, ConfigDict


class RunConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    model_type: Optional[str] = None
    model_name_or_path: Optional[str] = None
    replicas: Optional[int] = None
    data_s3_path: Optional[str] = None
    output_s3_path: Optional[str] = None


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: Optional[str] = None
    strategy: Optional[str] = None
    metric: Optional[str] = None
    subtask: Optional[str] = None


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_k: Optional[int] = None
    top_p: Optional[float] = None
    temperature: Optional[float] = None
    max_new_tokens: Optional[int] = None


class NovaEvaluationRecipeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run: RunConfig
    evaluation: EvaluationConfig
    inference: Optional[InferenceConfig] = None
