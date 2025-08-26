"""
Command Registry System for SageMaker HyperPod CLI

This module provides a centralized way to register and discover CLI commands,
eliminating hardcoded command mappings throughout the codebase.
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
import importlib
from dataclasses import dataclass, field


@dataclass
class CommandMetadata:
    """Metadata for a CLI command"""
    name: str
    help_text: str
    module_name: str
    import_path: str
    parent_group: Optional[str] = None
    
    
@dataclass
class CommandGroup:
    """Represents a CLI command group"""
    name: str
    help_text: str
    commands: List[CommandMetadata] = field(default_factory=list)


class CommandRegistry:
    """
    Central registry for CLI commands that eliminates hardcoded mappings.
    
    Commands register themselves with metadata, and the CLI dynamically
    discovers and loads them as needed.
    """
    
    def __init__(self):
        self._commands: Dict[str, CommandMetadata] = {}
        self._groups: Dict[str, CommandGroup] = {}
        self._module_to_commands: Dict[str, List[str]] = {}
        self._initialized = False
    
    def register_command(
        self,
        name: str,
        help_text: str,
        module_name: str,
        import_path: str,
        parent_group: Optional[str] = None
    ):
        """Register a command with the registry"""
        cmd = CommandMetadata(
            name=name,
            help_text=help_text,
            module_name=module_name,
            import_path=import_path,
            parent_group=parent_group
        )
        
        self._commands[name] = cmd
        
        # Track commands by module
        if module_name not in self._module_to_commands:
            self._module_to_commands[module_name] = []
        self._module_to_commands[module_name].append(name)
        
        # Add to group if specified
        if parent_group:
            if parent_group not in self._groups:
                self._groups[parent_group] = CommandGroup(parent_group, f"{parent_group.title()} operations.")
            self._groups[parent_group].commands.append(cmd)
    
    def register_group(self, name: str, help_text: str):
        """Register a command group"""
        if name not in self._groups:
            self._groups[name] = CommandGroup(name, help_text)
    
    def get_command_metadata(self, name: str) -> Optional[CommandMetadata]:
        """Get metadata for a specific command"""
        return self._commands.get(name)
    
    def get_commands_by_module(self, module_name: str) -> List[CommandMetadata]:
        """Get all commands for a specific module"""
        command_names = self._module_to_commands.get(module_name, [])
        return [self._commands[name] for name in command_names]
    
    def get_top_level_commands(self) -> List[str]:
        """Get all top-level commands (no parent group)"""
        return [name for name, cmd in self._commands.items() if cmd.parent_group is None]
    
    def get_subcommands(self, group_name: str) -> List[str]:
        """Get all subcommands for a group"""
        group = self._groups.get(group_name)
        return [cmd.name for cmd in group.commands] if group else []
    
    def get_all_groups(self) -> List[str]:
        """Get all registered group names"""
        return list(self._groups.keys())
    
    def get_module_for_command(self, name: str) -> Optional[str]:
        """Get the module name that provides a command"""
        cmd = self._commands.get(name)
        return cmd.module_name if cmd else None
    
    def initialize_registry(self):
        """Initialize the registry - commands will self-register via decorators"""
        if self._initialized:
            return
            
        # Register command groups only - commands will auto-register themselves
        self.register_group('create', 'Create endpoints or pytorch jobs.')
        self.register_group('list', 'List endpoints or pytorch jobs.')
        self.register_group('describe', 'Describe endpoints or pytorch jobs.')
        self.register_group('delete', 'Delete endpoints or pytorch jobs.')
        self.register_group('list-pods', 'List pods for endpoints or pytorch jobs.')
        self.register_group('get-logs', 'Get pod logs for endpoints or pytorch jobs.')
        self.register_group('invoke', 'Invoke model endpoints.')
        self.register_group('get-operator-logs', 'Get operator logs for endpoints.')
        
        self._initialized = True
    
    def ensure_commands_loaded(self):
        """Ensure command modules are imported so they can self-register"""
        try:
            # Import modules to trigger self-registration
            import sagemaker.hyperpod.cli.commands.cluster
            import sagemaker.hyperpod.cli.commands.training  
            import sagemaker.hyperpod.cli.commands.inference
        except ImportError:
            pass  # Modules will be loaded when needed


# Command Registration Decorators
def register_command(name: str, module_name: str, parent_group: str = None):
    """
    Decorator that auto-registers commands with the registry.
    Extracts help text from the Click command's docstring.
    
    Usage:
        @register_command("pytorch-job", "training", "create")
        def pytorch_create():
            '''Create a new PyTorch training job.'''
            pass
    """
    def decorator(func):
        # Extract help text from function docstring
        help_text = func.__doc__.strip() if func.__doc__ else f"{name.replace('-', ' ').title()} operations."
        
        # Auto-register with registry (done at import time)
        registry = get_registry()
        registry.register_command(
            name=name,
            help_text=help_text,
            module_name=module_name,
            import_path=f"{func.__module__}:{func.__name__}",
            parent_group=parent_group
        )
        
        # Import click here to avoid import issues during lazy loading
        import click
        
        # Create Click command
        click_cmd = click.command(name)(func)
        
        return click_cmd
    
    return decorator

def register_cluster_command(name: str):
    """Register a top-level cluster command."""
    return register_command(name, 'cluster', parent_group=None)

def register_training_command(name: str, group: str):
    """Register a training command in specified group."""
    return register_command(name, 'training', parent_group=group)

def register_inference_command(name: str, group: str):
    """Register an inference command in specified group."""
    return register_command(name, 'inference', parent_group=group)


# Global registry instance
_registry = CommandRegistry()

def get_registry() -> CommandRegistry:
    """Get the global command registry instance"""
    _registry.initialize_registry()
    return _registry
