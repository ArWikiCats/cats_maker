"""
from ..tools_bots.sort_bot import CatSorting
"""

import re


def sort_text(categorylist):
    finallradeh = []
    s_radeh = []
    # ---
    alphabets = " 0123456789آاأإبتثجحخدذرزسشصضطظعغفقكلمنهوي"
    # ---
    for radeh in categorylist:
        radeh = radeh.replace("[[تصنيف:", "").replace("]]", "")
        # ---
        coderadeh = radeh
        # ---
        for i in range(0, len(alphabets)):
            alphabet = alphabets[i]
            # ---
            if i < 10:
                j = "0" + str(i)
            else:
                j = str(i)
            # ---
            coderadeh = coderadeh.replace(alphabet, j)
        # ---
        s_radeh.append(coderadeh + "0000000000000000000@@@@" + radeh)
    # ---
    s_radeh = list(set(s_radeh))
    # ---
    sortedradeh = sorted(s_radeh)
    # ---
    for radeh in sortedradeh:
        radeh = "[[تصنيف:" + radeh.split("@@@@")[1] + "]]"
        finallradeh.append(radeh)
    # ---
    return finallradeh


def sort_categories(text, title):
    """
    This function sorts the categories in a given text based on a specific page.

    Args:
        text (str): The text that contains the categories to be sorted.
        title (str): The title of the page that contains the categories.

    Returns:
        str: The text with the categories sorted.
    """
    # ---
    new_text = text
    # ---
    RE = re.compile(r"(\[\[تصنيف\:(?:.+?)\]\])")
    # ---
    cats = RE.findall(text)
    # ---
    if not cats:
        return text  # ,msg
    # ---
    for i in cats:
        new_text = new_text.replace(i, "")
    # ---
    cats = sort_text(cats)
    # ---
    for name in cats[1:]:
        if re.search(r"\[\[(.+?)\|[ \*]\]\]", name) or "[[تصنيف:" + title == name.split("]]")[0].split("|")[0]:
            cats.remove(name)
            cats.insert(0, name)
    # ---
    if cats == RE.findall(text):
        return text  # ,msg
    # ---
    for i in cats:
        new_text = new_text + "\n" + i
        new_text = new_text.replace("\r", "").replace("\n\n\n\n", "\n").replace("\n\n\n", "\n")
    # ---
    return new_text
