def format_sitelinks(sitelinks: dict[str, dict]) -> dict[str, str]:
    """
    Data Example:
    {
        "arwiki": { "site": "arwiki", "title": "ويكيبيديا:مشروع ويكي بيانات", "badges": [] },
        "dawiki": { "site": "dawiki", "title": "Wikipedia:WikiProjekt Wikidata", "badges": [] }
    }
    """
    return {x["site"]: x["title"] for d, x in sitelinks.items()}


def format_aliases(aliases: dict[str, list[dict[str, str]]]) -> dict[str, list[str]]:
    """
    Data Example:
    {
        "pl": [ { "language": "pl", "value": "Wikiprojekt:Wikidane" } ],
        "uk": [ { "language": "uk", "value": "Проект:Вікідані" }, { "language": "uk", "value": "..." } ]
    }
    """
    return {code: [x["value"] for x in tab] for code, tab in aliases.items()}


def format_labels_descriptions(labels: dict[str, dict]) -> dict[str, str]:
    """
    Data Example:
    {
        "lv": { "language": "lv", "value": "Vikiprojekts:Vikidati" },
        "de": { "language": "de", "value": "Wikipedia:WikiProjekt Wikidata in Wikipedia" }
    }
    """
    return {x["language"]: x["value"] for _, x in labels.items()}


__all__ = [
    "format_sitelinks",
    "format_aliases",
    "format_labels_descriptions",
]
