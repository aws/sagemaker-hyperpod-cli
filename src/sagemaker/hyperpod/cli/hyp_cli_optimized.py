import click
from typing import Optional
import importlib

class TruelyLazyGroup(click.Group):
    """A Click group that defers ALL imports until command execution"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._command_registry = {}
        self._loaded_modules = set()
        
        # Register commands as lightweight callables instead of importing modules
        self._setup_command_registry()
    
    def _setup_command_registry(self):
        """Setup command registry without importing any heavy modules"""
        
        # Top-level cluster commands
        self._command_registry.update({
            'list-cluster': ('cluster', 'list_cluster'),
            'set-cluster-context': ('cluster', 'set_cluster_context'), 
            'get-cluster-context': ('cluster', 'get_cluster_context'),
            'get-monitoring': ('cluster', 'get_monitoring')
        })

        # Create command groups without triggering imports
        self._create_command_groups()
    
    def _create_command_groups(self):
        """Create command groups with lazy-loaded subcommands"""
        
        # Training subcommands
        training_cmds = {
            'pytorch-job': ('training', 'pytorch_create')
        }
        
        # Inference subcommands  
        inference_cmds = {
            'hyp-jumpstart-endpoint': ('inference', 'js_create'),
            'hyp-custom-endpoint': ('inference', 'custom_create')
        }
        
        # Store subcommand mappings
        self._subcommand_registry = {
            'create': {**training_cmds, **inference_cmds},
            'list': {
                'pytorch-job': ('training', 'list_jobs'),
                'hyp-jumpstart-endpoint': ('inference', 'js_list'),
                'hyp-custom-endpoint': ('inference', 'custom_list')
            },
            'describe': {
                'pytorch-job': ('training', 'pytorch_describe'),
                'hyp-jumpstart-endpoint': ('inference', 'js_describe'),
                'hyp-custom-endpoint': ('inference', 'custom_describe')
            },
            'delete': {
                'pytorch-job': ('training', 'pytorch_delete'),
                'hyp-jumpstart-endpoint': ('inference', 'js_delete'),
                'hyp-custom-endpoint': ('inference', 'custom_delete')
            },
            'list-pods': {
                'pytorch-job': ('training', 'pytorch_list_pods'),
                'hyp-jumpstart-endpoint': ('inference', 'js_list_pods'),
                'hyp-custom-endpoint': ('inference', 'custom_list_pods')
            },
            'get-logs': {
                'pytorch-job': ('training', 'pytorch_get_logs'),
                'hyp-jumpstart-endpoint': ('inference', 'js_get_logs'),
                'hyp-custom-endpoint': ('inference', 'custom_get_logs')
            },
            'invoke': {
                'hyp-custom-endpoint': ('inference', 'custom_invoke')
            },
            'get-operator-logs': {
                'hyp-jumpstart-endpoint': ('inference', 'js_get_operator_logs'),
                'hyp-custom-endpoint': ('inference', 'custom_get_operator_logs')
            }
        }
    
    def get_command(self, ctx, name):
        """Get command with true lazy loading"""
        # Handle top-level commands
        if name in self._command_registry:
            module_name, func_name = self._command_registry[name]
            return self._load_command(module_name, func_name)
        
        # Handle subgroup commands (create, list, etc.)
        if hasattr(self, 'commands') and name in self.commands:
            return self.commands[name]
        
        return None
    
    def _load_command(self, module_name, func_name):
        """Load a specific command function without importing heavy dependencies"""
        try:
            if module_name == 'cluster':
                from sagemaker.hyperpod.cli.commands.cluster import (
                    list_cluster, set_cluster_context, get_cluster_context, get_monitoring
                )
                return locals()[func_name]
            elif module_name == 'training':
                from sagemaker.hyperpod.cli.commands.training_optimized import (
                    pytorch_create, list_jobs, pytorch_describe, pytorch_delete,
                    pytorch_list_pods, pytorch_get_logs
                )
                return locals()[func_name]
            elif module_name == 'inference':
                from sagemaker.hyperpod.cli.commands.inference_optimized import (
                    js_create, custom_create, custom_invoke, js_list, custom_list,
                    js_describe, custom_describe, js_delete, custom_delete,
                    js_list_pods, custom_list_pods, js_get_logs, custom_get_logs,
                    js_get_operator_logs, custom_get_operator_logs
                )
                return locals()[func_name]
        except ImportError as e:
            # Fallback to original modules if optimized versions don't exist
            return self._load_original_command(module_name, func_name)
    
    def _load_original_command(self, module_name, func_name):
        """Fallback to load from original modules"""
        if module_name == 'training':
            from sagemaker.hyperpod.cli.commands.training import (
                pytorch_create, list_jobs, pytorch_describe, pytorch_delete,
                pytorch_list_pods, pytorch_get_logs
            )
            return locals()[func_name]
        elif module_name == 'inference':
            from sagemaker.hyperpod.cli.commands.inference import (
                js_create, custom_create, custom_invoke, js_list, custom_list,
                js_describe, custom_describe, js_delete, custom_delete,
                js_list_pods, custom_list_pods, js_get_logs, custom_get_logs,
                js_get_operator_logs, custom_get_operator_logs
            )
            return locals()[func_name]
    
    def list_commands(self, ctx):
        """List available commands without triggering heavy imports"""
        commands = list(self._command_registry.keys())
        commands.extend(['create', 'list', 'describe', 'delete', 'list-pods', 'get-logs', 'invoke', 'get-operator-logs'])
        return sorted(commands)

class LazySubGroup(click.Group):
    """Lazy loading subgroup for nested commands"""
    
    def __init__(self, parent_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_name = parent_name
        self._parent_cli = None
    
    def get_command(self, ctx, name):
        # Get parent CLI reference
        if not self._parent_cli:
            self._parent_cli = ctx.find_root().command
        
        if hasattr(self._parent_cli, '_subcommand_registry'):
            subcommands = self._parent_cli._subcommand_registry.get(self.parent_name, {})
            if name in subcommands:
                module_name, func_name = subcommands[name]
                return self._parent_cli._load_command(module_name, func_name)
        return None
    
    def list_commands(self, ctx):
        if not self._parent_cli:
            self._parent_cli = ctx.find_root().command
        
        if hasattr(self._parent_cli, '_subcommand_registry'):
            return sorted(self._parent_cli._subcommand_registry.get(self.parent_name, {}).keys())
        return []

# Create CLI with true lazy loading
cli = TruelyLazyGroup()

# Create subgroups
@cli.group(cls=LazySubGroup, parent_name='create')
def create():
    """Create endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='list', name='list')
def list_cmd():
    """List endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='describe')
def describe():
    """Describe endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='delete')
def delete():
    """Delete endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='list-pods')
def list_pods():
    """List pods for endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='get-logs')
def get_logs():
    """Get pod logs for endpoints or pytorch jobs."""
    pass

@cli.group(cls=LazySubGroup, parent_name='invoke')
def invoke():
    """Invoke model endpoints."""
    pass

@cli.group(cls=LazySubGroup, parent_name='get-operator-logs')
def get_operator_logs():
    """Get operator logs for endpoints."""
    pass

if __name__ == "__main__":
    cli()
