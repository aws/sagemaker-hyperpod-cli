"""
Param ordering and grouped config.yaml rendering for recipe jobs.

The priority list is a hardcoded ordered sequence of param names grouped by
concern. When rendering a config.yaml from a recipe's parameter_schema, params
are emitted in this order with section headers as comments. Any param not in
the list falls into a final "Other" group at the end.

This is intentionally a simple, explicit list — no dynamic inference. When new
params appear in recipes they can be slotted into the right group here.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Priority list — ordered by group, required before optional within each group
# ---------------------------------------------------------------------------

# Each entry is (param_name, group_label).
# Group label is used to emit section header comments in the YAML output.
_PARAM_ORDER: list[tuple[str, str]] = [
    # Job Identity
    ("name",                    "Job Identity"),
    ("namespace",               "Job Identity"),

    # Data — llmft/verl family
    ("data_path",               "Data"),
    ("training_data_name",      "Data"),
    ("validation_data_path",    "Data"),
    ("validation_data_name",    "Data"),
    ("train_val_split_ratio",   "Data"),

    # Data — nova family
    ("data_s3_path",            "Data"),
    ("validation_s3_path",      "Data"),

    # Output
    ("output_path",             "Output"),
    ("results_directory",       "Output"),
    ("resume_from_path",        "Output"),
    ("output_s3_path",          "Output"),

    # Core Hyperparameters
    ("global_batch_size",       "Core Hyperparameters"),
    ("learning_rate",           "Core Hyperparameters"),
    ("max_epochs",              "Core Hyperparameters"),
    ("max_steps",               "Core Hyperparameters"),

    # Advanced Hyperparameters (includes technique-specific params)
    ("lr_warmup_ratio",         "Advanced Hyperparameters"),
    ("max_context_length",      "Advanced Hyperparameters"),
    ("max_prompt_length",       "Advanced Hyperparameters"),
    ("max_length",              "Advanced Hyperparameters"),
    ("lora_alpha",              "Advanced Hyperparameters"),
    ("learning_rate_ratio",     "Advanced Hyperparameters"),
    ("adam_beta",               "Advanced Hyperparameters"),
    ("rollout",                 "Advanced Hyperparameters"),
    ("number_generation",       "Advanced Hyperparameters"),
    ("preset_reward_function",  "Advanced Hyperparameters"),
    ("judge_model_id",          "Advanced Hyperparameters"),
    ("judge_prompt_template",   "Advanced Hyperparameters"),
    ("reward_lambda_arn",       "Advanced Hyperparameters"),
    ("reasoning_enabled",       "Advanced Hyperparameters"),

    # MLflow
    ("mlflow_tracking_uri",     "MLflow"),
    ("mlflow_run_id",           "MLflow"),
    ("mlflow_experiment_name",  "MLflow"),
    ("mlflow_run_name",         "MLflow"),

    # Compute
    ("instance_type",           "Compute"),
    ("replicas",                "Compute"),

    # Model (auto-resolved from recipe, rarely overridden)
    ("model_name_or_path",      "Model"),
]

# Build lookup: param_name -> (index, group)
_ORDER_INDEX: dict[str, tuple[int, str]] = {
    name: (i, group) for i, (name, group) in enumerate(_PARAM_ORDER)
}

_FALLBACK_GROUP = "Other"


def sort_key(param_name: str) -> tuple[int, str]:
    """Return (priority_index, param_name) for stable ordering."""
    idx, _ = _ORDER_INDEX.get(param_name, (len(_PARAM_ORDER), param_name))
    return (idx, param_name)


def render_config_yaml(parameter_schema: dict[str, Any], header_comments: list[str] | None = None) -> str:
    """Render a config.yaml string from a recipe's parameter_schema.

    Params are emitted in priority order with section header comments.
    Params not in the priority list are appended at the end under "Other".

    Args:
        parameter_schema: The recipe's parameter_schema dict (from cache.json).
        header_comments: Optional list of lines to emit at the top (e.g. model, technique).

    Returns:
        A YAML string ready to write to config.yaml.
    """
    lines: list[str] = []

    if header_comments:
        for c in header_comments:
            lines.append(f"# {c}")
        lines.append("")

    # Sort params by priority
    sorted_params = sorted(parameter_schema.items(), key=lambda kv: sort_key(kv[0]))

    current_group: str | None = None
    for param_name, spec in sorted_params:
        _, group = _ORDER_INDEX.get(param_name, (len(_PARAM_ORDER), _FALLBACK_GROUP))

        # Emit section header when group changes
        if group != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"# {'─' * 10} {group} {'─' * (40 - len(group))}")
            current_group = group

        # Build inline comment from spec metadata
        meta_parts: list[str] = [f"Type: {spec.get('type', 'any')}"]
        if spec.get("required"):
            meta_parts.append("Required")
        else:
            meta_parts.append("Optional")
        if "minimum" in spec:
            meta_parts.append(f"Min: {spec['minimum']}")
        if "maximum" in spec:
            meta_parts.append(f"Max: {spec['maximum']}")
        if "enum" in spec:
            meta_parts.append(f"Options: {spec['enum']}")
        lines.append(f"# {', '.join(meta_parts)}")

        # Emit the param with its default value
        default = spec.get("default", "")
        if default is None:
            default = ""
        lines.append(f"{param_name}: {default}")

    return "\n".join(lines) + "\n"
