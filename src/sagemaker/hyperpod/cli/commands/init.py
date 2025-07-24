import click
import yaml
import sys
from pathlib import Path
from pydantic import ValidationError
from datetime import datetime
from jinja2 import Template
import shutil

from sagemaker.hyperpod.cli.constants.init_constants import (
    USAGE_GUIDE_TEXT
)
from sagemaker.hyperpod.cli.init_utils import (
    generate_click_command,
    save_config_yaml,
    TEMPLATES,
    load_config_and_validate,
    build_config_from_schema,
    save_k8s_template
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
        click.secho("💥  Could not write config.yaml: %s", e, fg="red")
        sys.exit(1)

    # 4) Generate K8s template
    if not save_k8s_template(template, dir_path):
        click.secho("⚠️  K8s template generation failed", fg="yellow")

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
    data, template, version = load_config_and_validate(dir_path)
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
    if save_k8s_template(template, dir_path):
        click.secho("✔️  k8s-template.jinja regenerated.", fg="green")


@click.command("configure")
@generate_click_command(
    require_schema_fields=False,  # flags are all optional
    auto_load_config=True,        # load template/namespace/version from config.yaml
)
def configure(model_config):
    """
    Update any subset of fields in ./config.yaml by passing
    --<field> flags. E.g.

      hyp configure --model-name my-model --instance-type ml.m5.large
    """
    # 1) Load existing config
    dir_path = Path(".").resolve()
    data, template, version = load_config_and_validate(dir_path)
    namespace = data.get("namespace", "default")
    
    # 2) Build config with merged values from existing config and user input
    full_cfg, comment_map = build_config_from_schema(
        template=template,
        namespace=namespace,
        version=version,
        model_config=model_config,
        existing_config=data
    )

    # 3) Write out the updated config.yaml
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
    Validate this directory's config.yaml against the JSON schema.
    """
    dir_path = Path(".").resolve()
    data, template, version = load_config_and_validate(dir_path)
    
    info = TEMPLATES[template]
    registry = info["registry"]
    model = registry.get(version)
    if model is None:
        click.secho(f"❌  Unsupported schema version: {version}", fg="red")
        sys.exit(1)

    # prepare only the fields the model knows about
    payload = {
        k: v
        for k, v in data.items()
        if k not in ("template", "namespace")
    }

    try:
        # this will raise ValidationError if anything is invalid
        model(**payload)
        click.secho("✔️  config.yaml is valid!", fg="green")
    except ValidationError as e:
        click.secho("❌  Validation errors:", fg="red")
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            msg = err["msg"]
            click.echo(f"  – {loc}: {msg}")
        sys.exit(1)


@click.command("submit")
def submit():
    """
    Validate config.yaml, render k8s.yaml from k8s.jinja,
    and store both in a timestamped run/ subdirectory.
    """
    dir_path = Path('.').resolve()
    config_file = dir_path / 'config.yaml'
    jinja_file = dir_path / 'k8s.jinja'

    # 1) Ensure files exist
    if not config_file.is_file() or not jinja_file.is_file():
        click.secho("❌  Missing config.yaml or k8s.jinja. Run `hyp init` first.", fg="red")
        sys.exit(1)

    # 2) Load and validate config
    data, template, version = load_config_and_validate(dir_path)
    
    # 3) Validate config against schema
    info = TEMPLATES[template]
    registry = info["registry"]
    model = registry.get(version)
    
    if model is None:
        click.secho(f"❌  Unsupported schema version: {version}", fg="red")
        sys.exit(1)

    payload = {k: v for k, v in data.items() if k not in ('template', 'namespace')}
    try:
        model(**payload)
    except ValidationError as e:
        click.secho("❌  Validation errors:", fg="red")
        for err in e.errors():
            loc = '.'.join(str(x) for x in err['loc'])
            msg = err['msg']
            click.echo(f"  – {loc}: {msg}")
        sys.exit(1)

    # 4) Render Jinja template
    try:
        template_source = jinja_file.read_text()
        tpl = Template(template_source)
        rendered = tpl.render(**data)
    except Exception as e:
        click.secho(f"❌  Failed to render k8s template: {e}", fg="red")
        sys.exit(1)

    # 5) Prepare run/<timestamp> directory and write files
    run_root = dir_path / 'run'
    run_root.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    out_dir = run_root / timestamp
    out_dir.mkdir()

    try:
        shutil.copy(config_file, out_dir / 'config.yaml')
        with open(out_dir / 'k8s.yaml', 'w', encoding='utf-8') as f:
            f.write(rendered)
        click.secho(f"✔️  Submitted! Files written to {out_dir}", fg="green")
    except Exception as e:
        click.secho(f"❌  Failed to write run files: {e}", fg="red")
        sys.exit(1)