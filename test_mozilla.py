""" """

import sys
import logging
import os
from pathlib import Path

import json
import requests
from http.cookiejar import MozillaCookieJar
from requests.cookies import cookiejar_from_dict

from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass

sys.path.insert(0, Path(__file__).parent.parent.parent)

from src.core.new_api import AuthProvider

logger = logging.getLogger(__name__)

logger.setLevel("DEBUG")

# ==========================

session = requests.Session()

session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"})


cookies_file = Path("C:/Windows/Temp/cookies/wikipedia_ar_mr.ibrahembot.mozilla")

cookie_jar = MozillaCookieJar(cookies_file)
cookie_jar_loaded = False

if os.path.exists(cookies_file):
    logger.debug("Load cookies from file, including session cookies")
    try:
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        cookie_jar_loaded = True
        logger.debug("We have %d cookies" % len(cookie_jar))

    except Exception as e:
        logger.exception("Error loading cookies from file")

# Bind cookies once; subsequent calls for the same user reuse the same jar.
if session.cookies is not cookie_jar:
    session.cookies = cookie_jar

auth = AuthProvider(
    lang="ar",
    family="wikipedia",
    session=session,
    username=os.getenv("WIKIPEDIA_BOT_USERNAME"),
    password=os.getenv("WIKIPEDIA_BOT_PASSWORD"),
)
if not cookie_jar_loaded:
    auth.login()

if auth.loged_in():
    print(f"Save cookies to {cookies_path}")
    cookie_jar.save(ignore_discard=True, ignore_expires=True)
