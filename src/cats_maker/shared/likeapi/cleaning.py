#!/usr/bin/python3


""" """

from __future__ import annotations

import re


def cleaning(text: str, msg: str) -> tuple:
    old_text = text
    text = text.replace("\n\n*", "\n*").replace("\n\n#", "\n#").replace("\n# \n", "\n#")
    text = text.replace("\n#\n", "\n#").replace("\n*\n", "\n*").replace("\n* \n", "\n*").replace("\n*==", "\n==")
    # ---cleaning for subsections -----
    text = re.sub(r"(\< *\/ *br *\>|\< *br *\\ *\>|\< *br *\. *\>)", "</br>", text)

    text = text.replace("], ", "]، ")
    text = text.replace(" ،", "، ")
    text = text.replace('== "', "== ").replace('" ==', " ==")
    text = text.replace("== '''", "== ").replace("''' == ", " ==")
    text = text.replace("=='''", "==").replace("'''== ", "==")

    # ---cleaning for links and wiki syntaxes-----
    text = text.replace("[[ ", "[[").replace(" ]]", "]]")  # .replace(' }}','}}').replace('{{ ','{{')
    text = text.replace("==  ", "== ").replace("==  ", "== ").replace("  ==", " ==").replace("  ==", " ==")
    text = text.replace("\n ]]\n", "]]\n").replace("\n]]\n", "]]\n")

    text = re.sub(r"\=\s*مراجع\s*\=", "= مراجع =", text)
    text = re.sub(r"\=\s*المراجع\s*\=", "= المراجع =", text)
    text = re.sub(r"\=\s*Usage\s*\=", "= الاستخدام =", text)
    text = re.sub(r"\=\s*See also\s*\=", "= طالع أيضاً =", text)
    text = re.sub(r"\=\s*Examples\s*\=", "= أمثلة =", text)
    text = re.sub(r"\=\s*Parameters\s*\=", "= المعلمات =", text)

    # text_test = re.sub(r"\n\=+ (مراجع|مصادر|المراجع) \=+\n", "", text)
    text = text.replace("==  ", "== ").replace("  ==", " ==").replace("==  ", "== ").replace("  ==", " ==")
    text = text.replace("==<", "==\n<").replace(">==", ">\n==")  # وأكردأنی خطأی كد
    # Files

    text = re.sub(r"\[\[ *[Ii]mage *: *", "[[ملف:", text)
    text = re.sub(r"\[\[ *[Ff]ile *: *", "[[ملف:", text)

    # ---cleaning for images-----
    text = re.sub(r"\{\{ *(?:[Tt]emplate|قالب):", "{{", text)
    text = re.sub(r"\[\[ *(?:[Ii]mage|[Ff]ile|صورة:|صورة):", "[[ملف:", text)
    text = text.replace("صورة::", "ملف:").replace("صورة:", "ملف:").replace("ملف:صورة::", "ملف:")
    text = re.sub(r"{{(?:[Cc]ommons?) ?\|", "{{كومنز|", text)
    text = re.sub(r"\[\[ *(https?\:\/\/.*?) *\]\]", r"[\1]", text)
    text = re.sub(r"\[\[ *(\/\/.*?) *\]\]", r"[\1]", text)
    text = re.sub(r"(https?:\/?\/?){2,}", r"\1", text)

    text = re.sub(r"\[\[\|", "[[", text)
    text = re.sub(r"\[\[([^\]]+)\{\{\!\}\}([^\]]+)\]\]", r"[[\1|\2]]", text)
    text = re.sub(r"\[{2}([^\|]+)\|\1\]{2}", r"[[\1]]", text)

    text = (
        text.replace("\n\n{{تحديد}}\n\n", "\n{{تحديد}}\n")
        .replace(" [[ملف:]] ", "")
        .replace("<!---->\n", "")
        .replace("<!---->", "")
    )
    text = text.replace("\\{\\{Infobox person\n\\|", "{{صندوق معلومات شخص\n|")

    text = text.replace("==<", "==\n<").replace(">==", ">\n==")
    # logger.info(msg)
    return text.strip(), msg


__all__ = [
    "cleaning",
]
