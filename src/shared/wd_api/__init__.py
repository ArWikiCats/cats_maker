#!/usr/bin/python3
""" """

from .to_wd import add_labels, log_to_wikidata, log_to_wikidata_qid
from .wd_api_bot import get_p373_api, get_sitelinks_from_qid, get_sitelinks_from_wikidata

__all__ = [
    "get_p373_api",
    "get_sitelinks_from_wikidata",
    "get_sitelinks_from_qid",
    "log_to_wikidata",
    "log_to_wikidata_qid",
    "add_labels",
]
