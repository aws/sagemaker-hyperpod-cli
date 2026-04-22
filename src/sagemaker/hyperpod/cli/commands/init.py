import click
import yaml
import sys
import shutil
from pathlib import Path
from datetime import datetime
from jinja2 import Template
from sagemaker.hyperpod.cli.constants.init_constants import (
    USAGE_GUIDE_TEXT_CFN,
    USAGE_GUIDE_TEXT_CRD,
    CFN
)
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack
from sagemaker.hyperpod.cli.commands.cluster_stack import get_newest_template_version
from sagemaker.hyperpod.cli.init_utils import (
    generate_click_command,
    save_config_yaml,
    TEMPLATES,
    load_config,
    load_config_and_validate,
    validate_config_against_model,
    filter_validation_errors_for_user_input,
    display_validation_results,
    build_config_from_schema,
    save_template,
    get_default_version_for_template,
    create_from_k8s_yaml,
    is_dynamic_template
)
from sagemaker.hyperpod.common.utils import get_aws_default_region
from sagemaker.hyperpod.common.telemetry.telemetry_logging import (
    _hyperpod_telemetry_emitter,
)
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.cli.commands.training_recipe import _init_training_job, _configure_dynamic_template, _create_dynamic_template
from sagemaker.hyperpod.cli.recipe_utils import _validate_dynamic_template, _generate_dynamic_config_yaml


@click.command("init")
@click.argument("template", type=click.Choice(list(TEMPLATES.keys())))
@click.argument("directory", type=click.Path(file_okay=False), default=".")
@click.option("--version", "-v", default=None, help="Schema version")
@click.option("--model-id", hidden=True, help="JumpStart model ID (e.g. meta-textgeneration-llama-3-2-1b)")
@click.option("--huggingface-model-id", hidden=True, help="HuggingFace model ID (e.g. meta-llama/Llama-2-7b)")
@click.option("--technique", hidden=True, help="Customization technique (for hyp-recipe-job only)")
@click.option("--instance-type", hidden=True, help="Instance type (optional - if not provided, interactive cluster selection will be used)")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "init_template_cli")
def init(
    template: str,
    directory: str,
    version: str,
    model_id: str,
    huggingface_model_id: str,
    technique: str,
    instance_type: str,
):
    """
    Initialize a TEMPLATE scaffold in DIRECTORY.

    This command creates a complete project scaffold for the specified template type.
    It performs the following steps:

    \b
    1. Checks if the directory already contains a config.yaml and handles existing configurations
    2. Creates the target directory if it doesn't exist
    3. Generates a config.yaml file with schema-based default values
    4. Creates a template file (.jinja) for the specified template type
    5. Adds a README.md with usage instructions

    The generated files provide a starting point for configuring and submitting
    jobs to SageMaker HyperPod clusters orchestrated by Amazon EKS.

    Available templates:

    \b
      hyp-pytorch-job         PyTorch distributed training job
      hyp-jumpstart-endpoint  JumpStart model inference endpoint
      hyp-custom-endpoint     Custom model inference endpoint
      cluster-stack           HyperPod EKS cluster CloudFormation stack
      hyp-recipe-job          Fine-tuning/evaluation job from JumpStart Hub recipe

    For hyp-recipe-job, the following options are available:

    \b
      --model-id              JumpStart model ID (required, or use --huggingface-model-id)
      --huggingface-model-id  HuggingFace model ID (required, or use --model-id)
      --technique      Fine-tuning: SFT, DPO, RLAIF, RLVR, CPT, PPO
                       Evaluation: deterministic, LLMAJ (required)
      --instance-type  Instance type to use. If not provided, an interactive
                       cluster selection will be launched (optional)
    """
    # Original template initialization logic
    dir_path = Path(directory).resolve()
    config_file = dir_path / "config.yaml"
    skip_readme = False

    # Validate required params for hyp-recipe-job before any output
    if template in ["hyp-recipe-job"]:
        if not model_id and not huggingface_model_id:
            click.secho(f"❌ --model-id or --huggingface-model-id is required for {template}", fg="red")
            return
        if model_id and huggingface_model_id:
            click.secho("❌ Specify either --model-id or --huggingface-model-id, not both", fg="red")
            return
        if not technique:
            click.secho(f"❌ --technique is required for {template} (e.g. SFT, DPO, deterministic, LLMAJ)", fg="red")
            return

    # 1) Inspect existing config.yaml
    try:
        if config_file.is_file():
            try:
                # Use load_config to properly read commented template
                _, existing_template, _ = load_config(dir_path)
            except Exception as e:
                click.secho(f"⚠️  Could not parse existing config.yaml: {e}", fg="yellow")
                existing_template = None

            if existing_template == template:
                click.echo(f"⚠️  config.yaml already initialized as '{template}'.")
                if not click.confirm("Override?", default=False):
                    click.echo("Aborting init.")
                    return
                click.echo("Overriding config.yaml...")
                skip_readme = True
            else:
                click.echo(f"⚠️  Directory already initialized as '{existing_template}'.")
                click.secho(f"⚠️  It is highly unrecommended to initiate this directory with a different template.", fg="red")
                click.echo(f"⚠️  Recommended path is create a new folder and then init with '{template}'.")
                if not click.confirm(f"Do you want to re-initialize this directory with {template}?", default=False):
                    click.echo("Aborting init.")
                    return
                click.echo(f"Re-initializing {existing_template} → {template}…")

        else:
            click.echo(f"Initializing new scaffold for '{template}'…")
    except Exception as e:
        click.secho(f"💥  Initialization aborted due to error: {e}", fg="red")
        sys.exit(1)

    # 2) Ensure directory exists
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        click.secho(f"❌  Could not create directory {dir_path}: {e}", fg="red")
        sys.exit(1)

    # Handle dynamic job templates
    if template in ["hyp-recipe-job"]:
        resolved_model_id = huggingface_model_id if huggingface_model_id else model_id
        if _init_training_job(directory, template, resolved_model_id, technique, instance_type, is_huggingface=bool(huggingface_model_id)):
            click.secho(f"✔️ {template.replace('-', ' ').title()} initialized successfully", fg="green")
            click.secho("📄 Created: config.yaml, k8s.jinja", fg="green")
        return

    # 3) Build config dict + comment map, then write config.yaml
    try:
        # Determine version: use user-provided version or default to latest
        if version is None:
            version = get_default_version_for_template(template)

        # Use the common function to build config from schema
        full_cfg, comment_map = build_config_from_schema(template, version)

        save_config_yaml(
            prefill=full_cfg,
            comment_map=comment_map,
            directory=str(dir_path),
        )

        # 4) Generate template
        save_template(template, dir_path, version)

    except Exception as e:
        click.secho(f"💥  Could not write config.yaml or template: {e}", fg="red")
        sys.exit(1)

    # 5) Write README.md
    if not skip_readme:
        try:
            readme_path = dir_path / "README.md"
            with open(readme_path, "w") as f:
                if TEMPLATES[template]["schema_type"] == CFN:
                    f.write(USAGE_GUIDE_TEXT_CFN)
                else:
                    f.write(USAGE_GUIDE_TEXT_CRD)
        except Exception as e:
            click.secho("⚠️  README.md generation failed: %s", e, fg="yellow")

    # Convert to relative path for cleaner display
    relative_path = Path(directory) if directory != "." else Path("./")
    
    click.secho(
        f"✔️ {template} for schema version={version!r} is initialized in {relative_path}",
        fg="green",
    )
    click.echo(
        click.style(
            "🚀 Welcome!\n"
            f"📘 See {relative_path}/README.md for usage.\n",
            fg="green",
        )
    )


@click.command("reset")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "init_reset_cli")
def reset():
    """
    Reset the current directory's config.yaml to an "empty" scaffold:
    all schema keys set to default values (but keeping the template and version).
    """
    dir_path = Path(".").resolve()
    
    # 1) Load and validate config
    data, template, version = load_config(dir_path)
    
    # 2) Check if this is a dynamic template
    if is_dynamic_template(template, dir_path):
        # For dynamic templates, reset using the helper function
        try:
            _generate_dynamic_config_yaml(dir_path, template, version)
            click.secho("✔️ config.yaml reset: all fields set to default values.", fg="green")
        except Exception as e:
            click.secho(f"💥 Could not reset config.yaml: {e}", fg="red")
            sys.exit(1)
        return
    
    # 3) Standard template reset logic
    full_cfg, comment_map = build_config_from_schema(template, version)
    try:
        save_config_yaml(
            prefill=full_cfg,
            comment_map=comment_map,
            directory=str(dir_path),
        )
        click.secho("✔️  config.yaml reset: all fields set to default values.", fg="green")
    except Exception as e:
        click.secho(f"💥  Could not reset config.yaml: {e}", fg="red")
        sys.exit(1)

    # 4) Regenerate the k8s Jinja template
    if save_template(template, dir_path):
        click.secho(f"✔️  {template} is regenerated.", fg="green")


@click.command("configure")
@generate_click_command()
@click.pass_context
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "init_configure_cli")
def configure(ctx, option, value, model_config):
    """
    Update any subset of fields in ./config.yaml by passing --<field> flags.
    
    This command allows you to modify specific configuration fields without having
    to regenerate the entire config or fix unrelated validation issues. Only the
    fields you explicitly provide will be validated, making it easy to update
    configurations incrementally.
    
    Examples:
    
        # Update a single field
        hyp configure --hyperpod-cluster-name my-new-cluster
        
        # Update multiple fields at once
        hyp configure --stack-name my-stack  --create-fsx-stack: False

        # Update complex fields with JSON object
        hyp configure --availability-zone-ids '["id1", "id2"]'
    """
    # 1) Load existing config without validation
    dir_path = Path(".").resolve()
    data, template, version = load_config(dir_path)
    
    # 2) Check if this is a dynamic template (recipe)
    if is_dynamic_template(template, dir_path):
        # Handle recipe configure logic
        _configure_dynamic_template(ctx, option, value, dir_path)
        return
    
    # 3) Handle standard template configure logic
    _configure_standard_template(ctx, model_config, dir_path, data, template, version)


def _configure_standard_template(ctx, model_config, dir_path, data, template, version):
    """Handle configure for standard templates"""
    # Determine which fields the user actually provided
    # Use Click's parameter source tracking to identify command-line provided parameters
    user_input_fields = set()
    
    if ctx and hasattr(ctx, 'params') and model_config:
        # Check which parameters were provided via command line (not defaults)
        for param_name, param_value in ctx.params.items():
            # Skip if the parameter source indicates it came from default
            param_source = ctx.get_parameter_source(param_name)
            if param_source and param_source.name == 'COMMANDLINE':
                user_input_fields.add(param_name)
    
    if not user_input_fields:
        click.echo(ctx.get_help())
        ctx.exit(0)

    # Build merged config with user input
    full_cfg, comment_map = build_config_from_schema(
        template=template,
        version=version,
        model_config=model_config,
        existing_config=data,
        user_provided_fields=user_input_fields
    )

    # Validate the merged config, but only check user-provided fields
    all_validation_errors = validate_config_against_model(full_cfg, template, version)
    user_input_errors = filter_validation_errors_for_user_input(all_validation_errors, user_input_fields)
    
    is_valid = display_validation_results(
        user_input_errors,
        success_message="User input is valid!" if user_input_errors else "config.yaml updated successfully.",
        error_prefix="Invalid input arguments:"
    )
    
    if not is_valid:
        click.secho("❌  config.yaml was not updated due to invalid input.", fg="red")
        sys.exit(1)

    # Write out the updated config.yaml (only if user input is valid)
    try:
        save_config_yaml(
            prefill=full_cfg,
            comment_map=comment_map,
            directory=str(dir_path),
        )
    except Exception as e:
        click.secho(f"💥 Could not update config.yaml: {e}", fg="red")
        sys.exit(1)


@click.command("validate")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "init_validate_cli")
def validate():
    """
    Validate this directory's config.yaml against the appropriate schema.
    """
    dir_path = Path(".").resolve()
    
    try:
        # Load config to determine template type
        data, template, version = load_config(dir_path)
        
        # Check if this is a dynamic template
        if is_dynamic_template(template, dir_path):
            # Validate dynamic template
            _validate_dynamic_template(dir_path)
            click.secho("✔️ Configuration validated successfully", fg="green")
        else:
            # Use standard validation
            load_config_and_validate(dir_path)
            click.secho("✔️ Configuration validated successfully", fg="green")
    except (FileNotFoundError, ValueError) as e:
        click.secho(f"❌ {e}", fg="red")
        sys.exit(1)
    except Exception as e:
        click.secho(f"❌ Validation failed: {e}", fg="red")
        sys.exit(1)


@click.command(name="_default_create")
@click.option("--region", "-r", default=None, help="Region to create cluster stack for, default to your region in aws configure. Not available for other templates.")
@click.option("--template-version", type=click.INT, help="Version number of cluster creation template. Not available for other templates.")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@_hyperpod_telemetry_emitter(Feature.HYPERPOD_CLI, "init_create_cli")
def _default_create(region, template_version, debug):
    """
    Validate configuration and render template files for deployment.
    
    This command performs the following operations:
    
    1. Loads and validates the config.yaml file in the current directory
    2. Determines the template type (CFN for CloudFormation or CRD for Kubernetes)
    3. Locates the appropriate Jinja template file:
       - cfn_params.jinja for CloudFormation templates
       - k8s.jinja for Kubernetes CRD templates
    4. Validates the configuration using the appropriate schema:
       - HpClusterStack validation for CFN templates
       - Registry-based validation for CRD templates
    5. Renders the Jinja template with configuration values
    6. Creates a timestamped directory under run/ (e.g., run/20240116T143022/)
    7. Copies the validated config.yaml to the run directory
    8. Writes the rendered output:
       - cfn_params.yaml for CloudFormation templates
       - k8s.yaml for Kubernetes templates
    
    The generated files in the run directory can be used for actual deployment
    to SageMaker HyperPod clusters or CloudFormation stacks.
    
    Prerequisites:
    - Must be run in a directory initialized with 'hyp init'
    - config.yaml and the appropriate template file must exist
    """
    dir_path = Path('.').resolve()
    config_file = dir_path / 'config.yaml'
    
    # 1) Load config to determine template type
    data, template, version = load_config_and_validate(dir_path)
    
    # Check if this is a dynamic template (recipe)
    if is_dynamic_template(template, dir_path):
        _create_dynamic_template(dir_path, data)
        return
    
    # Handle standard templates (existing logic)
    _create_standard_template(dir_path, data, template, version, region, template_version, debug)


def _create_standard_template(dir_path: Path, data: dict, template: str, version: str, region: str, template_version: int, debug: bool = False):
    """Handle create for standard templates"""
    # Check if region flag is used for non-cluster-stack templates
    if region and template != "cluster-stack":
        click.secho(f"❌  --region flag is only available for cluster-stack template, not for {template}.", fg="red")
        sys.exit(1)
    
    # 2) Determine correct jinja file based on template type
    info = TEMPLATES[template]
    schema_type = info["schema_type"]
    if schema_type == CFN:
        jinja_file = dir_path / 'cfn_params.jinja'
    else:
        jinja_file = dir_path / 'k8s.jinja'

    # 3) Ensure files exist
    config_file = dir_path / 'config.yaml'
    if not config_file.is_file() or not jinja_file.is_file():
        click.secho(f"❌  Missing config.yaml or {jinja_file.name}. Run `hyp init` first.", fg="red")
        sys.exit(1)

    try:
        template_source = jinja_file.read_text()
        tpl = Template(template_source)
        rendered = tpl.render(**data)
    except Exception as e:
        click.secho(f"❌  Failed to render template: {e}", fg="red")
        sys.exit(1)

    # 6) Prepare run/<timestamp> directory and write files
    run_root = dir_path / 'run'
    run_root.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    out_dir = run_root / timestamp
    out_dir.mkdir()

    try:
        shutil.copy(config_file, out_dir / 'config.yaml')
        output_file = 'cfn_params.yaml' if schema_type == CFN else 'k8s.yaml'
        with open(out_dir / output_file, 'w', encoding='utf-8') as f:
            f.write(rendered)
        # Use relative path for cleaner display
        relative_out_dir = Path("run") / timestamp
        click.secho(f"✔️  Submitted! Files written to {relative_out_dir}", fg="green")
    except Exception as e:
        click.secho(f"❌  Failed to write run files: {e}", fg="red")
        sys.exit(1)

    # 7) Make the downstream call
    try :
        if region is None:
            region = get_aws_default_region()
            # Only show region message for cluster-stack template
            if template == "cluster-stack":
                click.secho(f"Submitting to default region: {region}.", fg="yellow")

        # Unified pattern for all templates
        dir_path = Path(".").resolve()
        data, template, version = load_config(dir_path)
        registry = TEMPLATES[template]["registry"]
        model = registry.get(str(version))
        if model:
            # Filter out CLI metadata fields before passing to model
            from sagemaker.hyperpod.cli.init_utils import _filter_cli_metadata_fields
            filtered_config = _filter_cli_metadata_fields(data)
            template_model = model(**filtered_config)
            
            # Pass region to to_domain for cluster stack template
            if template == "cluster-stack":
                config = template_model.to_config(region=region)
                # Use newest template version if not provided
                if template_version is None:
                    template_version = get_newest_template_version()
                    click.secho(f"No template version specified, using newest version: {template_version}", fg="yellow")
                HpClusterStack(**config).create(region, template_version)
            else:
                # Create from k8s.yaml
                k8s_file = out_dir / 'k8s.yaml'
                create_from_k8s_yaml(str(k8s_file), debug=debug)

    except Exception as e:
        click.secho(f"❌  Failed to submit the command: {e}", fg="red")
        sys.exit(1)