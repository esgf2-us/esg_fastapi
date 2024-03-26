import pkgutil
from importlib import import_module

discovered = []
for submodule in pkgutil.iter_modules(__path__):
    if submodule.name.lstrip("v").isdigit():
        discovered.append(import_module("." + submodule.name, __package__))
