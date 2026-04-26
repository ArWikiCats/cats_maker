#!/usr/bin/python3
""" """
import logging

from ..config import settings
from ..utils.skip_cats import global_False_entemps as NO_Templates

logger = logging.getLogger(__name__)

# Define a blacklist for templates and names
templateblacklist = NO_Templates

nameblcklist = [
    "Current events",  # حدث جاري
    "Articles with",
    "Tracking",
    "articles",
    "Surnames",
    "Loanword",
    "Words and phrases",
    "Given names",
    "Human names",
    "stubs",  # بذرة
    "Nicknames",
]

if settings.category.stubs:
    nameblcklist.remove("stubs")
