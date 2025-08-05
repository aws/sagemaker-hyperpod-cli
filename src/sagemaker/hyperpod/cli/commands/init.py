import click
import yaml
import sys
from pathlib import Path
from pydantic import ValidationError
from datetime import datetime
from jinja2 import Template
import shutil

from sagemaker.hyperpod.cli.constants.init_constants import (
    USAGE_GUIDE_TEXT,
    CFN
)
from sagemaker.hyperpod.cluster_management.hp_cluster_stack import HpClusterStack
import json
from sagemaker.hyperpod.cli.init_utils import (
    generate_click_command,
    save_config_yaml,
    TEMPLATES,
    load_config_and_validate,
    load_config,
    validate_config_against_model,
    filter_validation_errors_for_user_input,
    display_validation_results,
    extract_user_provided_args_from_cli,
    build_config_from_schema,
    save_template
)

@click.command("init")
@click.argument("template", type=click.Choice(list(TEMPLATES.keys())))
@click.argument("directory", type=click.Path(file_okay=False), default=".")
@click.option("--namespace", "-n", default="default", help="Namespace, default to default")
@click.option("--version", "-v", default="1.0", help="Schema version")
@generate_click_command(require_schema_fields=False)
def init(
    template: str,
    directory: str,
    namespace: str,
    version: str,
    model_config,  # Pydantic model from decorator
):
    """
    Initialize a TEMPLATE scaffold in DIRECTORY.
    
    This command creates a complete project scaffold for the specified template type.
    It performs the following steps:
    
    1. Checks if the directory already contains a config.yaml and handles existing configurations
    2. Creates the target directory if it doesn't exist
    3. Generates a config.yaml file with schema-based default values and user-provided inputs
    4. Creates a Kubernetes template file (k8s.jinja) for the specified template type
    5. Adds a README.md with usage instructions
    
    The generated files provide a starting point for configuring and submitting
    jobs to SageMaker HyperPod clusters orchestrated by Amazon EKS.
    """
    dir_path = Path(directory).resolve()
    config_file = dir_path / "config.yaml"
    skip_readme = False

    # 1) Inspect existing config.yaml
    try:
        if config_file.is_file():
            try:
                existing = yaml.safe_load(config_file.read_text()) or {}
                existing_template = existing.get("template")
            except Exception as e:
                click.echo("Could not parse existing config.yaml: %s", e)
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
                skip_readme = True

        else:
            click.echo(f"Initializing new scaffold for '{template}'…")
    except Exception as e:
        click.secho("💥  Initialization aborted due to error: %s", e, fg="red")
        sys.exit(1)

    # 2) Ensure directory exists
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        click.secho(f"❌  Could not create directory {dir_path}: {e}", fg="red")
        sys.exit(1)

    # 3) Build config dict + comment map, then write config.yaml
    try:
        # Use the common function to build config from schema
        full_cfg, comment_map = build_config_from_schema(template, namespace, version, model_config)

        save_config_yaml(
            prefill=full_cfg,
            comment_map=comment_map,
            directory=str(dir_path),
        )

    except Exception as e:
        click.secho(f"💥  Could not write config.yaml: {e}", fg="red")
        sys.exit(1)

    # 4) Generate  template
    if not save_template(template, dir_path):
        click.secho("⚠️ Template generation failed", fg="yellow")

    # 5) Write README.md
    if not skip_readme:
        try:
            readme_path = dir_path / "README.md"
            with open(readme_path, "w") as f:
                f.write(USAGE_GUIDE_TEXT)
        except Exception as e:
            click.secho("⚠️  README.md generation failed: %s", e, fg="yellow")

    click.secho(
        f"✔️  {template} for schema version={version!r} is initialized in {dir_path}",
        fg="green",
    )
    click.echo(
        click.style(
            "🚀 Welcome!\n"
            f"📘 See {dir_path}/README.md for usage.\n",
            fg="green",
        )
    )


@click.command("reset")
def reset():
    """
    Reset the current directory's config.yaml to an "empty" scaffold:
    all schema keys set to default values (but keeping the template and namespace).
    """
    dir_path = Path(".").resolve()
    
    # 1) Load and validate config
    data, template, version = load_config(dir_path)
    namespace = data.get("namespace", "default")
    
    # 2) Build config with default values from schema
    full_cfg, comment_map = build_config_from_schema(template, namespace, version)
    
    # 3) Overwrite config.yaml
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
        click.secho(f"✔️ {template} is regenerated.", fg="green")


@click.command("configure")
@generate_click_command(
    require_schema_fields=False,  # flags are all optional
    auto_load_config=True,        # load template/namespace/version from config.yaml
)
@click.pass_context
def configure(ctx, model_config):
    """
    Update any subset of fields in ./config.yaml by passing
    --<field> flags. E.g.

      hyp configure --model-name my-model --instance-type ml.m5.large
      hyp configure --namespace production
      hyp configure --namespace test --stage gamma
    """
    # Extract namespace from command line arguments manually
    import sys
    namespace = None
    args = sys.argv
    for i, arg in enumerate(args):
        if arg in ['--namespace', '-n'] and i + 1 < len(args):
            namespace = args[i + 1]
            break
    
    # 1) Load existing config without validation
    dir_path = Path(".").resolve()
    data, template, version = load_config(dir_path)
    
    # Use provided namespace or fall back to existing config namespace
    config_namespace = namespace if namespace is not None else data.get("namespace", "default")
    
    # 2) Extract ONLY the user's input arguments by checking what was actually provided
    provided_args = extract_user_provided_args_from_cli()
    
    # Filter model_config to only include user-provided fields
    all_model_data = model_config.model_dump(exclude_none=True) if model_config else {}
    user_input = {k: v for k, v in all_model_data.items() if k in provided_args}
    
    if not user_input and namespace is None:
        click.secho("⚠️  No arguments provided to configure.", fg="yellow")
        return

    # 3) Build merged config with user input
    full_cfg, comment_map = build_config_from_schema(
        template=template,
        namespace=config_namespace,
        version=version,
        model_config=model_config,
        existing_config=data
    )

    # 4) Validate the merged config and filter errors for user input fields only
    all_validation_errors = validate_config_against_model(full_cfg, template, version)
    
    # Include namespace in user input fields if it was provided
    user_input_fields = set(user_input.keys())
    if namespace is not None:
        user_input_fields.add("namespace")
    
    user_input_errors = filter_validation_errors_for_user_input(all_validation_errors, user_input_fields)
    
    is_valid = display_validation_results(
        user_input_errors,
        success_message="User input is valid!" if user_input_errors else "Merged configuration is valid!",
        error_prefix="Invalid input arguments:"
    )
    
    if not is_valid:
        click.secho("❌  config.yaml was not updated due to invalid input.", fg="red")
        sys.exit(1)

    # 5) Write out the updated config.yaml (only if user input is valid)
    try:
        save_config_yaml(
            prefill=full_cfg,
            comment_map=comment_map,
            directory=str(dir_path),
        )
        click.secho("✔️  config.yaml updated successfully.", fg="green")
    except Exception as e:
        click.secho(f"💥 Could not update config.yaml: {e}", fg="red")
        sys.exit(1)


@click.command("validate")
def validate():
    """
    Validate this directory's config.yaml against the appropriate schema.
    """
    dir_path = Path(".").resolve()
    load_config_and_validate(dir_path)


@click.command("submit")
@click.option("--region", "-r", default="us-west-2", help="Region, Default is us-west-2")
def submit(region):
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
    
    # 2) Determine correct jinja file based on template type
    info = TEMPLATES[template]
    schema_type = info["schema_type"]
    if schema_type == CFN:
        jinja_file = dir_path / 'cfn_params.jinja'
    else:
        jinja_file = dir_path / 'k8s.jinja'

    # 3) Ensure files exist
    if not config_file.is_file() or not jinja_file.is_file():
        click.secho(f"❌  Missing config.yaml or {jinja_file.name}. Run `hyp init` first.", fg="red")
        sys.exit(1)
    
    # 4) Validate config using consolidated function
    validation_errors = validate_config_against_model(data, template, version)
    is_valid = display_validation_results(
        validation_errors,
        success_message="Configuration is valid!",
        error_prefix="Validation errors:"
    )
    
    if not is_valid:
        sys.exit(1)

    try:
        template_source = jinja_file.read_text()
        tpl = Template(template_source)
        
        # For CFN templates, prepare arrays for Jinja template
        if schema_type == CFN:
            # Prepare instance_group_settings array
            instance_group_settings = []
            rig_settings = []
            for i in range(1, 21):
                ig_key = f'instance_group_settings{i}'
                rig_key = f'rig_settings{i}'
                if ig_key in data:
                    instance_group_settings.append(data[ig_key])
                if rig_key in data:
                    rig_settings.append(data[rig_key])
            
            # Add arrays to template context
            template_data = dict(data)
            template_data['instance_group_settings'] = instance_group_settings
            template_data['rig_settings'] = rig_settings
            rendered = tpl.render(**template_data)
        else:
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
        click.secho(f"✔️  Submitted! Files written to {out_dir}", fg="green")
    except Exception as e:
        click.secho(f"❌  Failed to write run files: {e}", fg="red")
        sys.exit(1)

    # 7) Make the downstream call
    try :
        if schema_type == CFN:
            from sagemaker.hyperpod.cli.commands.cluster_stack import create_cluster_stack_helper
            create_cluster_stack_helper(config_file=f"{out_dir}/config.yaml",
                                        region=region)
    except Exception as e:
        click.secho(f"❌  Failed to sumbit the command: {e}", fg="red")
        sys.exit(1)
