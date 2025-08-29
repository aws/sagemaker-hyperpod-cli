"""
Lightweight command manifest for fast CLI startup.

This module provides command metadata without importing heavy dependencies.
It's designed to be imported quickly during CLI initialization.
"""

# Command manifest - lightweight metadata without heavy imports
COMMAND_MANIFEST = {
    # Top-level cluster commands
    'list-cluster': {
        'module': 'cluster',
        'help': 'List available SageMaker HyperPod clusters.'
    },
    'set-cluster-context': {
        'module': 'cluster', 
        'help': 'Configure local Kubectl environment.'
    },
    'get-cluster-context': {
        'module': 'cluster',
        'help': 'Get current cluster context information.'
    },
    'get-monitoring': {
        'module': 'cluster',
        'help': 'Get monitoring configuration and URLs.'
    },
    
    # Top-level init commands
    'init': {
        'module': 'init',
        'help': 'Initialize a new HyperPod project.'
    },
    'reset': {
        'module': 'init',
        'help': 'Reset HyperPod configuration.'
    },
    'configure': {
        'module': 'init', 
        'help': 'Configure HyperPod settings.'
    },
    'validate': {
        'module': 'init',
        'help': 'Validate HyperPod configuration.'
    }
}

def get_module_for_command(command_name: str) -> str:
    """Get the module name for a command without importing anything."""
    return COMMAND_MANIFEST.get(command_name, {}).get('module')

def get_help_for_command(command_name: str) -> str:
    """Get help text for a command without importing anything."""
    return COMMAND_MANIFEST.get(command_name, {}).get('help', f'{command_name.replace("-", " ").title()} operations.')

def get_top_level_commands() -> list:
    """Get all top-level commands without importing anything."""
    return list(COMMAND_MANIFEST.keys())