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
from src.core.wiki_client import WikiLoginClient

logger = logging.getLogger(__name__)

logger.setLevel("DEBUG")

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})

auth = AuthProvider(
    lang="ar",
    family="wikipedia",
    session=session,
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)

auth.login()

client = WikiLoginClient(
    lang="ar",
    family="wikipedia",
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)


client.login()
