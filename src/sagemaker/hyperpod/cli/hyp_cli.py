import click
from typing import Optional
from .command_registry import get_registry

# Custom CLI group that delays command registration until needed
class LazyGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.registry = get_registry()
        
        # ensure that duplicate modules aren't loaded
        self.modules_registered = set()

    def list_commands(self, ctx):
        """Return list of commands without loading modules"""
        # Return static command list for fast help generation (no module loading)
        return sorted([
            'create', 'list', 'describe', 'delete', 'list-pods', 'get-logs', 
            'invoke', 'get-operator-logs', 'list-cluster', 'set-cluster-context', 
            'get-cluster-context', 'get-monitoring'
        ])
    
    def get_help(self, ctx):
        """Override get_help to avoid loading modules for help text"""
        # Generate help without loading heavy modules
        formatter = ctx.make_formatter()
        self.format_help(ctx, formatter)
        return formatter.getvalue()
    
    def format_usage(self, ctx, formatter):
        """Format usage without loading modules"""
        pieces = self.collect_usage_pieces(ctx)
        prog_name = ctx.find_root().info_name
        formatter.write_usage(prog_name, ' '.join(pieces))
    
    def format_help(self, ctx, formatter):
        """Format help without loading modules"""
        self.format_usage(ctx, formatter)
        self.format_help_text(ctx, formatter)
        self.format_options(ctx, formatter)
        self.format_commands(ctx, formatter)
    
    def format_commands(self, ctx, formatter):
        """Format commands section without loading modules"""
        # Static help text mapping for fast help generation (no registry queries)
        static_help = {
            'create': 'Create endpoints or pytorch jobs.',
            'list': 'List endpoints or pytorch jobs.',
            'describe': 'Describe endpoints or pytorch jobs.',
            'delete': 'Delete endpoints or pytorch jobs.',
            'list-pods': 'List pods for endpoints or pytorch jobs.',
            'get-logs': 'Get pod logs for endpoints or pytorch jobs.',
            'invoke': 'Invoke model endpoints.',
            'get-operator-logs': 'Get operator logs for endpoints.',
            'list-cluster': 'List SageMaker Hyperpod Clusters with metadata.',
            'set-cluster-context': 'Connect to a HyperPod EKS cluster.',
            'get-cluster-context': 'Get context related to the current set cluster.',
            'get-monitoring': 'Get monitoring configurations for Hyperpod cluster.'
        }
        
        commands = []
        for name in self.list_commands(ctx):
            help_text = static_help.get(name, f'{name.replace("-", " ").title()} operations.')
            commands.append((name, help_text))
        
        if commands:
            with formatter.section('Commands'):
                formatter.write_dl(commands)

    def get_command(self, ctx, name):
        self.registry.ensure_commands_loaded()
        
        # Register modules when actually needed
        self._register_module_for_command(name)
        return super().get_command(ctx, name)
    
    
    def _register_module_for_command(self, name):
        """Register only the module needed for a specific command"""
        module_name = self.registry.get_module_for_command(name)
        
        if module_name and module_name not in self.modules_registered:
            self._register_module(module_name)
        elif name in self.registry.get_all_groups():
            # These are subgroup commands - register all modules so subcommands show in help
            self._ensure_all_modules_registered()
    
    def _ensure_all_modules_registered(self):
        """Register all modules - used when actually accessing subcommands"""
        # Trigger self-registration by ensuring commands are loaded
        self.registry.ensure_commands_loaded()
        
        for module in ['training', 'inference', 'cluster']:
            if module not in self.modules_registered:
                self._register_module(module)
    
    def _register_module(self, module_name):
        """Register commands from a specific module"""
        if module_name in self.modules_registered:
            return
        
        if module_name == 'training':
            from sagemaker.hyperpod.cli.commands.training import (
            pytorch_create, list_jobs, pytorch_describe, pytorch_delete,
            pytorch_list_pods, pytorch_get_logs, pytorch_get_operator_logs
            )

            self.commands['create'].add_command(pytorch_create)
            self.commands['list'].add_command(list_jobs)
            self.commands['describe'].add_command(pytorch_describe)
            self.commands['delete'].add_command(pytorch_delete)
            self.commands['list-pods'].add_command(pytorch_list_pods)
            self.commands['get-logs'].add_command(pytorch_get_logs)
            self.commands['get-operator-logs'].add_command(pytorch_get_operator_logs)
        
        elif module_name == 'inference':
            from sagemaker.hyperpod.cli.commands.inference import (
                js_create, custom_create, custom_invoke, js_list, custom_list,
                js_describe, custom_describe, js_delete, custom_delete,
                js_list_pods, custom_list_pods, js_get_logs, custom_get_logs,
                js_get_operator_logs, custom_get_operator_logs,
            )

            self.commands['create'].add_command(js_create)
            self.commands['create'].add_command(custom_create)
            self.commands['list'].add_command(js_list)
            self.commands['list'].add_command(custom_list)
            self.commands['describe'].add_command(js_describe)
            self.commands['describe'].add_command(custom_describe)
            self.commands['delete'].add_command(js_delete)
            self.commands['delete'].add_command(custom_delete)
            self.commands['list-pods'].add_command(js_list_pods)
            self.commands['list-pods'].add_command(custom_list_pods)
            self.commands['get-logs'].add_command(js_get_logs)
            self.commands['get-logs'].add_command(custom_get_logs)
            self.commands['get-operator-logs'].add_command(js_get_operator_logs)
            self.commands['get-operator-logs'].add_command(custom_get_operator_logs)
            self.commands['invoke'].add_command(custom_invoke)

        elif module_name == 'cluster':
            from sagemaker.hyperpod.cli.commands.cluster import list_cluster, set_cluster_context, get_cluster_context, get_monitoring
            self.add_command(list_cluster)
            self.add_command(set_cluster_context)
            self.add_command(get_cluster_context)
            self.add_command(get_monitoring)
            
        self.modules_registered.add(module_name)
            

class CLICommand(click.Group):
    pass


# Create CLI with lazy loading
cli = LazyGroup()

# Create subgroups, lightweight and don't trigger imports
@cli.group(cls=CLICommand)
def create():
    """Create endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def list():
    """List endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def describe():
    """Describe endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def delete():
    """Delete endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def list_pods():
    """List pods for endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def get_logs():
    """Get pod logs for endpoints or pytorch jobs."""
    pass


@cli.group(cls=CLICommand)
def invoke():
    """Invoke model endpoints."""
    pass


@cli.group(cls=CLICommand)
def get_operator_logs():
    """Get operator logs for endpoints."""
    pass


if __name__ == "__main__":
    cli()
