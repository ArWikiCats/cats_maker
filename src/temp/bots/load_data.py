#!/usr/bin/python3
"""

from .load_data import years_Baco, Baco_decades, Baco_centries, Baco, elfffff, decades_list, cacaca

"""

years_Baco = {}
Baco_decades = {}
Baco_centries = {}
Baco = {}

elfffff = {
    -1: [-1],
    1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    2: [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
    3: [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
}

decades_list = {}
decades_list[1] = ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90"]
decades_list[-1] = ["-90", "-80", "-70", "-60", "-50", "-40", "-30", "-20", "-10"]

cacaca = {"تأسيسات ": "تأسيس ", "انحلالات ": "انحلال ", "": ""}

for elff, tatt in elfffff.items():
    for centry in tatt:
        centry2 = str(centry - 1)
        if centry2 == "0":
            centry2 = ""

        Baco_centries[str(centry)] = elff
        if centry in decades_list:
            decades = decades_list[centry]
        else:
            decades = [f"{centry2}{x}0" for x in range(0, 10)]

        for dic in decades:
            if dic == "00":
                dic = "0"
            Baco_decades[str(dic)] = centry
            Baco[int(dic)] = centry
            years = [int(dic) + x for x in range(0, 10)]
            if int(dic) < 1:
                years = [int(dic) - x for x in range(0, 10)]

            for year in years:
                years_Baco[str(year)] = {"dic": dic, "centry": centry}
