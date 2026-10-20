"""Public API for the service package."""

from __future__ import annotations

from .service import CategoryComparator
from .utils import add_namespace_prefix

__all__ = [
    "CategoryComparator",
    "add_namespace_prefix",
]
