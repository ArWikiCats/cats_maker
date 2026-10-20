from __future__ import annotations

from .dontadd import dont_add_pages_loader
from .rename_temps import rename_temps_loader
from .temps_params import template_params_loader

__all__ = [
    "rename_temps_loader",
    "template_params_loader",
    "dont_add_pages_loader",
]
