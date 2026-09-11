"""Public API for the service package."""

from .service import CategoryComparator
from .utils import add_namespace_prefix

__all__ = [
    "CategoryComparator",
    "add_namespace_prefix",
]
