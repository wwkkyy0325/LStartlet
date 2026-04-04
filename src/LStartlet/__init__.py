"""
LStartlet Core Infrastructure Framework

A modular Python infrastructure framework providing high cohesion and low coupling
for Python applications through unified component management.

This framework offers standardized solutions for:
- Command System: Command pattern execution with event-driven lifecycle
- Decorators: Common utilities for error handling, logging, permissions, and metrics

Usage:
    from LStartlet import BaseCommand, CommandResult, with_error_handling
    
    # Define a command
    @with_error_handling
    class MyCommand(BaseCommand):
        def execute(self):
            return CommandResult.success("Hello")
"""

import importlib.metadata

# Get version from package metadata (setuptools_scm)
try:
    __version__ = importlib.metadata.version("LStartlet")
except importlib.metadata.PackageNotFoundError:
    # Package is not installed, fallback to development version
    __version__ = "0.1.0.dev0"

# Import core module exports
from LStartlet.core import (
    # Decorators
    with_error_handling,
    with_logging,
    plugin_component,
    plugin_event_handler,
    with_error_handling_async,
    with_logging_async,
    cached_async,
    require_permission,
    require_permission_async,
    PermissionLevel,
    monitor_metrics,
    monitor_metrics_async,
    MetricsCollector,
    register_service,
    register_plugin,
    register_command,
    
    # Dependency Injection System
    ServiceContainer,
    ServiceLifetime,
    get_default_container,
    
    # Command System - 仅暴露核心抽象接口
    BaseCommand,
    CommandResult,
    CommandMetadata,

)

# Re-export version
__all__ = [
    "__version__",
    
    # Decorators
    "with_error_handling",
    "with_logging",
    "plugin_component",
    "plugin_event_handler",
    "with_error_handling_async",
    "with_logging_async",
    "cached_async",
    "require_permission",
    "require_permission_async",
    "PermissionLevel",
    "monitor_metrics",
    "monitor_metrics_async",
    "MetricsCollector",
    "register_service",
    "register_plugin",
    "register_command",
    
    # Dependency Injection System
    "ServiceContainer",
    "ServiceLifetime", 
    "get_default_container",

    # Command System - 仅暴露核心抽象接口
    "BaseCommand",
    "CommandResult",
    "CommandMetadata",

]
