import click
from typing import Optional

# Custom CLI group that delays command registration until needed
class LazyGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ensure that duplicate modules aren't loaded
        self.modules_registered = set()
        
        # map commands to respective modules for selective loading, top level commands
        self._command_module_map = {
            'list-cluster': 'cluster',
            'set-cluster-context': 'cluster', 
            'get-cluster-context': 'cluster',
            'get-monitoring': 'cluster'
        }

        # nested commands
        # can be a maintenance burden if we were to add many new commands
        self._subcommand_module_map = {
            ('create', 'pytorch-job'): 'training',
            ('list', 'pytorch-job'): 'training', 
            ('describe', 'pytorch-job'): 'training',
            ('delete', 'pytorch-job'): 'training',
            ('list-pods', 'pytorch-job'): 'training',
            ('get-logs', 'pytorch-job'): 'training',
            ('create', 'hyp-jumpstart-endpoint'): 'inference',
            ('create', 'hyp-custom-endpoint'): 'inference',
            ('list', 'hyp-jumpstart-endpoint'): 'inference',
            ('list', 'hyp-custom-endpoint'): 'inference',
            ('describe', 'hyp-jumpstart-endpoint'): 'inference',
            ('describe', 'hyp-custom-endpoint'): 'inference',
            ('delete', 'hyp-jumpstart-endpoint'): 'inference',
            ('delete', 'hyp-custom-endpoint'): 'inference',
            ('list-pods', 'hyp-jumpstart-endpoint'): 'inference',
            ('list-pods', 'hyp-custom-endpoint'): 'inference',
            ('get-logs', 'hyp-jumpstart-endpoint'): 'inference',
            ('get-logs', 'hyp-custom-endpoint'): 'inference',
            ('get-operator-logs', 'hyp-jumpstart-endpoint'): 'inference',
            ('get-operator-logs', 'hyp-custom-endpoint'): 'inference',
            ('invoke', 'hyp-custom-endpoint'): 'inference',
        }

    def list_commands(self, ctx):
        """Return list of commands without loading modules"""
        # Return static list to avoid loading modules for help
        base_commands = ['create', 'list', 'describe', 'delete', 'list-pods', 'get-logs', 'invoke', 'get-operator-logs']
        cluster_commands = ['list-cluster', 'set-cluster-context', 'get-cluster-context', 'get-monitoring']
        return sorted(base_commands + cluster_commands)
    
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
        commands = []
        # Static command descriptions to avoid module loading
        command_help = {
            'create': 'Create endpoints or pytorch jobs.',
            'delete': 'Delete endpoints or pytorch jobs.',
            'describe': 'Describe endpoints or pytorch jobs.',
            'get-logs': 'Get pod logs for endpoints or pytorch jobs.',
            'get-operator-logs': 'Get operator logs for endpoints.',
            'invoke': 'Invoke model endpoints.',
            'list': 'List endpoints or pytorch jobs.',
            'list-pods': 'List pods for endpoints or pytorch jobs.',
            'list-cluster': 'List available SageMaker HyperPod clusters.',
            'set-cluster-context': 'Configure kubectl to interact with a cluster.',
            'get-cluster-context': 'Get current cluster context.',
            'get-monitoring': 'Get monitoring configuration.'
        }
        
        for name in self.list_commands(ctx):
            help_text = command_help.get(name, '')
            commands.append((name, help_text))
        
        if commands:
            with formatter.section('Commands'):
                formatter.write_dl(commands)

    def get_command(self, ctx, name):
        # Register modules for subgroups to ensure help works
        self._register_module_for_command(name)
        return super().get_command(ctx, name)
    
    def _register_module_for_command(self, name):
        """Register only the module needed for a specific command"""
        if name in self._command_module_map:
            module_name = self._command_module_map[name]
            if module_name not in self.modules_registered:
                self._register_module(module_name)
        elif name in ['create', 'list', 'describe', 'delete', 'list-pods', 'get-logs', 'invoke', 'get-operator-logs']:
            # These are subgroup commands - register all modules so subcommands show in help
            self._ensure_all_modules_registered()
    
    def _ensure_all_modules_registered(self):
        """Register all modules - used when actually accessing subcommands"""
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
            pytorch_list_pods, pytorch_get_logs,
            )
            # pytorch_create is a factory function that returns a command
            self.commands['create'].add_command(pytorch_create())
            # All others are already command objects - don't call them!
            self.commands['list'].add_command(list_jobs)
            self.commands['describe'].add_command(pytorch_describe)
            self.commands['delete'].add_command(pytorch_delete)
            self.commands['list-pods'].add_command(pytorch_list_pods)
            self.commands['get-logs'].add_command(pytorch_get_logs)
        
        elif module_name == 'inference':
            from sagemaker.hyperpod.cli.commands.inference import (
                js_create, custom_create, custom_invoke, js_list, custom_list,
                js_describe, custom_describe, js_delete, custom_delete,
                js_list_pods, custom_list_pods, js_get_logs, custom_get_logs,
                js_get_operator_logs, custom_get_operator_logs,
            )
            # Factory functions that return commands (need to be called)
            self.commands['create'].add_command(js_create())
            self.commands['create'].add_command(custom_create())
            # Command objects (should NOT be called)
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
