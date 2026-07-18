"""Public API for the service package."""

from .db_pool import db_manager
from .service import CategoryComparator
from .utils import add_namespace_prefix

__all__ = [
    "db_manager",
    "CategoryComparator",
    "add_namespace_prefix",
]
