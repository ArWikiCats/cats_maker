"""
from .app_initializer import AppInitializer

AppInitializer.setup()
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class AppInitializer:
    """"""

    _initialized: bool = False

    @classmethod
    def setup(cls) -> None:
        """ """
        if cls._initialized:
            return

        cls._setup_cats_maker()
        logger.info("App initialized")
        cls._initialized = True

    @staticmethod
    def _setup_cats_maker() -> None:
        """
        Check for cats_maker availability and dynamically append its path if configured.
        """
        try:
            from cats_maker import process_catagories  # noqa: F401
        except ImportError:
            logger.warning("cats_maker library not found")
            msg = """
            Please install cats_maker from https://github.com/ArWikiCats/cats_maker
                - `pip install git+https://github.com/ArWikiCats/cats_maker.git -U`
            or clone cats_maker into your workspace and inside `cats_maker` folder run:
                - `pip install -e .`
            """
            logger.error(msg)
