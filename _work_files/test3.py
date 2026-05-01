""" """

from http.cookiejar import MozillaCookieJar
import sys
import logging
import os
from pathlib import Path

import requests
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

# ==========================

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})

cookies_jar_path = "C:/Windows/Temp/cookies/wikipedia_ar_mr.ibrahembot.mozilla"

session.cookies = MozillaCookieJar(cookies_jar_path)

auth = AuthProvider(
    lang="ar",
    family="wikipedia",
    session=session,
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)

auth.login()

session.cookies.save(ignore_discard=True, ignore_expires=True)

# ==========================


_site = mwclient.Site(
    "ar.wikipedia.org",
)

cookies_path = "C:/Windows/Temp/cookies/wikipedia_ar_mr.ibrahembot.json"

_site.connection.cookies = requests.sessions.RequestsCookieJar()

_site.login(
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
    # cookies=auth.cookies
)

print(f"{_site.logged_in=}")

# ==========================

client = WikiLoginClient_1(
    lang="ar",
    family="wikipedia",
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)


client.login()

# ==========================
