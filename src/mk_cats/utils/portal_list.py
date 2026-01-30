#!/usr/bin/python3
""" """

import json
from pathlib import Path

Dir = Path(__file__).parent

with open(f"{Dir}/New_Portal_List.json", "r", encoding="utf-8") as c:
    New_Portal_List = json.load(c)

portal_en_to_ar_lower = {}
# ---
for ar in New_Portal_List:
    en = New_Portal_List[ar]["en"]
    # ---
    if en:
        portal_en_to_ar_lower[en.lower()] = ar
