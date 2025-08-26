"""
Common lazy loading infrastructure for deferred imports and CLI performance optimization.

This module provides reusable components for implementing lazy loading patterns
that improve startup performance while maintaining full functionality.
"""

import sys
from typing import Any, Dict, List, Callable, Optional, Union


class LazyRegistry:
    """
    A registry that provides version info for CLI generation but lazy-loads model classes for execution.
    
    This class implements a two-tier approach:
    - CLI Generation Time: Provides version info without importing heavy dependencies
    - Execution Time: Lazy-loads the real registry with model classes when needed
    """
    
    def __init__(
        self, 
        versions: List[str], 
        real_registry_loader: Optional[Callable] = None,
        registry_import_path: Optional[str] = None
    ):
        """
        Initialize LazyRegistry.
        
        Args:
            versions: List of supported versions for CLI generation
            real_registry_loader: Function to load the real registry (optional)
            registry_import_path: Import path for the real registry (alternative to loader)
        """
        self.versions = versions
        self.real_registry_loader = real_registry_loader
        self.registry_import_path = registry_import_path
        self._real_registry = None
    
    def _load_real_registry(self):
        """Load the real registry using either the loader function or import path."""
        if self._real_registry is None:
            if self.real_registry_loader:
                self._real_registry = self.real_registry_loader()
            elif self.registry_import_path:
                module_path, attr_name = self.registry_import_path.split(':', 1)
                module = __import__(module_path, fromlist=[attr_name])
                self._real_registry = getattr(module, attr_name)
            else:
                raise ValueError("Either real_registry_loader or registry_import_path must be provided")
    
    def keys(self):
        """Provide version keys for CLI generation."""
        return self.versions
    
    def get(self, version):
        """Lazy-load real model class when needed for execution."""
        self._load_real_registry()
        return self._real_registry.get(version)
    
    def __contains__(self, version):
        """Support version checking for CLI generation."""
        return version in self.versions
    
    def items(self):
        """Support iteration for CLI generation - only provide keys, not values."""
        return [(version, None) for version in self.versions]


class LazyDecorator:
    """
    A decorator that applies decorators based on their type.
    
    CLI generation decorators (like generate_click_command) are applied immediately 
    to ensure proper help text generation. Execution decorators (like telemetry) 
    are deferred until command execution.
    """
    
    def __init__(self, decorator_getter: Callable, *args, **kwargs):
        """
        Initialize LazyDecorator.
        
        Args:
            decorator_getter: Function that returns the decorator
            *args, **kwargs: Arguments to pass to the decorator
        """
        self.decorator_getter = decorator_getter
        self.args = args
        self.kwargs = kwargs
        self._cached_decorator = None
    
    def __call__(self, func):
        """Apply the decorator based on its type."""
        # Check if this is a CLI generation decorator that needs immediate application for help
        if (hasattr(self.decorator_getter, '__name__') and 
            self.decorator_getter.__name__ in ['_get_generate_click_command']):
            return self._apply_immediately(func)
        else:
            # Defer execution decorators like telemetry
            return self._apply_deferred(func)
    
    def _apply_immediately(self, func):
        """Apply decorator immediately for CLI generation."""
        decorator = self.decorator_getter()
        
        # Resolve any callable arguments (like lambda functions)
        resolved_args = [arg() if callable(arg) else arg for arg in self.args]
        resolved_kwargs = {k: (v() if callable(v) else v) for k, v in self.kwargs.items()}
        
        return decorator(*resolved_args, **resolved_kwargs)(func)
    
    def _apply_deferred(self, func):
        """Apply decorator at execution time for runtime decorators."""
        def wrapper(*wrapper_args, **wrapper_kwargs):
            if self._cached_decorator is None:
                decorator = self.decorator_getter()
                
                # Resolve any callable arguments at runtime
                resolved_args = [arg() if callable(arg) else arg for arg in self.args]
                resolved_kwargs = {k: (v() if callable(v) else v) for k, v in self.kwargs.items()}
                
                self._cached_decorator = decorator(*resolved_args, **resolved_kwargs)
                self._decorated_func = self._cached_decorator(func)
            
            return self._decorated_func(*wrapper_args, **wrapper_kwargs)
        
        # Preserve function metadata
        wrapper.__name__ = getattr(func, '__name__', 'wrapped_function')
        wrapper.__doc__ = getattr(func, '__doc__', None)
        return wrapper


class LazyImportManager:
    """
    Manages lazy imports using a mapping-based approach.
    
    This provides a clean, declarative way to define lazy imports without
    coupling to specific module implementations.
    """
    
    def __init__(self, import_mapping: Dict[str, str]):
        """
        Initialize LazyImportManager.
        
        Args:
            import_mapping: Dict mapping attribute names to import paths
                          Format: "module.path:attribute" or "module_name"
        """
        self.import_mapping = import_mapping
        self._cached_imports = {}
    
    def get_lazy_import(self, name: str) -> Any:
        """
        Get a lazy import by name.
        
        Args:
            name: Name of the import to retrieve
            
        Returns:
            The imported object
            
        Raises:
            AttributeError: If the import name is not found
        """
        if name in self._cached_imports:
            return self._cached_imports[name]
        
        if name not in self.import_mapping:
            raise AttributeError(f"No lazy import defined for '{name}'")
        
        import_path = self.import_mapping[name]
        
        if ':' in import_path:
            # Format: "module.path:attribute"
            module_path, attr_name = import_path.split(':', 1)
            module = __import__(module_path, fromlist=[attr_name])
            obj = getattr(module, attr_name)
        else:
            # Format: "module_name" (import entire module)
            obj = __import__(import_path)
        
        # Cache for future access
        self._cached_imports[name] = obj
        return obj
    
    def create_getattr_function(self, module_name: str) -> Callable[[str], Any]:
        """
        Create a __getattr__ function for a module.
        
        Args:
            module_name: Name of the module (for error messages)
            
        Returns:
            A __getattr__ function that can be used in a module
        """
        def __getattr__(name: str) -> Any:
            try:
                obj = self.get_lazy_import(name)
                # Cache it in the module namespace for direct access
                setattr(sys.modules[module_name], name, obj)
                return obj
            except AttributeError:
                raise AttributeError(f"module '{module_name}' has no attribute '{name}'")
        
        return __getattr__


def create_critical_deps_loader(
    dependencies: Dict[str, str],
    module_name: str,
    extra_setup: Optional[Callable] = None
) -> Callable:
    """
    Create a function to load critical dependencies for decorators.
    
    Args:
        dependencies: Dict mapping dependency names to import paths
        module_name: Name of the module (for setting in sys.modules)
        extra_setup: Optional function for additional setup logic
        
    Returns:
        Function that loads critical dependencies
    """
    def _ensure_critical_deps():
        """Load critical dependencies needed for decorators."""
        deps = {}
        
        for name, import_path in dependencies.items():
            try:
                if ':' in import_path:
                    module_path, attr_name = import_path.split(':', 1)
                    module = __import__(module_path, fromlist=[attr_name])
                    obj = getattr(module, attr_name)
                else:
                    obj = __import__(import_path)
                
                deps[name] = obj
                # Set in module namespace for immediate access
                setattr(sys.modules[module_name], name, obj)
            except ImportError:
                # Ignore import errors during module loading
                pass
        
        # Call any extra setup function
        if extra_setup:
            extra_setup(deps)
        
        return deps
    
    return _ensure_critical_deps


def setup_lazy_module(module_name: str, config: Dict[str, Any]) -> None:
    """
    Setup lazy loading infrastructure for a command module.
    
    This eliminates boilerplate by providing a single setup function that handles
    all the lazy loading infrastructure based on configuration.
    
    Args:
        module_name: The __name__ of the module
        config: Configuration dict with keys:
            - exports: List of what should be available (__all__)
            - template_packages: Dict of template package configs
            - critical_deps: List of dependencies needed for decorators
            - lazy_imports: Dict mapping names to import paths
            - extra_setup: Optional function for additional setup
    """
    module = sys.modules[module_name]
    
    # Set __all__ for the module
    if 'exports' in config:
        setattr(module, '__all__', config['exports'])
    
    # Create module config if template packages specified
    if 'template_packages' in config:
        setattr(module, '_MODULE_CONFIG', config['template_packages'])
    
    # Setup critical dependencies
    if 'critical_deps' in config:
        critical_deps = {}
        base_paths = {
            'telemetry_emitter': 'sagemaker.hyperpod.common.telemetry.telemetry_logging:_hyperpod_telemetry_emitter',
            'telemetry_feature': 'sagemaker.hyperpod.common.telemetry.constants:Feature',
            'training_utils': 'sagemaker.hyperpod.cli.training_utils:generate_click_command',
            'inference_utils': 'sagemaker.hyperpod.cli.inference_utils:generate_click_command'
        }
        
        for dep in config['critical_deps']:
            if dep in base_paths:
                # Map to final attribute names
                if dep == 'telemetry_emitter':
                    critical_deps['_hyperpod_telemetry_emitter'] = base_paths[dep]
                elif dep == 'telemetry_feature':
                    critical_deps['Feature'] = base_paths[dep]
                elif dep == 'training_utils':
                    critical_deps['generate_click_command'] = base_paths[dep]
                elif dep == 'inference_utils':
                    critical_deps['generate_click_command'] = base_paths[dep]
            else:
                critical_deps[dep] = config['lazy_imports'].get(dep, dep)
        
        # Create and call critical deps loader
        extra_setup = config.get('extra_setup')
        ensure_critical_deps = create_critical_deps_loader(
            dependencies=critical_deps,
            module_name=module_name,
            extra_setup=extra_setup
        )
        ensure_critical_deps()
        setattr(module, '_ensure_critical_deps', ensure_critical_deps)
    
    # Setup lazy imports
    if 'lazy_imports' in config:
        import_manager = LazyImportManager(config['lazy_imports'])
        getattr_func = import_manager.create_getattr_function(module_name)
        setattr(module, '__getattr__', getattr_func)
        setattr(module, '_import_manager', import_manager)
    
    # Helper functions for decorators
    if 'telemetry_emitter' in config.get('critical_deps', []):
        def _get_telemetry_emitter():
            return getattr(module, '_hyperpod_telemetry_emitter')
        setattr(module, '_get_telemetry_emitter', _get_telemetry_emitter)
    
    if any('utils' in dep for dep in config.get('critical_deps', [])):
        def _get_generate_click_command():
            return getattr(module, 'generate_click_command')
        setattr(module, '_get_generate_click_command', _get_generate_click_command)
