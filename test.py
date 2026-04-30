""" """

import logging
import os

import requests
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass

from src.core.new_api import AuthProvider

logger = logging.getLogger(__name__)

logger.setLevel("DEBUG")

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})

auth = AuthProvider(
    "ar",
    "wikipedia",
    session,
    os.getenv("WIKIPEDIA_BOT_USERNAME"),
    os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)

auth.log_in()
