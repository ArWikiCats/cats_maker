"""
Wikidata functions
"""

from __future__ import annotations

import logging
from typing import Any

from ...newapi import WikiLoginClient
from ..utils import (
    format_aliases,
    format_labels_descriptions,
    format_sitelinks,
)

logger = logging.getLogger(__name__)


class WDFunctions:
    def __init__(self, login_bot: WikiLoginClient) -> None:
        self.login_bot = login_bot

    def get_item_descriptions_or_labels(
        self,
        qid: str,
        ty: str = "descriptions or labels",
    ) -> dict[str, str]:
        """Retrieve item descriptions or labels from a given entity ID.

        This function queries an API to obtain either descriptions or labels for
        a specified entity ID. It constructs a request based on the provided
        entity ID and the type of information requested. If the type is not
        explicitly set to "descriptions" or "labels", it defaults to
        "descriptions". The function processes the API response and returns a
        dictionary mapping languages to their respective descriptions or labels.
        If the API call is unsuccessful or returns no valid entities, an empty
        dictionary is returned.

        Args:
            qid (str): The entity ID for which descriptions or labels are to be retrieved.
            ty (str): The type of information to retrieve, either "descriptions" or "labels".
                Defaults to
                "descriptions or labels".

        Returns:
            dict: A dictionary where keys are language codes and values are the
                corresponding descriptions or labels.
        """

        params: dict[str, Any] = {"action": "wbgetentities", "ids": qid}

        if ty == "descriptions or labels":
            ty = "descriptions"

        if ty in ["descriptions", "labels"]:
            params["props"] = ty

        def _load_data(body):
            return body.get("entities") or {}

        json1 = self.login_bot.post_continue_dict(
            params=params,
            action="wbgetentities",
            _load_data=_load_data,
        )
        if not json1:
            return {}

        success = json1.get("success", False)
        entities = json1.get("entities", {})

        if not success or success != 1:
            return {}

        if "-1" in entities:
            return {}

        for qid in entities:
            qprop = entities[qid].get(ty, {})
            return format_labels_descriptions(qprop)

        return {}

    def get_property_api_data(
        self,
        qid: str = "",
        pid: str = "",
        title: str = "",
        sites: str = "",
    ) -> list[Any]:
        # url = 'https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=' + q + '&property=' + p + '&format=json'

        params: dict[str, Any] = {
            "action": "wbgetclaims",
            "entity": qid,
            "property": pid,
        }

        if qid == "" and title and sites:
            del params["entity"]
            params["sites"] = sites
            params["titles"] = title

        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        listo: list = []

        if not json1:
            return listo

        claims_p = json1.get("claims", {}).get(pid, {})

        for claims in claims_p:
            datavalue = claims.get("mainsnak", {}).get("datavalue", {})
            # method = datavalue.get("type", False)
            value = datavalue.get("value", {})

            listo.append(value)

        return listo

    def get_infos_wikidata(self, params: dict[str, Any]) -> dict[str, Any]:

        main_table = {}

        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        if not json1:
            return main_table

        success = json1.get("success", False)
        if not success or success != 1:
            return main_table

        entities = json1.get("entities", {})

        if "-1" in entities:
            return main_table

        props = params["props"].split("|")

        for q, qprop in entities.items():
            result_data = {
                "labels": format_labels_descriptions(qprop.get("labels", {})),
                "descriptions": format_labels_descriptions(qprop.get("descriptions", {})),
                "sitelinks": format_sitelinks(qprop.get("sitelinks", {})),
                "aliases": format_aliases(qprop.get("aliases", {})),
                "q": q,
            }

            for x in props:
                if x in qprop and x not in result_data:
                    result_data[x] = qprop[x]

            main_table[q] = result_data

        return main_table

    def get_from_wikidata(
        self,
        site: str,
        titles: list[str],
        get_site: str = "",
        label_or_desc_lang: str = "",
        add_props: list | tuple | None = None,
    ) -> dict[str, Any]:

        sitewiki = site
        if site.find("wiki") == -1:
            sitewiki = f"{site}wiki"

        logger.info(f"{len(titles)=}")

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "props": "sitelinks",
            # "props": "sitelinks|descriptions|labels|aliases",
            "sites": sitewiki,
            "titles": "",
            # "normalize": 1,
            # "tlnamespace": "10",
            # "tllimit": "max",
            # "tltemplates": "Template:Category redirect",
        }

        props = ["sitelinks", "labels"]

        if isinstance(add_props, list):
            valid = ["sitelinks", "labels", "descriptions", "aliases"]

            props.extend([x for x in add_props if x in valid])

        props = list(set(props))

        params["props"] = "|".join(props)

        result_data = {}

        groups = [titles[i : i + 50] for i in range(0, len(titles), 50)]

        for group in groups:  # tqdm(groups, desc=f"split titles({len(titles)}) by 50 title to {len(groups)} group."):
            params["titles"] = "|".join(group)

            table2 = self.get_infos_wikidata(params)

            result_data.update(table2)

        if get_site:
            for q, x in result_data.copy().items():
                result_data[q]["sitelinks"] = {
                    sitewiki: x.get("sitelinks", {}).get(sitewiki, ""),
                    get_site: x.get("sitelinks", {}).get(get_site, ""),
                }

        if label_or_desc_lang:
            for ty in ["labels", "descriptions", "aliases"]:
                for q, x in result_data.copy().items():
                    default = [] if ty == "aliases" else ""
                    slabel = x.get(ty, {}).get(label_or_desc_lang, default)
                    result_data[q][ty] = {label_or_desc_lang: slabel}

        return result_data

    def get_wikidata_sitelinks(
        self,
        site: str,
        title: str,
        props: str = "",
        add_props: list | tuple | None = None,
    ) -> dict[str, Any]:

        sitewiki = site
        if site.find("wiki") == -1:
            sitewiki = f"{site}wiki"

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "props": "sitelinks",
            # "props": "sitelinks|templates",
            "sites": sitewiki,
            "titles": title,
            "normalize": 1,
            # "tlnamespace": "10",
            # "tllimit": "max",
            # "tltemplates": "Template:Category redirect",
        }

        if props:
            params["props"] = props

        if isinstance(add_props, list | tuple):
            for x in add_props:
                if x not in params["props"]:
                    params["props"] += f"|{x}"

        result_data = self.get_infos_wikidata(params)

        q_data = list(result_data.values())

        if q_data:
            return q_data[0]

        return {}

    def get_sitelinks_from_wikidata(
        self,
        site: str,
        title: str,
        ssite: str,
    ) -> str:

        result_data = self.get_wikidata_sitelinks(
            site=site,
            title=title,
        )

        ssite2 = ssite
        if not ssite.endswith("wiki"):
            ssite2 += "wiki"

        sitelinks = result_data.get("sitelinks", {})
        result = sitelinks.get(ssite) or sitelinks.get(ssite2) or ""
        return result

    def get_wd_sitelinks_for_ids(
        self,
        ids: str,
        props: str = "",
        add_props: list | tuple | None = None,
    ) -> dict[str, Any]:

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "props": "sitelinks",
            # "props": "sitelinks|templates",
            "normalize": 1,
            "ids": ids,
            # "tlnamespace": "10",
            # "tllimit": "max",
            # "tltemplates": "Template:Category redirect",
        }

        if props:
            params["props"] = props

        if isinstance(add_props, list | tuple):
            for x in add_props:
                if x not in params["props"]:
                    params["props"] += f"|{x}"

        result_data = self.get_infos_wikidata(params)

        q_data = list(result_data.values())

        if q_data:
            return q_data[0]

        return {}

    def get_items_api_from_qids(
        self,
        qids: list[str],
        props: str = "",
        sitefilter: str = "",
    ) -> dict[str, Any]:

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "ids": "|".join(qids),
        }

        if props:
            params["props"] = props

        if sitefilter:
            params["sitefilter"] = sitefilter

        logger.info(f"<<purple>> get_items_api_from_qids: {len(qids)=}")

        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        if not json1:
            return {}

        success = json1.get("success", False)

        if not success or success != 1:
            return {}

        entities = json1.get("entities", {})

        tabx = {}

        for q_id, ppe in entities.items():
            result_data = {
                "sitelinks": {},
                "aliases": {},
                "labels": {},
                "descriptions": {},
                "claims": {},
                "q": q_id,
            }

            result_data["labels"] = format_labels_descriptions(ppe.get("labels", {}))
            result_data["descriptions"] = format_labels_descriptions(ppe.get("descriptions", {}))
            result_data["sitelinks"] = format_sitelinks(ppe.get("sitelinks", {}))
            result_data["aliases"] = ppe.get("aliases", {})
            result_data["claims"] = ppe.get("claims", {})

            tabx[q_id] = result_data

        return tabx

    def get_p373_api(self, qid, title: str = "", sites: str = "") -> str:
        """Retrieve the P373 value from the Wikidata API.

        This function constructs a request to the Wikidata API to fetch entities
        based on the provided identifier (qid). It retrieves the sitelinks and
        claims associated with the entity and specifically looks for the P373
        property, which is used to link to Wikimedia Commons categories. If the
        identifier is not provided, it can use titles and sites to fetch
        relevant data.

        Args:
            qid (str): The identifier for the Wikidata entity.
            titles (str?): Titles to search for if no identifier is provided.
            sites (str?): Sites to filter the search if no identifier is provided.

        Returns:
            str: The P373 value (Wikimedia Commons category title) if found,
                otherwise an empty string.
        """

        P = "P373"

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "props": "sitelinks|claims",
            "ids": qid,
        }

        if qid == "" and title and sites:
            del params["ids"]
            # params["ids"] = ids
            params["sites"] = sites
            params["titles"] = title

        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        mainvalue = ""

        if not json1:
            return ""

        entities = json1.get("entities", {})
        for jj in entities:
            commonswiki = entities[jj].get("sitelinks", {}).get("commonswiki", {}).get("title", "")
            if commonswiki:
                mainvalue = commonswiki.replace("Category:", "")
                return mainvalue

            claims = entities[jj].get("claims", {}).get(P, {})
            for claim in claims:
                datavalue = claim.get("mainsnak", {}).get("datavalue", {})
                _type = datavalue.get("type", False)
                value = datavalue.get("value", "")
                if _type == "string" and value:
                    logger.info(value)
                    return value

        return mainvalue

    def get_item_api(self, qid: str, props: str = "") -> dict[str, Any]:

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "ids": qid,
        }

        if props:
            params["props"] = props

        result_data = {
            "sitelinks": {},
            "aliases": {},
            "labels": {},
            "descriptions": {},
            "claims": {},
            "q": "",
        }
        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        if not json1:
            return result_data

        success = json1.get("success", False)
        if not success or success != 1:
            return result_data

        entities = json1.get("entities", {})

        if "-1" in entities:
            return result_data

        for q_id, ppe in entities.items():
            result_data["q"] = q_id
            # ---#aliases
            result_data["labels"] = format_labels_descriptions(ppe.get("labels", {}))
            result_data["descriptions"] = format_labels_descriptions(ppe.get("descriptions", {}))
            result_data["sitelinks"] = format_sitelinks(ppe.get("sitelinks", {}))
            result_data["aliases"] = ppe.get("aliases", {})
            result_data["claims"] = ppe.get("claims", {})

        return result_data

    def get_item_api_by_title_and_site(
        self,
        sites: str = "",
        title: str = "",
        props: str = "",
    ) -> dict[str, Any]:

        if not sites or not title:
            logger.error("sites or title is empty")
            return {}

        params: dict[str, Any] = {
            "action": "wbgetentities",
            "titles": title,
            "sites": sites,
            "normalize": 1,
        }

        if props:
            params["props"] = props

        site_code = sites.removesuffix("wiki")
        site_code = f"{site_code}wiki"

        json1 = self.login_bot.client_request_safe(
            params=params,
            method="GET",
        )

        result_data = {
            "sitelinks": {},
            "aliases": {},
            "labels": {},
            "descriptions": {},
            "claims": {},
            "q": "",
        }

        if not json1:
            return result_data

        success = json1.get("success", False)
        if not success or success != 1:
            return result_data

        entities = json1.get("entities", {})

        if "-1" in entities:
            return result_data

        for q_id, ppe in entities.items():
            result_data["q"] = q_id
            # ---#aliases
            result_data["labels"] = format_labels_descriptions(ppe.get("labels", {}))
            result_data["descriptions"] = format_labels_descriptions(ppe.get("descriptions", {}))
            result_data["sitelinks"] = format_sitelinks(ppe.get("sitelinks", {}))
            result_data["aliases"] = ppe.get("aliases", {})
            result_data["claims"] = ppe.get("claims", {})

        return result_data


__all__ = [
    "WDFunctions",
]
