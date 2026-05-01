""" """

import sys
import logging
import os

import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import mwclient


try:
    load_dotenv()
except Exception:
    pass

sys.path.append(Path(__file__).parent.parent)

from src.core.new_api import AuthProvider
from src.core.wiki_client.client import WikiLoginClient
from src.core.wiki_client.client_1 import WikiLoginClient as WikiLoginClient_1

logger = logging.getLogger(__name__)

logger.setLevel("DEBUG")

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})

# ==========================

_site = mwclient.Site(
    "ar.wikipedia.org",
)

cookies_path = Path("C:/Windows/Temp/cookies/wikipedia_ar_mr.ibrahembot.json")
cookies_data = {}
if cookies_path.exists():
    cookies_data = json.load(cookies_path.open("r", encoding="utf-8"))
    print(f"load cookies data: {len(cookies_data)}")

_site.connection.cookies = requests.sessions.RequestsCookieJar()

_site.login(
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
    cookies=cookies_data
)

print(f"{_site.logged_in=}")
if _site.logged_in:
    print(f"Save cookies to {cookies_path}")
    # save cookies to cookies_path
    with open(cookies_path, "w", encoding="utf-8") as f:
        json.dump(_site.connection.cookies.get_dict(), f)
