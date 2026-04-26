#!/usr/bin/python3
"""
Output JSON handling

This module provides functions for handling JSON output from API calls.
"""

import logging
import os
import time

logger = logging.getLogger(__name__)

file_name = os.path.basename(__file__)


def outbot_json_bot(err):
    text = str(err)

    err_code = err.get("code", "")
    err_info = err.get("info", "")

    extradata = err.get("extradata", [""])
    messages = err.get("messages", [{}])[0]
    msg_name = messages.get("name", "")

    msg_html = ""
    if isinstance(messages.get("html", {}), dict):
        msg_html = messages.get("html", {}).get("*", "")

    err_wait = "احترازًا من الإساء، يُحظر إجراء هذا الفعل مرات كثيرة في فترةٍ زمنية قصيرة، ولقد تجاوزت هذا الحد"

    if err_code == "origin-not-empty":
        logger.debug(f"<<lightred>> msg_html: {msg_html} ")
        logger.debug(f"<<lightred>> err_info: {err_info} ")
        return err_code

    if err_code == "missingparam":
        logger.debug(f"<<lightred>> err_info: {err_info} ")
        return "warn"

    elif err_code in ["modification-failed", "failed-modify"]:
        logger.debug(f"<<lightred>> err_info: {err_info} ")

        if msg_name == "wikibase-api-failed-modify":
            logger.debug(f"<<lightred>>err msg_name: {msg_name}")
            logger.debug(f"<<lightred>>\t: {extradata}")
            return msg_name

        if msg_name == "wikibase-validator-label-equals-description":
            logger.debug(f"<<lightred>>err msg_name: {msg_name}")
            logger.debug(f"<<lightred>>\t: {msg_html}")
            return msg_name

        if msg_name == "wikibase-validator-label-with-description-conflict":
            logger.debug("<<lightred>>same description:")

            lab, code, q = messages.get("parameters", [])

            logger.debug(f"<<lightred>>\t: lab:{lab}, code:{code}, q:{q}")

            return "same description"
        return "warn"
    elif err_code == "unresolved-redirect":
        logger.debug("<<lightred>> - unresolved-redirect")
        return "unresolved-redirect"

    elif err_code == "failed-save":
        if err_wait in text:
            logger.debug(f'<<lightred>> {file_name} - "{err_wait} time.sleep(5) " ')
            time.sleep(5)
            return "reagain"

        logger.debug(f'<<lightred>> - "{err_code}" ')
        logger.debug(text)
        return False
    elif err_code == "no-external-page":
        logger.debug(f'<<lightred>> - "{err_code}" ')
        logger.debug(text)
        return False

    else:
        if "wikibase-api-invalid-json" in text:
            logger.debug('<<lightred>> - "wikibase-api-invalid-json" ')
            logger.debug(text)
            return "wikibase-api-invalid-json"

        elif "Could not find an Item containing a sitelink to the provided site and page name" in text:
            logger.debug(
                "<<lightred>> ** error. : Could not find an Item containing a sitelink to the provided site and page name "
            )
            return "Could not find an Item containing a sitelink to the provided site and page name"
        else:
            return err_code


def outbot_json(js_text, fi="", line=""):
    success = js_text.get("success", 0)

    if success == 1:
        logger.warning(f"<<lightgreen>> ** true. {fi}")

        return True

    err = js_text.get("error", {})

    if not err:
        return "warn"

    if fi:
        logger.debug(f"<<lightred>> ** error. : {fi} ")

    if line:
        logger.debug(f"<<lightpurple>> ** line. : {line} ")

    return outbot_json_bot(err)
