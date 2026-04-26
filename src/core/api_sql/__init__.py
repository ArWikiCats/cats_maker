"""Public API for the service package."""

from .service import CategoryComparator
from .utils import add_namespace_prefix
from .db_pool import db_manager

__all__ = [
    "db_manager",
    "CategoryComparator",
    "add_namespace_prefix",
]
