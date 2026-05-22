"""
MICKEY Plugin System.

Plugins are auto-discovered from this directory.
Each plugin is a Python file with a class that extends MickeyPlugin.

To create a plugin:
1. Create a new .py file in this directory
2. Define a class that extends MickeyPlugin
3. Implement on_load(), get_commands(), and handle_command()
4. MICKEY auto-discovers and registers it on startup
"""

import os
import importlib
import inspect
from abc import ABC, abstractmethod


class MickeyPlugin(ABC):
    """Base class for all MICKEY plugins."""

    name: str = "unnamed"
    description: str = ""
    version: str = "0.1"

    @abstractmethod
    def on_load(self):
        """Called when plugin is loaded. Set up any state here."""
        pass

    @abstractmethod
    def get_commands(self) -> list[dict]:
        """Return list of commands this plugin provides.
        Each: {"name": str, "description": str, "params": dict}
        """
        return []

    @abstractmethod
    def handle_command(self, command: str, params: dict) -> str:
        """Handle a command. Return result string."""
        pass

    def on_unload(self):
        """Called when plugin is unloaded. Clean up here."""
        pass


class PluginRegistry:
    """Discovers, loads, and manages plugins."""

    def __init__(self):
        self.plugins: dict[str, MickeyPlugin] = {}
        self.commands: dict[str, MickeyPlugin] = {}  # command_name -> plugin

    def discover(self):
        """Auto-discover plugins in the plugins directory."""
        plugins_dir = os.path.dirname(__file__)
        for filename in os.listdir(plugins_dir):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue
            module_name = filename[:-3]
            try:
                module = importlib.import_module(f"plugins.{module_name}")
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, MickeyPlugin) and obj is not MickeyPlugin:
                        self._load_plugin(obj)
            except Exception as e:
                print(f"  ⚠ Failed to load plugin {module_name}: {e}")

    def _load_plugin(self, plugin_class):
        plugin = plugin_class()
        plugin.on_load()
        self.plugins[plugin.name] = plugin

        # Register commands
        for cmd in plugin.get_commands():
            cmd_name = cmd["name"]
            self.commands[cmd_name] = plugin
            print(f"  ✓ Plugin '{plugin.name}' registered command: {cmd_name}")

    def handle(self, command: str, params: dict) -> str | None:
        """Route command to the right plugin. Returns None if no plugin handles it."""
        plugin = self.commands.get(command)
        if plugin:
            return plugin.handle_command(command, params)
        return None

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "commands": [c["name"] for c in p.get_commands()],
            }
            for p in self.plugins.values()
        ]

    def list_all_commands(self) -> list[dict]:
        """List all commands from all plugins."""
        commands = []
        for plugin in self.plugins.values():
            for cmd in plugin.get_commands():
                cmd["plugin"] = plugin.name
                commands.append(cmd)
        return commands

    def unload_all(self):
        for plugin in self.plugins.values():
            plugin.on_unload()
        self.plugins.clear()
        self.commands.clear()


# Global registry
registry = PluginRegistry()
