#!/usr/bin/python3
"""
POST bot - Claims functionality

This module provides functions for working with claims in Wikidata.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from ....newapi import ApiResult
from ..wd_requests_handler import WikidataRequestHandler
from .handle_response import ResponseHandler

logger = logging.getLogger(__name__)


class WdClaims(ResponseHandler):
    def __init__(self, wd_handler: WikidataRequestHandler) -> None:
        self.execute_wd_api_call = wd_handler.execute_wd_api_call

    def add_quall(
        self,
        claim_id: str,
        quall_prop: str,
        valueline: dict[str, Any],
        hashx: str = "",
    ) -> ApiResult:
        """Add a qualifier to a claim.

        This function adds a specified qualifier to a given claim identified by
        the Claimid. It first checks for any lag conditions and then prepares
        the necessary parameters for the action. If the numeric ID in the
        valueline matches the ID extracted from the Claimid, it will not proceed
        with adding the qualifier.

        Args:
            Claimid (str): The identifier of the claim to which the qualifier is added.
            quall_prop (str): The property name of the qualifier being added.
            valueline (dict): A dictionary containing the value details for the qualifier.
            hash (str?): An optional hash value for the qualifier. Defaults to an empty string.

        Returns:
            dict or bool: Returns a dictionary with the result of the operation if
                successful,
                or False if the operation fails.
        """
        valueline2 = json.JSONEncoder().encode(valueline)
        logger.info(f'add_quall Claimid: "{claim_id}" ,{valueline2}: ')

        id2 = claim_id.split("$")[0].replace("Q", "")
        numeric = valueline.get("numeric-id", False)
        if numeric and numeric == id2:
            logger.info(f"<<lightred>> add_quall {quall_prop}: q:Q{id2} == numeric:Q{numeric}.")
            return ApiResult.fail(code="numeric_id")

        params: dict[str, Any] = {
            "action": "wbsetqualifier",
            "claim": claim_id,
            "snaktype": "value",
            "property": quall_prop,
            "value": valueline2,
        }

        if hashx:
            params["snakhash"] = hashx

        nhh = numeric or valueline.get("time", valueline.get("amount", ""))
        out = f'Add qualifier "{quall_prop}":"{nhh}" to Claimid {claim_id}. '

        if hashx:
            out = f'change qualifier "{quall_prop}":"{nhh}" in Claimid {claim_id}. '

        r4 = self.execute_wd_api_call(params)

        return self.handle_response(r4, out)

    def claim_api(
        self,
        entity_id: str,
        proprty: str,
        numeric: int,
        qualifiers: list | None = None,
    ) -> ApiResult:

        if qualifiers is None:
            qualifiers = []

        out = f"{entity_id}: {proprty}:Q{numeric}."

        if entity_id == "" or proprty == "" or not numeric:
            logger.info(f"one param empty {entity_id=}, {proprty=}, {numeric=}")
            return ApiResult.fail(code="empty_parameter")

        numeric = int(numeric)

        qq = re.sub(r"Q", "", entity_id)
        if int(qq) == numeric:
            logger.info(out)
            logger.info(f"<<lightred>>  {proprty}:  id:Q{entity_id} == numeric:Q{numeric}.")
            return ApiResult.fail(code="numeric_id")

        params: dict[str, Any] = {
            "action": "wbcreateclaim",
            "entity": entity_id,
            "snaktype": "value",
            "property": proprty,
            "value": '{"entity-type":"item","numeric-id":' + str(numeric) + "}",
        }

        r4 = self.execute_wd_api_call(params)

        result = self.handle_response(r4, out)

        if result.is_ok:
            claim_id = r4.get("claim", {}).get("id", "")
            if qualifiers and claim_id:
                self._set_quall2(claim_id, qualifiers)
            return result

        return result

    def claim_api_time(
        self,
        q: str,
        proprty: str,
        precision: int = 9,
        year: str = "",
        strtime: str = "",
    ) -> ApiResult:

        out = f"{q}: {proprty}:{year}."

        if precision == 9 and strtime == "":
            strtime = f"+{year}-00-00T00:00:00Z"

        time_data = {
            "after": 0,
            "before": 0,
            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            "precision": precision,
            "time": strtime,
            "timezone": 0,
        }
        if not strtime:
            logger.info(f'strtime is "{strtime}"')

        params: dict[str, Any] = {
            "action": "wbcreateclaim",
            "entity": q,
            "snaktype": "value",
            "property": proprty,
            "value": json.JSONEncoder().encode(time_data),
        }
        r4 = self.execute_wd_api_call(params)

        return self.handle_response(r4, out)

    def _set_quall2(self, claim_id: str, qualifiers: list) -> None:

        logger.info(f'<<lightyellow>> Claimid: "{claim_id}"')

        for qua in qualifiers:
            quall_prop = qua["property"]
            value = qua["value"]
            ty_pe = qua["type"]
            valueline = {}
            if ty_pe == "time":  # , 'time': '+2003-04-27T00:00:00Z'
                if value.get("time"):
                    valueline = value
                else:
                    valueline = {
                        "after": 0,
                        "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                        "time": "",
                        "timezone": 0,
                        "before": 0,
                        "precision": 11,
                    }
                    valueline["time"] = value  # '+2003-04-27T00:00:00Z'
            elif ty_pe == "quantity":
                # valueline["property"] = quall_prop
                # valueline["type"] = "quantity"
                # valueline["value"] = {}
                # valueline = value
                # if type(value) != dict:
                valueline = {"amount": "+" + str(value), "unit": "1"}
                # else:
                #  valueline["value"] = value
            else:
                entitytype = "item"
                quat = ""
                if value.get("numeric-id", False):
                    valueline = value
                    quat = value.get("numeric-id", "")
                else:
                    quat = value
                    qua_id = re.sub(r"Q", "", quat)
                    if quat != re.sub(r"P", "", quat):
                        entitytype = "property"
                        qua_id = re.sub(r"P", "", quat)
                    valueline = {"entity-type": entitytype, "numeric-id": qua_id}

            self.add_quall(claim_id, quall_prop, valueline)


__all__ = [
    "WdClaims",
]
