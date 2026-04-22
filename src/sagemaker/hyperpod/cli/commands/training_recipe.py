from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml
import json
import sys
import click
from pathlib import Path
from sagemaker.hyperpod.cli.init_utils import load_dynamic_schema
from sagemaker.hyperpod.common.utils import handle_exception
from sagemaker.hyperpod.cli.type_handler_utils import is_undefined_value
from sagemaker.hyperpod.cli.recipe_utils import (
    _fetch_recipe_from_hub, _download_s3_content, _download_s3_json,
    _validate_and_convert_value, _collect_all_parameters_interactively,
    _submit_k8s_resources, _render_k8s_template, _get_sagemaker_client,
    _get_s3_client, _get_k8s_custom_client, _validate_dynamic_template,
    _generate_dynamic_config_yaml, _update_config_field
)
import shutil
from sagemaker.hyperpod.common.telemetry.constants import Feature
from sagemaker.hyperpod.common.telemetry.telemetry_logging import _hyperpod_telemetry_emitter
from sagemaker.hyperpod.common.cli_decorators import handle_cli_exceptions


def _interactive_cluster_selection(sagemaker_client, model_id: str, job_type: str, technique: str = None, is_huggingface: bool = False):
    """Interactive cluster and instance type selection."""
    try:
        matching_recipe = _fetch_recipe_from_hub(sagemaker_client, model_id, job_type, technique, None, is_huggingface=is_huggingface)
        supported_instance_types = set(matching_recipe.get('SupportedInstanceTypes', []))

        if not supported_instance_types:
            click.secho("❌ No supported instance types found in recipe", fg="red")
            return None, None

        click.secho("🔍 Fetching available clusters...", fg="blue")

        try:
            from sagemaker.hyperpod.cli.commands.cluster import _get_hyperpod_clusters
            from sagemaker.hyperpod.common.utils import get_current_cluster

            cluster_names = _get_hyperpod_clusters(sagemaker_client)
            if not cluster_names:
                click.secho("❌ No HyperPod clusters found", fg="red")
                return None, None

            # Build {cluster_name: [(instance_type, node_count), ...]} for compatible types only
            clusters_map: dict = {}
            lock = threading.Lock()

            def _fetch_cluster(cluster_name: str):
                try:
                    cluster_response = sagemaker_client.describe_cluster(ClusterName=cluster_name)
                    compatible = [
                        (g.get('InstanceType'), g.get('CurrentCount', 0))
                        for g in cluster_response.get('InstanceGroups', [])
                        if g.get('InstanceType') in supported_instance_types
                    ]
                    if compatible:
                        with lock:
                            clusters_map[cluster_name] = compatible
                except Exception as e:
                    click.secho(f"⚠️ Warning: Could not get details for cluster {cluster_name}: {e}", fg="yellow")

            with ThreadPoolExecutor(max_workers=min(len(cluster_names), 10)) as executor:
                list(executor.map(_fetch_cluster, cluster_names))

            if not clusters_map:
                click.secho("❌ No cluster details could be retrieved", fg="red")
                return None, None

        except Exception as e:
            click.secho(f"❌ Error fetching clusters: {e}", fg="red")
            return None, None

        if not clusters_map:
            click.secho(
                f"❌ No compatible clusters found. The '{technique or job_type}' recipe for "
                f"'{model_id}' requires one of: {sorted(supported_instance_types)}",
                fg="red",
            )
            click.secho(
                "   To skip cluster auto-detection, specify the instance type directly: --instance-type <instance-type>",
                fg="yellow",
            )
            return None, None

        # Detect current cluster context
        current_cluster = None
        try:
            current_cluster = get_current_cluster()
        except Exception:
            pass

        def _prompt_instance_type(cluster_name: str) -> str | None:
            instance_types = clusters_map[cluster_name]
            click.secho(f"\n📋 Compatible instance types for {cluster_name}:", fg="green")
            for i, (itype, nodes) in enumerate(instance_types, 1):
                click.secho(f"  {i}. {itype:<22} ({nodes} nodes)", fg="white")
            while True:
                try:
                    choice = click.prompt(f"Select an instance type (1-{len(instance_types)})", type=int)
                    if 1 <= choice <= len(instance_types):
                        return instance_types[choice - 1][0]
                    click.secho(f"❌ Please enter a number between 1 and {len(instance_types)}", fg="red")
                except (ValueError, click.Abort):
                    click.secho("❌ Operation cancelled", fg="red")
                    return None

        # If current context cluster is compatible, offer it as default
        if current_cluster and current_cluster in clusters_map:
            click.secho(f"\nCurrent cluster context: {current_cluster}", fg="cyan")
            instance_type = _prompt_instance_type(current_cluster)
            if instance_type is None:
                return None, None
            # Ask if they want to use a different cluster
            try:
                use_different = click.confirm("Use a different cluster?", default=False)
            except click.Abort:
                click.secho("❌ Operation cancelled", fg="red")
                return None, None
            if not use_different:
                click.secho(f"✔️ Selected: {current_cluster} ({instance_type})", fg="green")
                return current_cluster, instance_type

        # Full cluster selection
        cluster_list = list(clusters_map.keys())
        click.secho(f"\n📋 Compatible clusters ({len(cluster_list)} found):", fg="green")
        click.secho("-" * 80, fg="blue")
        for i, name in enumerate(cluster_list, 1):
            types_summary = ", ".join(f"{t} ({n} nodes)" for t, n in clusters_map[name])
            click.secho(f"{i}. {name:<40} {types_summary}", fg="cyan")

        while True:
            try:
                choice = click.prompt(f"\nSelect a cluster (1-{len(cluster_list)})", type=int)
                if 1 <= choice <= len(cluster_list):
                    selected_cluster = cluster_list[choice - 1]
                    break
                click.secho(f"❌ Please enter a number between 1 and {len(cluster_list)}", fg="red")
            except (ValueError, click.Abort):
                click.secho("❌ Operation cancelled", fg="red")
                return None, None

        instance_type = _prompt_instance_type(selected_cluster)
        if instance_type is None:
            return None, None

        click.secho(f"✔️ Selected: {selected_cluster} ({instance_type})", fg="green")
        return selected_cluster, instance_type

    except ValueError as e:
        click.secho(f"❌ {e}", fg="red")
        return None, None
    except Exception as e:
        click.secho(f"❌ Error during cluster selection: {e}", fg="red")
        return None, None


def _init_training_job(directory: str, job_type: str, model_id: str, technique: str, instance_type: str = None, is_huggingface: bool = False) -> bool:
    """Initialize training job configuration."""
    try:
        sagemaker_client = _get_sagemaker_client()
        s3_client = _get_s3_client()

        # If instance_type not provided, use interactive selection
        cluster_name = None
        if not instance_type:
            cluster_name, instance_type = _interactive_cluster_selection(
                sagemaker_client, model_id, job_type, technique, is_huggingface=is_huggingface
            )
            if not instance_type:
                return False

        # Update kubeconfig to point at the selected cluster
        if cluster_name:
            from sagemaker.hyperpod.cli.commands.cluster import set_cluster_context
            click.secho(f"🔧 Connecting to cluster: {cluster_name}", fg="blue")
            set_cluster_context.main(["--cluster-name", cluster_name], standalone_mode=False)
        
        # Fetch and validate recipe
        matching_recipe = _fetch_recipe_from_hub(sagemaker_client, model_id, job_type, technique, instance_type, is_huggingface=is_huggingface)
        
        override_params_uri = matching_recipe.get('HpEksOverrideParamsS3Uri')
        k8s_template_uri = matching_recipe.get('HpEksPayloadTemplateS3Uri')
        
        if not override_params_uri or not k8s_template_uri:
            click.secho("❌ Missing S3 URIs in recipe", fg="red")
            return False
        
        # Create directory
        dir_path = Path(directory).resolve()
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Download and save override params
        override_data = _download_s3_json(s3_client, override_params_uri)
        with open(dir_path / '.override_spec.json', 'w') as f:
            json.dump(override_data, f, indent=2)
        
        # Create config.yaml
        _generate_dynamic_config_yaml(dir_path, job_type, model_name=model_id, technique=technique, instance_type=instance_type)
        
        # Download and save k8s template
        k8s_content = _download_s3_content(s3_client, k8s_template_uri)
        with open(dir_path / 'k8s.jinja', 'w') as f:
            f.write(k8s_content)
        
        return True
        
    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        return False

def _configure_dynamic_template(ctx, option, value, dir_path):
    """Handle configure for dynamic templates (recipe)"""
    config_path = dir_path / "config.yaml"
    spec_path = dir_path / ".override_spec.json"
    
    if not spec_path.exists():
        click.secho(f"❌ .override_spec.json not found", fg="red")
        ctx.exit(1)
    
    # Load spec
    spec = load_dynamic_schema(dir_path)
    
    # Check if user provided --option flags (only those explicitly provided, not defaults)
    provided_options = {}
    for param_name, param_value in ctx.params.items():
        if param_name not in ['option', 'value', 'model_config']:
            # Check if this parameter was actually provided by the user (not a default)
            param_source = ctx.get_parameter_source(param_name)
            if param_source and param_source.name == 'COMMANDLINE' and param_value is not None:
                # Convert back to original key format
                original_key = param_name.replace('-', '_')
                if original_key in spec:
                    provided_options[original_key] = param_value
    
    # If --option flags were used, process them
    if provided_options:
        for key, value in provided_options.items():
            _update_config_field(config_path, spec, key, value)
        click.secho("✔️  config.yaml updated successfully.", fg="green")
        return

    # If no arguments, show help
    click.echo(ctx.get_help())
    ctx.exit(0)


def _warn_if_instance_type_unavailable(instance_type: str) -> None:
    """Warn if the requested instance type has no ready nodes in the current cluster."""
    try:
        config.load_kube_config()
        v1 = client.CoreV1Api()
        nodes = v1.list_node().items
        available = {
            n.metadata.labels.get("node.kubernetes.io/instance-type")
            for n in nodes
            if n.metadata.labels
        }
        available.discard(None)
        if instance_type and instance_type not in available:
            click.secho(
                f"⚠️  Instance type '{instance_type}' not found in the current cluster.\n"
                f"   Available: {', '.join(sorted(available)) or 'none'}\n"
                f"   The job will be submitted but pods may remain Pending.",
                fg="yellow"
            )
    except Exception as e:
        click.secho(f"⚠️  Could not verify instance type availability: {e}", fg="yellow")


def _create_dynamic_template(dir_path: Path, config_data: dict):
    """Handle create for dynamic templates (recipe)"""
    try:
        # Validate config first
        _validate_dynamic_template(dir_path)
        click.secho("✔️ Configuration validated successfully", fg="green")

        # Warn if instance type isn't available in the cluster
        _warn_if_instance_type_unavailable(config_data.get('instance_type'))
        
        k8s_template_file = dir_path / 'k8s.jinja'
        if not k8s_template_file.exists():
            raise FileNotFoundError("k8s.jinja template not found")
        
        # Read and render template
        template_content = k8s_template_file.read_text()
        rendered = _render_k8s_template(template_content, config_data)
        
        # Create run directory
        run_root = dir_path / 'run'
        run_root.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
        out_dir = run_root / timestamp
        out_dir.mkdir()
        
        # Save files
        shutil.copy(dir_path / 'config.yaml', out_dir / 'config.yaml')
        (out_dir / 'k8s.yaml').write_text(rendered)
        
        relative_out_dir = Path("run") / timestamp
        click.secho(f"✔️ Files written to {relative_out_dir}", fg="green")
        
        # Submit to Kubernetes
        custom_api = _get_k8s_custom_client()
        _submit_k8s_resources(custom_api, rendered)
        
        click.secho("✔️ Successfully submitted to HyperPod", fg="green")
                
    except (FileNotFoundError, ValueError) as e:
        click.secho(f"❌ {e}", fg="red")
        sys.exit(1)
    except Exception as e:
        try:
            resource_name = config_data.get('name', 'unknown')
            handle_exception(e, resource_name, 'default')
        except Exception as handled_e:
            click.secho(f"❌ {handled_e}", fg="red")
        sys.exit(1)
