"""
Unit tests for src/core/client_wiki/factory.py module.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.client_wiki.factory import load_login_bot, load_main_api
