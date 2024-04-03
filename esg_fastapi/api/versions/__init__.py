"""Module for discovering and importing all versioned API submodules.

This module provides a mechanism for discovering and importing all versioned API submodules within the current package. It uses the `pkgutil` and `importlib` modules to iterate through all the submodules in the package and import those that have a version number in their name.

The discovered submodules are then added to the main application using the `app.mount()` method. This allows developers to easily extend and customize the functionality of the main application by adding new submodules that provide additional API endpoints.
"""

import pkgutil
from importlib import import_module

discovered = []
for submodule in pkgutil.iter_modules(__path__):
    if submodule.name.lstrip("v").isdigit():
        discovered.append(import_module("." + submodule.name, __package__))
