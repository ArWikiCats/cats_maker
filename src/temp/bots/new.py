# maketemps.py
import logging
import re

logger = logging.getLogger(__name__)


class TemplatesMaker:
    """Class to generate different wiki templates for centuries, decades, years, and millennia."""

    # ====== البيانات الثابتة ======
    elfffff = {
        -1: [-1],
        1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        2: [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        3: [21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
    }

    decades_list = {
        1: ["0", "10", "20", "30", "40", "50", "60", "70", "80", "90"],
        -1: ["-90", "-80", "-70", "-60", "-50", "-40", "-30", "-20", "-10"],
    }

    cacaca = {"تأسيسات ": "تأسيس ", "انحلالات ": "انحلال ", "": ""}

    years_Baco = {}
    Baco_decades = {}
    Baco_centries = {}
    Baco = {}

    @classmethod
    def _initialize_data(cls):
        """Build the lookup dictionaries (only once)."""
        if cls.years_Baco:
            return  # Already initialized

        for elff, tatt in cls.elfffff.items():
            for centry in tatt:
                centry2 = str(centry - 1)
                if centry2 == "0":
                    centry2 = ""
                cls.Baco_centries[str(centry)] = elff

                decades = cls.decades_list.get(centry, [f"{centry2}{x}0" for x in range(0, 10)])
                for dic in decades:
                    if dic == "00":
                        dic = "0"
                    cls.Baco_decades[str(dic)] = centry
                    cls.Baco[int(dic)] = centry

                    years = [int(dic) + x for x in range(0, 10)]
                    if int(dic) < 1:
                        years = [int(dic) - x for x in range(0, 10)]
                    for year in years:
                        cls.years_Baco[str(year)] = {"dic": dic, "centry": centry}

    # ====== الدوال الرئيسية ======
    @classmethod
    def Make_Elff_temp(cls, title):
        logger.info(f"<<lightblue>> Make_Elff_temp :{title} ")
        title = re.sub(r"الألفية الأولى", "الألفية 1", title)
        title = re.sub(r"الألفية الثانية", "الألفية 2", title)
        title = re.sub(r"الألفية الثالثة", "الألفية 3", title)

        for texx, xdx in cls.cacaca.items():
            regex = rf"تصنيف\:{texx}الألفية (\d+|)( ق م| ق\.م|)( في |)(.*|)$"
            if re.sub(regex, "", title):
                continue

            elffs = re.sub(regex, r"\g<1>", title)
            bef = re.sub(regex, r"\g<2>", title)
            In = re.sub(regex, r"\g<3>", title)
            bld = re.sub(regex, r"\g<4>", title)

            if elffs == title:
                elffs = ""
            if bef == title:
                bef = ""

            if elffs in ["1", "2", "3"] and not bef:
                bld = bld.strip()
                temp = f"{xdx}بلد الألفية {elffs}" if texx else f"الألفية {elffs} في بلد"
                ass = f"|{bld}" if bld else ""
                if bld.startswith("حسب"):
                    ass += "|في="
                if not bld:
                    temp = f"{xdx} الألفية {elffs}"

                return f"{{{{{temp}{ass}}}}}", temp

        return "{{تصنيف موسم}}", "تصنيف موسم"

    @classmethod
    def MakedecadesTemp(cls, title):
        title = re.sub(r"_", " ", title)
        for texx, ssss in cls.cacaca.items():
            regdd = rf"{texx}عقد (\d+)( ق م| ق\.م|)"
            regex = "تصنيف:" + regdd + "( في |)(.*|)$"
            dee = re.sub(regex, r"\g<1>", title)
            if dee and dee in cls.Baco_decades:
                bld = re.sub(regex, r"\g<4>", title).strip()
                ass = ""
                if bld:
                    ass = f"|بلد={bld}" if not bld.startswith("حسب") else f"|حسب={bld}"
                Qrn = str(cls.Baco_decades[dee])
                temp = f"{ssss}عقد" if texx else "تصنيف عقد"
                return f"{{{{{temp}|قرن={Qrn}|عقد={dee}{ass}}}}}", temp
        return "{{تصنيف موسم}}", "تصنيف موسم"

    @classmethod
    def Make_Cent_temp(cls, title):
        title = re.sub(r"_", " ", title)
        for texx, cttt in cls.cacaca.items():
            regex = rf"تصنيف\:{texx}القرن (\d+)( ق م| ق\.م|)( في |)(.*|)$"
            dee = re.sub(regex, r"\g<1>", title)
            if dee:
                bef = re.sub(regex, r"\g<2>", title)
                bld = re.sub(regex, r"\g<4>", title).strip()
                ass = f"|بلد={bld}" if bld else ""
                if bld.startswith("حسب"):
                    ass = f"|حسب={bld}"
                sss = "-" if bef else ""
                temp = f"{cttt}قرن" if texx else "سنوات في القرن"
                return f"{{{{{temp}|{sss}{dee}{ass}}}}}", temp
        return "{{تصنيف موسم}}", "تصنيف موسم"

    @classmethod
    def Make_years_temp(cls, title, tex, return_title=False):
        if "ق م" in title or "ق.م" in title:
            return ("", "") if return_title else ""
        t_1 = f"تصنيف:{tex}"
        ttt = t_1 + r"(عام |سنة |)(\d+)\s*(في |)(.*|)$"
        ye = re.sub(ttt, r"\g<2>", title)
        if ye not in cls.years_Baco:
            return ("{{تصنيف موسم}}", "تصنيف موسم") if return_title else "{{تصنيف موسم}}"

        bld = re.sub(ttt, r"\g<4>", title)
        Y = ye[-1] if len(ye) >= 1 else ""
        YY = ye[:-1] if len(ye) >= 2 else ""
        template = f"{cls.cacaca[tex]}بلد"
        if bld.startswith("حسب"):
            bld += "|في="
        text = f"{{{{{template}|{YY}|{Y}|{bld}}}}}" if bld else f"{{{{{cls.cacaca[tex]}سنة|{YY}|{Y}}}}}"
        return (text, template) if return_title else text

    @classmethod
    def main_make_temp(cls, enca, title):
        title = re.sub(r"_", " ", title)
        if "فيروس كورونا" in title:
            return "", ""
        if re.match(r"^تصنيف\:\d+.*", title) or re.match(r".*\d\d\d\d[\-\–]\d\d$", title):
            return "{{تصنيف موسم}}", "تصنيف موسم"
        for tex in ["تأسيسات ", "انحلالات "]:
            if any(title.startswith(f"تصنيف:{tex}{n}") for n in range(10)):
                return cls.Make_years_temp(title, tex, return_title=True)
        if title.startswith("تصنيف:عقد") or title.startswith("تصنيف:تأسيسات عقد"):
            return cls.MakedecadesTemp(title)
        if "القرن" in title:
            return cls.Make_Cent_temp(title)
        if "الألفية" in title:
            return cls.Make_Elff_temp(title)
        return "", ""


bot = TemplatesMaker()
bot._initialize_data()

MakedecadesTemp = bot.MakedecadesTemp
Make_years_temp = bot.Make_years_temp
Make_Cent_temp = bot.Make_Cent_temp
Make_Elff_temp = bot.Make_Elff_temp
main_make_temp = bot.main_make_temp

__all__ = [
    "MakedecadesTemp",
    "Make_years_temp",
    "Make_Cent_temp",
    "Make_Elff_temp",
    "main_make_temp",
]
