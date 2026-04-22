"""Reusable utilities for recipe job operations."""

import json
import re
import yaml
import click
import boto3
import sys
from jinja2 import Template
from kubernetes import client, config
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from sagemaker.hyperpod.cli.init_utils import load_dynamic_schema
from sagemaker.hyperpod.cli.type_handler_utils import is_undefined_value

_KIND_PLURALS = {
    "ingress": "ingresses",
    "networkpolicy": "networkpolicies",
    "storageclass": "storageclasses",
    "clusterrole": "clusterroles",
    "clusterrolebinding": "clusterrolebindings",
}

def _kind_to_plural(kind: str) -> str:
    k = kind.lower()
    return _KIND_PLURALS.get(k, k + 's')


import re


_HUB_CONTENT_ARN_PATTERN = re.compile(
    r"^arn:aws(-[\w]+)*:sagemaker:[a-z0-9\-]+:(\d{12}|aws):hub-content/[^/]+/[^/]+/[^/]+(/[\d.]+)?$"
)

# Static fallback for HF model IDs where name derivation fails the search.
# Only contains edge cases — not all models.
_HF_MODEL_ID_FALLBACK = {
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B": "deepseek-llm-r1-distill-qwen-32b",
    "Qwen/Qwen3-0.6B":                          "huggingface-reasoning-qwen3-06b",
}

# Technique aliases for user-friendly input
_TECHNIQUE_ALIASES = {
    "deterministic": "DeterministicEvaluation",
    "llmaj": "LLMAJEvaluation",
}


def _is_hub_content_arn(model_id: str) -> bool:
    """Check if model_id is a valid SageMaker Hub Content ARN."""
    return bool(_HUB_CONTENT_ARN_PATTERN.match(model_id))


def _parse_hub_content_arn(arn: str) -> dict:
    """Parse a Hub Content ARN into describe_hub_content parameters.

    ARN format: arn:aws:sagemaker:<region>:<account>:hub-content/<hub>/<type>/<name>[/<version>]
    """
    path = arn.split(":hub-content/", 1)[1]
    parts = path.split("/")
    params = {
        "HubName": parts[0],
        "HubContentType": parts[1],
        "HubContentName": parts[2],
    }
    if len(parts) >= 4:
        params["HubContentVersion"] = parts[3]
    return params


def _fetch_recipe_from_private_hub(sagemaker_client, hub_content_arn: str) -> Dict[str, Any]:
    """Fetch hub content document using a Hub Content ARN."""
    if not _is_hub_content_arn(hub_content_arn):
        raise ValueError(
            f"Invalid Hub Content ARN format: '{hub_content_arn}'. "
            f"Expected format: arn:aws:sagemaker:<region>:<account>:hub-content/<hub>/<type>/<name>"
        )
    params = _parse_hub_content_arn(hub_content_arn)
    response = sagemaker_client.describe_hub_content(**params)
    return json.loads(response.get('HubContentDocument', '{}'))


def _resolve_huggingface_model_id(sagemaker_client, hf_model_id: str) -> str:
    """Resolve a HuggingFace model ID to a JumpStart Hub content name.

    Strategy: dynamic search first (@recipe: keyword filter), then static
    fallback for models whose names don't derive cleanly to a search term.
    Raises ValueError with a clean "not supported" message for unknown models.
    """
    raw = hf_model_id.split('/')[-1].lower()
    search_term = re.sub(r'[^a-z0-9\-]', '-', raw).strip('-')

    response = sagemaker_client.list_hub_contents(
        HubName='SageMakerPublicHub',
        HubContentType='Model',
        NameContains=search_term,
        MaxResults=20,
    )
    recipe_matches = [
        m for m in response.get('HubContentSummaries', [])
        if any(k.startswith('@recipe:') for k in m.get('HubContentSearchKeywords', []))
    ]

    if len(recipe_matches) == 1:
        return recipe_matches[0]['HubContentName']

    if hf_model_id in _HF_MODEL_ID_FALLBACK:
        return _HF_MODEL_ID_FALLBACK[hf_model_id]

    raise ValueError(
        f"'{hf_model_id}' may not be supported for HyperPod recipes, or could not be resolved.\n"
        f"If you are using a HuggingFace model ID, try the JumpStart Hub model ID instead and retry.\n"
        f"To find supported model IDs: https://docs.aws.amazon.com/cli/latest/reference/sagemaker/list-hub-contents.html"
    )


def _fetch_recipe_from_hub(sagemaker_client, model_id: str, job_type: str, technique: str = None, instance_type: str = None, is_huggingface: bool = False) -> Dict[str, Any]:
    """Fetch and validate recipe from SageMaker Hub.

    Supports three model_id formats:
    - JumpStart model ID via --model-id (e.g. meta-textgeneration-llama-3-2-1b)
    - HuggingFace model ID via --huggingface-model-id (e.g. meta-llama/Llama-3.1-8B-Instruct)
    - Hub Content ARN via --model-id (e.g. arn:aws:sagemaker:...)
    """
    if _is_hub_content_arn(model_id):
        hub_content_doc = _fetch_recipe_from_private_hub(sagemaker_client, model_id)
    else:
        if is_huggingface:
            resolved_id = _resolve_huggingface_model_id(sagemaker_client, model_id)
        else:
            resolved_id = model_id
        response = sagemaker_client.describe_hub_content(
            HubName="SageMakerPublicHub",
            HubContentType="Model",
            HubContentName=resolved_id,
        )
        hub_content_doc = json.loads(response.get('HubContentDocument', '{}'))
    recipe_collection = hub_content_doc.get('RecipeCollection', [])

    if not technique:
        raise ValueError("technique is required. Supported values: SFT, DPO, RLAIF, RLVR, CPT, PPO, deterministic, LLMAJ")

    # Resolve technique aliases to canonical names (case-insensitive)
    technique_lower = technique.lower()
    technique = _TECHNIQUE_ALIASES.get(technique_lower, technique.upper() if technique_lower not in _TECHNIQUE_ALIASES else technique)

    # Filter recipes by technique
    matching_recipes = [
        r for r in recipe_collection
        if (r.get('CustomizationTechnique') or '').upper() == technique.upper()
        or r.get('EvaluationType') == technique
    ]
    
    if not matching_recipes:
        available = set()
        for r in recipe_collection:
            available.add(r.get('CustomizationTechnique') or r.get('EvaluationType') or '(none)')
        raise ValueError(f"No recipe found for technique: {technique}. Available: {sorted(available)}")
    
    # If instance type is provided, find recipe that supports it
    if instance_type:
        for recipe in matching_recipes:
            if instance_type in recipe.get('SupportedInstanceTypes', []):
                return recipe
        
        # If no recipe supports the instance type, collect all supported types
        all_supported = set()
        for recipe in matching_recipes:
            all_supported.update(recipe.get('SupportedInstanceTypes', []))
        
        raise ValueError(f"Instance type {instance_type} not supported. Supported: {sorted(all_supported)}")
    
    # Return first matching recipe if no instance type specified
    return matching_recipes[0]


def _download_s3_content(s3_client, s3_uri: str) -> str:
    """Download content from S3 URI."""
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return obj['Body'].read().decode('utf-8')


def _download_s3_json(s3_client, s3_uri: str) -> Dict[str, Any]:
    """Download JSON content from S3 URI."""
    bucket = s3_uri.split('/')[2]
    key = '/'.join(s3_uri.split('/')[3:])
    obj = s3_client.get_object(Bucket=bucket, Key=key)
    return json.loads(obj['Body'].read())


def _validate_and_convert_value(value: str, param_spec: Dict[str, Any]) -> Any:
    """Validate and convert a parameter value according to its specification."""
    param_type = param_spec.get('type', 'string')
    min_val = param_spec.get('minimum') or param_spec.get('min')
    max_val = param_spec.get('maximum') or param_spec.get('max')
    enum_vals = param_spec.get('enum')
    
    # Type conversion with better error messages
    try:
        if param_type == "integer":
            converted_value = int(value)
        elif param_type == "float":
            converted_value = float(value)
        elif param_type == "string":
            converted_value = str(value)
        else:
            converted_value = value
    except ValueError:
        raise ValueError(f"Invalid {param_type} value: '{value}'. Please enter a valid {param_type}.")
    
    # Constraint validation with specific messages
    if min_val is not None and converted_value < min_val:
        raise ValueError(f"Value {converted_value} is below the minimum allowed value of {min_val}.")
    
    if max_val is not None and converted_value > max_val:
        raise ValueError(f"Value {converted_value} exceeds the maximum allowed value of {max_val}.")
    
    if enum_vals and converted_value not in enum_vals:
        raise ValueError(f"Invalid option '{converted_value}'. Please choose from: {', '.join(map(str, enum_vals))}.")
    
    return converted_value


def _collect_parameter_interactively(key: str, param_spec: Dict[str, Any]) -> Tuple[str, Any]:
    """Collect a single parameter value interactively from user."""
    param_type = param_spec.get('type', 'string')
    description = param_spec.get('description', '')
    required = param_spec.get('required', False)
    default = param_spec.get('default')
    min_val = param_spec.get('min')
    max_val = param_spec.get('max')
    enum_vals = param_spec.get('enum')
    
    # Display parameter info
    click.secho(f"--{key.replace('_', '-')}", fg="cyan", bold=True)
    if description:
        click.secho(f"  Description: {description}", fg="white")
    
    type_info = f"  Type: {param_type}"
    if min_val is not None:
        type_info += f", Min: {min_val}"
    if max_val is not None:
        type_info += f", Max: {max_val}"
    if enum_vals:
        type_info += f", Options: {enum_vals}"
    type_info += f", Required: {required}"
    click.secho(type_info, fg="white")
    
    if default is not None:
        click.secho(f"  Default: {default}", fg="white")
    
    # Get user input with validation loop
    while True:
        if required and default is None:
            user_input = input(f"Enter value for {key}: ")
        else:
            prompt_text = f"Enter value for {key}"
            if default is not None:
                user_input = input(f"{prompt_text} [{default}]: ") or str(default)
            else:
                user_input = input(f"{prompt_text}: ")
        
        # Skip if empty and not required
        if not user_input and not required:
            return key, None
        
        # Check for empty input on required fields
        if not user_input and required:
            click.secho(f"❌ This field is required. Please provide a value.", fg="red")
            continue
        
        # Validate input
        try:
            converted_value = _validate_and_convert_value(user_input, param_spec)
            return key, converted_value
        except ValueError as e:
            click.secho(f"❌ {e}", fg="red")
            continue


def _submit_k8s_resources(custom_api, rendered_yaml: str) -> None:
    """Submit Kubernetes resources from rendered YAML."""
    k8s_documents = list(yaml.safe_load_all(rendered_yaml))
    
    for k8s_config in k8s_documents:
        if not k8s_config:
            continue
            
        api_version = k8s_config.get('apiVersion', '')
        kind = k8s_config.get('kind', '')
        metadata = k8s_config.get('metadata', {})
        namespace = metadata.get('namespace', 'default')
        
        # Handle standard vs custom resources
        if api_version == 'v1' or api_version.startswith('apps/') or api_version.startswith('extensions/'):
            core_api = client.CoreV1Api()
            if kind == 'ConfigMap':
                core_api.create_namespaced_config_map(namespace=namespace, body=k8s_config)
            elif kind == 'Secret':
                core_api.create_namespaced_secret(namespace=namespace, body=k8s_config)
            elif kind == 'Service':
                core_api.create_namespaced_service(namespace=namespace, body=k8s_config)
            else:
                custom_api.create_namespaced_custom_object(
                    group='', version=api_version, namespace=namespace,
                    plural=_kind_to_plural(kind), body=k8s_config)
        else:
            if '/' in api_version:
                group, version = api_version.split('/', 1)
            else:
                group, version = '', api_version

            custom_api.create_namespaced_custom_object(
                group=group, version=version, namespace=namespace,
                plural=_kind_to_plural(kind), body=k8s_config)


def _render_k8s_template(template_content: str, config_data: Dict[str, Any]) -> str:
    """Render Kubernetes template with configuration data."""
    template = Template(template_content)
    return template.render(**config_data)


def _collect_all_parameters_interactively(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Collect all parameters interactively from user."""
    config_data = {}
    sorted_spec = sorted(spec.items(), key=lambda x: (not x[1].get('required', False), x[0]))
    
    for key, param_spec in sorted_spec:
        param_key, param_value = _collect_parameter_interactively(key, param_spec)
        if param_value is not None:
            config_data[param_key] = param_value
        click.echo()  # Add spacing
    
    return config_data


# Client management utilities
_sagemaker_client = None
_s3_client = None
_k8s_custom_client = None


def _get_sagemaker_client():
    """Get cached SageMaker client."""
    global _sagemaker_client
    if _sagemaker_client is None:
        _sagemaker_client = boto3.client("sagemaker")
    return _sagemaker_client


def _get_s3_client():
    """Get cached S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3")
    return _s3_client


def _get_k8s_custom_client():
    """Get Kubernetes custom objects API client for PyTorchJob resources."""
    global _k8s_custom_client
    if _k8s_custom_client is None:
        try:
            config.load_kube_config()
        except config.ConfigException:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                raise Exception("Could not configure kubernetes python client")
        _k8s_custom_client = client.CustomObjectsApi()
    return _k8s_custom_client


def _validate_dynamic_template(dir_path: Path) -> bool:
    """Validate dynamic template config against .override_spec.json"""
    spec_path = dir_path / ".override_spec.json"
    if not spec_path.exists():
        raise FileNotFoundError(".override_spec.json not found")
    
    spec = load_dynamic_schema(dir_path)
    config_data = yaml.safe_load((dir_path / "config.yaml").read_text()) or {}
    
    validation_errors = []
    for key, field_spec in spec.items():
        value = config_data.get(key)
        required = field_spec.get("required", False)
        field_type = field_spec.get("type", "string")
        
        if required and (value is None or value == ""):
            validation_errors.append(f"{key}: Required field is missing or empty")
            continue
        
        if value is None:
            continue
        
        # Type validation
        if field_type == "integer" and not isinstance(value, int):
            validation_errors.append(f"{key}: Expected integer, got {type(value).__name__}")
        elif field_type == "float" and not isinstance(value, (int, float)):
            validation_errors.append(f"{key}: Expected number, got {type(value).__name__}")
        elif field_type == "string" and not isinstance(value, str):
            validation_errors.append(f"{key}: Expected string, got {type(value).__name__}")
        
        # Constraint validation with improved messages
        if isinstance(value, (int, float)):
            if "minimum" in field_spec and value < field_spec["minimum"]:
                validation_errors.append(f"{key}: Value {value} is below the minimum allowed value of {field_spec['minimum']}")
            if "maximum" in field_spec and value > field_spec["maximum"]:
                validation_errors.append(f"{key}: Value {value} exceeds the maximum allowed value of {field_spec['maximum']}")
        
        if "enum" in field_spec and value not in field_spec["enum"]:
            validation_errors.append(f"{key}: Invalid option '{value}'. Please choose from: {', '.join(map(str, field_spec['enum']))}")
    
    if validation_errors:
        raise ValueError("Config validation failed:\n" + "\n".join(f"  • {error}" for error in validation_errors))
    
    return True


def _generate_dynamic_config_yaml(dir_path: Path, template: str, version: str = None, model_name: str = None, technique: str = None, instance_type: str = None):
    """Generate config.yaml for dynamic templates with default values"""
    from sagemaker.hyperpod.cli.recipe_param_order import render_config_yaml

    spec = load_dynamic_schema(dir_path)

    # Override instance_type default with user-provided value (copy to avoid mutating loaded schema)
    if instance_type and 'instance_type' in spec:
        spec = dict(spec)
        spec['instance_type'] = dict(spec['instance_type'], default=instance_type)

    header = [f"template: {template}"]
    if model_name:
        header.append(f"model: {model_name}")
    if technique:
        header.append(f"fine tune technique: {technique}")

    config_path = dir_path / 'config.yaml'
    config_path.write_text(render_config_yaml(spec, header_comments=header))

    lockfile = dir_path / ".hyp"
    lockfile.write_text(template)


def _update_config_field(config_path: Path, spec: Dict[str, Any], option: str, value: Any):
    """Update a single field in config.yaml for dynamic templates"""
    # Validate option exists
    if option not in spec:
        click.secho(f"❌ Unknown option: {option}", fg="red")
        sys.exit(1)
    
    if is_undefined_value(value):
        click.secho(f"❌ This field is required. Please provide a value for option: {option}", fg="red")
        sys.exit(1)
    
    # Validate and convert value
    try:
        converted_value = _validate_and_convert_value(str(value), spec[option])
    except ValueError as e:
        click.secho(f"❌ {e}", fg="red")
        sys.exit(1)
    
    # Load and update config.yaml - preserve existing values
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    updated = False
    new_lines = []
    key_pattern = re.compile(r'^(\s*)' + re.escape(option) + r'\s*:')
    for line in lines:
        if not line.strip().startswith('#') and key_pattern.match(line):
            indent = len(line) - len(line.lstrip())
            new_lines.append(f"{' ' * indent}{option}: {converted_value}\n")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        click.secho(f"❌ Option {option} not found in config.yaml", fg="red")
        sys.exit(1)
    
    # Write back to config.yaml
    with open(config_path, 'w') as f:
        f.writelines(new_lines)
