#!/usr/bin/python3
""" """

from .to_wd import Log_to_wikidata, add_labels
from .wd_api_bot import Get_P373_API, Get_Sitelinks_from_qid, Get_Sitelinks_From_wikidata

__all__ = [
    "Get_P373_API",
    "Get_Sitelinks_From_wikidata",
    "Get_Sitelinks_from_qid",
    "Log_to_wikidata",
    "add_labels",
]
