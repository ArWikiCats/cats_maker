"""
Centralized configuration module for the project.

This module provides a central place for all configuration settings,
making it easier to manage and modify settings across the codebase.
"""

from .settings import (
    BotConfig,
    CategoryConfig,
    DatabaseConfig,
    DebugConfig,
    QueryConfig,
    Settings,
    SiteConfig,
    WikidataConfig,
    WikipediaConfig,
    WikiSiteInfo,
    settings,
)

__all__ = [
    "WikiSiteInfo",
    "Settings",
    "WikipediaConfig",
    "WikidataConfig",
    "DatabaseConfig",
    "DebugConfig",
    "BotConfig",
    "CategoryConfig",
    "QueryConfig",
    "SiteConfig",
    "settings",
]
