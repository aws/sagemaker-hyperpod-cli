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

    def get_command(self, ctx, name):
        """FIXED: This method must return the command object"""
        self._register_module_for_command(name)
        # Call parent's get_command to actually return the command
        return super().get_command(ctx, name)
    
    def _register_module_for_command(self, name):
        """Register only the module needed for a specific command"""
        if name in self._command_module_map:
            module_name = self._command_module_map[name]
            if module_name not in self.modules_registered:
                self._register_module(module_name)
        else:
            # For subgroup commands, we might need to load all for discovery
            # This could be optimized further but is complex with click's architecture
            self._ensure_all_modules_registered()
    
    def _ensure_all_modules_registered(self):
        """Register all modules - used for command listing (hyp --help)"""
        for module in ['training', 'inference', 'cluster']:
            if module not in self.modules_registered:
                self._register_module(module)
    
    def _register_module(self, module_name):
        """Register commands from a specific module"""
        if module_name in self.modules_registered:
            return
        
        if module_name == 'training':
            # LAZY IMPORT: Only import when needed
            from sagemaker.hyperpod.cli.commands.training import (
            pytorch_create, list_jobs, pytorch_describe, pytorch_delete,
            pytorch_list_pods, pytorch_get_logs,
            )
            self.commands['create'].add_command(pytorch_create)
            self.commands['list'].add_command(list_jobs)
            self.commands['describe'].add_command(pytorch_describe)
            self.commands['delete'].add_command(pytorch_delete)
            self.commands['list-pods'].add_command(pytorch_list_pods)
            self.commands['get-logs'].add_command(pytorch_get_logs)
        
        elif module_name == 'inference':
            # LAZY IMPORT: Only import when needed
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
            # LAZY IMPORT: Only import when needed
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


@cli.group(cls=CLICommand, name='list')
def list_cmd():
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
