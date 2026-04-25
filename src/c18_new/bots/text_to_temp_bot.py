#!/usr/bin/python3
"""

from ..bots import text_to_temp_bot

text = text_to_temp_bot.add_text_to_template(text, Final_Categories)
added = text_to_temp_bot.find_doc_and_add(Final_Categories, title)


if page has ({{#استدعاء:شريط|شريط) replace ({{توثيق}}) by ({{توثيق شريط}})

"""
import logging
import re

import wikitextparser as wtp

from ...new_api import load_main_api

logger = logging.getLogger(__name__)

tosearch_and_replace = [
    "{{توثيق شريط}}",
    "{{Navbox documentation}}",
]

to_search = [
    "{{#استدعاء:شريط|شريط",
]

pre_text = """{{صفحة توثيق فرعية}}

=== استعمال ===
{{نسخ:توثيق/مسبق/1|0}}
<!-- إن أردت توليد تلقائي لنموذج قالب فارغ لوسائط هذا القالب بإطار <pre></pre> قم بتحويل الرقم 0 إلى 1
{{نسخ:توثيق/مسبق/1| 0 }}
-->

=== مثال ===
{{توصيف
| <nowiki>
<!-- هنا المثال -->
</nowiki>
| <!-- هنا المثال -->
}}

== بيانات القالب==
{{رأس بيانات القالب}}
<div style="max-height:350px; width:100%; overflow:auto; padding:3px; border:solid 1px;">
<templatedata>
{
 "params": {},
 "format": "block"
}
</templatedata>
</div>

<includeonly>{{ملعب أخر||
<!-- [[تصنيف:قوالب ويكيبيديا]] -->

"""


def add_to_text_temps(text, Final_Categories):

    for x in tosearch_and_replace:
        if text.find(x) != -1:
            text = text.replace(x, x + "\n" + Final_Categories)
            return text

    return text


def add_to_doc_page(text, Final_Categories):

    if text == "":
        return pre_text + "\n" + Final_Categories + "\n}}</includeonly>"

    text2 = add_to_text_temps(text, Final_Categories)

    if text2 != text:
        return text2

    Final_Categories = Final_Categories.strip()

    cats2 = []

    for x in Final_Categories.split("\n"):
        if not x.strip():
            continue

        x2 = x.strip().split("|")[0].strip()
        x3 = x2.strip().split("]]")[0].strip()

        if text.find(x2 + "|") == -1 and text.find(x3 + "]]") == -1:
            cats2.append(x)

    if not cats2:
        return text

    Final_Categories = "\n".join(cats2)

    patern = r"<includeonly>[\s\n]+\[\[تصنيف\:"

    find_all = re.search(patern, text, re.M | re.I)

    new_text2 = text

    if find_all:
        text_string = find_all.group()
        new_text2 = text.replace(text_string, f"<includeonly>\n{Final_Categories}\n[[تصنيف:", 1)

    if new_text2 != text:
        return new_text2

    parsed = wtp.parse(text)

    target_temps = [
        "ملعب آخر",
        "sandbox other",
        "ملعب أخر",
    ]

    temp_done = False

    for template in parsed.templates:

        if not template:
            continue

        template_name = str(template.normal_name()).strip().lower()

        if template_name in target_temps:
            args_2 = template.get_arg("2")

            if args_2 and args_2.value:
                args_2.value += "\n" + Final_Categories
            else:
                template.set_arg("2", Final_Categories + "\n")

            temp_done = True

            break

    if temp_done:
        new_text = parsed.string
    elif text.find("</includeonly>") != -1:
        new_text = text.replace("</includeonly>", "\n" + Final_Categories + "\n</includeonly>", 1)
    else:
        temp_new = "<includeonly>{{ملعب آخر||\n" + Final_Categories + "}}</includeonly>"
        new_text = text + "\n" + temp_new

    return new_text


def add_direct(text, Final_Categories):

    if text.find("{{توثيق") != -1:
        num = text.find("{{توثيق")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    elif text.find("{{توثيق شريط}}") != -1:
        num = text.find("{{توثيق شريط}}")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    elif text.find("{{توثيق}}") != -1:
        num = text.find("{{توثيق}}")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    elif text.find("{{خيارات طي قالب تصفح}}") != -1:
        num = text.find("{{خيارات طي قالب تصفح}}")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    elif text.find("{{خيار طوي قالب}}") != -1:
        num = text.find("{{خيار طوي قالب}}")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    elif text.find("{{collapsible option}}") != -1:
        num = text.find("{{collapsible option}}")
        text = text[:num] + Final_Categories + "\n" + text[num:]

    else:
        # if page.namespace() == 10:
        # text += '\n' + Final_Categories
        text += "\n<noinclude>" + Final_Categories + "</noinclude>"
        text = re.sub(r"\<\/noinclude\>\n\<noinclude\>", "</noinclude><noinclude>", text)
        text = re.sub(
            r"\<noinclude\>\s*(.*?)\s*\<\/noinclude\>\s*\<noinclude\>\s*(.*?)\s*\<\/noinclude\>",
            r"<noinclude>\n\g<1>\n\g<2>\n</noinclude>",
            text,
            flags=re.DOTALL,
        )

    if text.find(Final_Categories.strip()) == -1:
        text += f"\n<noinclude>{Final_Categories}</noinclude>"

    return text


def find_doc_and_add(Final_Categories, title, create=False):

    if any(x in title for x in ["/ملعب", "/مختبر"]):
        logger.info(f"Skipping {title=}")
        return False

    doc_title = f"{title}/شرح"

    api = load_main_api("ar")
    page = api.MainPage(doc_title)

    text = page.get_text()

    if not text and not create:
        logger.info(f' text = "" {doc_title=}')
        return False

    if page.isRedirect():
        return False

    if page.isDisambiguation():
        return False

    if not page.exists() and not create:
        logger.info(f" not exists {doc_title=}")
        return False

    page_edit = page.can_edit(script="cat")

    if not page_edit:
        return False

    new_text = add_to_doc_page(text, Final_Categories)

    fi = "، ".join(Final_Categories.split("\n")).strip()

    fi = fi.replace("[[تصنيف:", "[[:تصنيف:")

    sumary = f"بوت [[مستخدم:Mr.Ibrahembot/التصانیف المعادلة|التصانيف المعادلة]]: +({fi})"

    if new_text != text:
        save = page.save(new_text, summary=sumary, nocreate=not create)
        if save:
            return True

    return False


def add_text_to_template(text, Final_Categories, title):
    """
    Adds the final categories to the provided text at the appropriate location.

    Args:
        text (str): The text to add the final categories to.
        Final_Categories (str): The final categories to add to the text.

    Returns:
        str: The text with the final categories added.
    """

    logger.info("page.namespace() == 10 ")

    if title.endswith("/شرح"):
        text = add_to_doc_page(text, Final_Categories)
        return text

    elif any(x in text for x in tosearch_and_replace):
        text = add_to_text_temps(text, Final_Categories)
        return text

    elif any(x in text for x in to_search):
        text = add_direct(text, Final_Categories)
        return text
    else:
        added = find_doc_and_add(Final_Categories, title, create=True)
        if added:
            return text

    text = add_direct(text, Final_Categories)

    return text
