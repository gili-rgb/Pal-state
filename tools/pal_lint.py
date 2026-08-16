#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pal-lint — שכבת אכיפה דטרמיניסטית לכל פלט של Pal Group (HTML לאלמנטור + Markdown לדפי מוצר).
stdlib בלבד. אפס תלויות. אפס צעדים ידניים.

שימוש:
    python3 pal_lint.py FILE [--site csb|marom|plrom] [--type blog|brandhub|product] [--keyword "מילת מפתח"] [--json]

Exit code: 0 = ירוק (מותר להגיש) | 1 = ERROR קיים (אסור להגיש) | 2 = שגיאת קלט
site לא סופק => זיהוי אוטומטי לפי דומיינים בקובץ.
type לא סופק => auto: brandhub לפי סמנים ייחודיים (diagnostic-box/brand-grid/sticky-cta),
                product לפי סיומת .md, אחרת blog. bh-pref-mini קיים גם בבלוגים ואינו סמן.
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

# changelog:
#  v1.4.0 (2026-07-23) — כלל חדש SCHEMA_ID_YOAST_COLLISION (ERROR): @id שאנחנו מגדירים ב-JSON-LD אסור
#    שיסתיים בדיוק ב-#article/#organization/#breadcrumb/#website/#primaryimage — אלה סיומות קבועות
#    של ה-@graph האוטומטי של Yoast (פעיל בכל האתרים), והתנגשות @id בין שני <script> ld+json באותו
#    עמוד גורמת ל-Rich Results Test לדווח breadcrumb/schema כלא תקין (אומת חי ב-Rich Results Test,
#    2026-07-16, מאמר Plrom Miele). מוסכמה: content-machine→#content-*, brand-hub-machine→#brandhub-*.
#    הערה: תיקון זה תועד קודם כבוצע (v1.4.0) אך לא נדחף בפועל לריפו — נסגר עכשיו, 2026-07-23.
#  v1.3.0 (2026-07-08) — יישום אודיט הסקילים: 4 כללים חדשים — ANCHOR_FORBIDDEN (ERROR: עוגן "כאן"/"לחץ כאן"/"למידע נוסף" בקישור פנימי), ANCHOR_DUPLICATE (WARN), LINK_BUDGET (WARN blog: מחוץ ל-4-14), SPEAKABLE_MISSING (WARN blog/brandhub). check_links מקבל doc_type. מוזג מעל v1.2.3 (MAROM_PC_LINK נשמר).
#  v1.2.3 (2026-07-08) — כלל MAROM_PC_LINK: /product-category/ במרום = ERROR (המוסכמה slug עברי /[brand]-אביזרים-וחלפים/). link_audit הפך לדרישת אימות check_url חוסמת.
#  v1.2.2 (2026-07-08) — תיקון DELONGHI_FRIDGE false-positive: "מקרר" בעמוד מותג אחר + "דלונגי" ברשימת מותגים/schema. כעת בדיקה פסקה-פסקה.
#  v1.2.1 (2026-07-07) — תיקון BRAND_BEKO false-positive: "בקו" תפס "בקושי"/"המתנה בקו". כעת רק Beko לטיני או "בקו"+מונח מכשיר.
#  v1.2.0 (2026-07-05) — קליטת Yoast/Zero-Hallucination/schema עמוק/WCAG/responsive/CTA/WAF-blog מהסקילים.
VERSION = "1.13.0"
# v1.13.0 (2026-08-16): פלרום עובר לעוגן סמכות ארגוני. הכרעת גיל.
#   הרקע: SITES הגדיר expert="דניאל", אבל project-plrom.md מעולם לא החזיק
#   שם, תפקיד או sameAs — רק "עוגן סמכות: מומחה שירות פלרום". התוצאה היא
#   ישות Person בכל מאמר פלרום בלי jobTitle ובלי הוכחה חיצונית, כלומר
#   E-E-A-T על הנייר. ישות אדם שאי אפשר לאמת אי אפשר לצטט, וזה בדיוק
#   המדד שאנחנו מנסים להזיז. אדם מזויף גרוע מארגון אמיתי.
#   (1) plrom.expert = None, ו-"דניאל" עבר ל-wrong_experts. כל שם פרטי
#       בתוכן פלרום הוא עכשיו ERROR.
#   (2) שדה חדש author_org_only (plrom=True, csb/marom=False).
#   (3) PERSON_ENTITY_FORBIDDEN (ERROR) — ישות Person ב-@graph של אתר
#       שסומן org_only.
#   (4) AUTHOR_NOT_ORG (ERROR) — author חייב להצביע על #content-organization
#       ולא על #content-author.
#   המעבר הפוך ברגע שיתקבלו שם, תפקיד ו-sameAs אמיתיים: הופכים את הדגל.
# v1.12.0 (2026-08-16): שכבת הקישורים של מרום יושרה מול המציאות.
#   (1) MAROM_PC_LINK **נמחק**. הכלל (v1.2.3) טען ש-/product-category/ במרום
#       הוא "כמעט תמיד 301/404". בדיקה מול מיפוי GSC: 420 עמודים, 308,604
#       חשיפות, 12,847 קליקים, 209 עם קליקים בפועל, 73 במיקום 1-3.
#       /product-category/sharp/ לבדו: 1,520 קליקים במיקום 1.0. המוסכמה
#       שהכלל דרש במקום (/[brand]-אביזרים-וחלפים/) מחזיקה 9 עמודים ו-10,967
#       חשיפות. הכלל חסם פי 28 ממה שהגן עליו, ו-preflight המליץ על אותם
#       עמודים ש-postflight חסם — חזרה מדויקת של כשל v8.12. הבעיה שהכלל נועד
#       לפתור (כתובות מומצאות) מכוסה ב-link_audit שנכנס באותה גרסה עצמה.
#   (2) BRAND_LINK_UNKNOWN (ERROR, מרום) — קישור ל-/brands/ שאינו ברשימה
#       הסגורה של 17 עמודי המותג המאושרים. תופס שגיאות כתיב בכתובת מותג,
#       שהיו עוברות בשקט עד היום. הכרעת גיל: רשימה סגורה ולא תבנית, כי אין
#       כוונה להוסיף עמודי שותפים חדשים.
#   (3) base_brand_path — נרמול קידומת שפה. הכרעת גיל: עמוד מתורגם הוא אותו
#       עמוד. /en/brands/amana-service ו-/ru/brands/moulinex-service קיימים
#       בפועל ב-GSC ונחשבים זהים לעמוד המקור.
# v1.11.1 (2026-08-10): EVASIVE_ANSWER לא זיהה גרשיים עברי (U+05F4) —
#   "ש״ח" נכשל למרות מספר אמיתי בתשובה. נוסף גם TEL_FORMAT: href="tel:"
#   עם מקפים עלול לא לעבוד בחלק מהמכשירים.
# v1.11.0 (2026-08-10): EVASIVE_ANSWER (ERROR) — שאלה מסחרית חייבת מספר בתשובה.
#   הרקע: מאמר Refresh על עמוד עם 73,539 חשיפות במיקום 5.2 ו-CTR 0.25% ענה
#   על "כמה עולה ביקור טכנאי" ב"העלות תלויה, פתחו קריאת שירות". זו הפניה
#   ולא תשובה, וזה בדיוק מה שמייצר CTR כזה. המאמרים נועדו להמיר.
#   מחירים מאומתים חיים בזיכרון: CSB 349 ₪, פלרום 390/340/290 ₪.
# v1.10.0 (2026-08-06): BRAND_SAMEAS_MISSING (WARN) — קישור לגרף הידע העולמי.
#   ישות Brand ב-@graph של מותג שנמצא ב-brand-entities.md חייבת sameAs.
#   הרישום מאומת ידנית; מותג שאינו בו אינו מעורר אזהרה. QID שגוי גרוע מחסר —
#   ל-"Sharp" קיימות שלוש ישויות בוויקידאטה, אחת מהן יצרן רובי אוויר.
# v1.9.0 (2026-08-06): BRAND_HUB_MISSING (ERROR, blog) — כל מאמר חייב קישור אחד לפחות
#   ל-/brands/. הרקע: עמודי השותפים בשורש (/bosch-service/ 178K חשיפות,
#   /siemens-service/ 86K) קולטים את שאילתות המותג, בעוד עמודי המותג שלנו תחת
#   /brands/ עומדים על אפס. 301 אינו אפשרי מסיבות עסקיות, ולכן הערוץ היחיד
#   להעברת סמכות הוא קישורים פנימיים מכל תוכן חדש.
# v1.8.0 (2026-08-03, סריקת שלמות: 90 אמירות מחייבות בקבצי הסקיל מופו למנגנון אוכף.
#   חמישה פערים אמיתיים נסגרו):
#   SUPERLATIVE (ERROR)      — שיווקיות אסורה ממאסטר-פרומפט ("מוביל", "מהפכני", "הטוב ביותר")
#   FOCUS_OUTLINE (ERROR)    — הסרת outline ב-:focus שוברת ניווט מקלדת
#   PREF_STRIP_ORDER (ERROR) — bh-pref-mini חייב להיות אחרי author-bio ואחרי cta-box
#   PERMALINK_CASE (ERROR)   — %XX ב-uppercase בקישור פנימי גורם 404
#   TERM_PLROM_NAME (ERROR)  — "חברת פלרום"; הנכון "שירות פלרום"
# v1.7.0 (2026-08-03, מיזוג שני מסלולי v1.6.1 שנוצרו במקביל בשני סשנים):
#   H1_LISTICLE (WARN) — H1 בדפוס ליסטיקל. גיל דחה את הדפוס שלוש פעמים (9.7, 3.8).
#     תופס גם בלי מספר. מועדף: הד לשאילתה ("X לא עובד: מה הסיבה ומה עושים?").
#   org_sameas הושלם ל-csb ו-plrom (היה למרום בלבד).
# v1.6.1 (2026-08-03): TERM_BAUKNECHT (ERROR) — "באוכנט" אינו קיים בשוק; הכתיב הנכון
#   "באוקנכט" (ניופאן היבואן, וכל הקמעונאים). ניתוח GSC: הכתיב השגוי צבר חשיפות רק
#   מה-meta description שלנו עצמו. הכתיב הנכון: 12,790 חשיפות אמיתיות מול 2,972.
# v1.6.0 (2026-08-03, לקחי ריצת "מצב שבת שארפ"): שני כללים חדשים + תיקון מדידה.
#   COMPETITOR_SOURCE (ERROR): ספקי לידים שמתחרים על אותן שאילתות שירות אסורים
#     כמקור מצוטט, כקישור וכאזכור בשם. כרייה מהם למחקר מותרת; ציטוט לא.
#   ORG_SCHEMA_DRIFT (ERROR): Organization היא ישות יציבה ברמת האתר. חובה
#     telephone/url תואמים ל-SITES וכל sameAs הקנוני. נצפה דריפט בין שני מאמרי
#     מרום באותו יום: באחד sameAs כלל ערוץ יוטיוב, בשני נעלם.
#   KEYWORD_DENSITY: מדידה על ביטוי בן 3+ מילים החזירה תמיד ~0.3%. היעד 1-2%
#     נמדד מעכשיו על ראש הביטוי (2 מילים) + דוח כיסוי לכל רכיב.
# v1.5.0 (2026-08-03, לקחי ריצת "וו גיטרה" מרום): שלושה כללים חדשים —
#   SOURCES_INTERNAL_TOOL (ERROR): כלי מחקר פנימיים (Search Console, Bing Webmaster, GSC,
#     WooCommerce, MCP, content-ledger, Autocomplete) אסורים ברשימת המקורות הגלויה ללקוח.
#   DANGLING_CONNECTOR (WARN): מחבר ניגוד (אך/אבל/אולם/ואילו) אחרי פסוקית קצרה מ-4 מילים —
#     דפוס של משפט שבור תחבירית ("וו לישה, אך הוא מושך ומקפל").
#   TRANSITION_STACK (WARN): 2+ מילות קישור באותו משפט, או >50% מהפסקאות נפתחות במילת קישור.
#     Yoast יראה ירוק ב-30-45% והטקסט עדיין ייקרא מכני.
#   בנוסף: PHONE_CANON (WARN) — מרום, 2620* בתוכן חדש; הקנוני *2620 (שתי הצורות תקפות).
# @id שאנחנו מגדירים אסור שיסתיים בדיוק באחת מהסיומות הבאות (שמורות ל-@graph האוטומטי של Yoast):
YOAST_GRAPH_ID_SUFFIXES = ("#article", "#organization", "#breadcrumb", "#website", "#primaryimage")
# v1.2.0 (2026-07-05, audit חוצה-סקילים): קליטת הבדיקות המוטמעות מהסקילים כמקור יחיד —
#   yoast (מילים/משפטים/transitions עם גבולות מילה/H1), Zero Hallucination (אחוז/מק"ט/TOC),
#   schema_deep (@id/FAQPage=H3/dateModified), WCAG (כותרות/alt/scope/table-wrap),
#   responsive+&#9742;+CTA-login ל-brandhub, WAF %XX הורחב גם ל-blog, חילוץ קישורים ל-link_audit.
#   תיקונים: טלפון מרום מקבל *2620 וגם 2620* (קנוני: *2620, כוכבית לפני הספרות),
#   detect_type לא נשען יותר על "bh-" (בלוגים מכילים bh-pref-mini), טרמינולוגיה הושלמה,
#   "חיקוי" אסור ב-type=product. מדיניות Product schema: בבלוג אין ישות Product בכלל
#   (content-machine v7.15); כשיש Product (brandhub) — offers חובה.
# v1.1.0 (2026-07-05): חוסמי Elementor מלאים.

# ---------------------------------------------------------------- כללי אמת

SITES = {
    "csb": {
        "domain": "csb.co.il",
        "expert": "אילן שמה",
        "wrong_experts": ["סמי", "מיכה", "דניאל"],
        "author_org_only": False,
        "phone_ok": ["08-977-7222", "089777222", "08-9777222"],
        "phone_bad": [],
        "nap_street": "הצורפים 3",
        "nap_city": "לוד",
        "sitemap_ok": "csb.co.il/sitemap-2/",
        "org_sameas": ["youtube.com/@csbinc"],
        "forbidden_paths": [
            "/bosch-service/", "/siemens-service/",
            "/bosch-parts/", "/siemens-parts/",
        ],
        "allowed_brand_links": None,
        "forbidden_pc": False,  # product-category מותר
    },
    "marom": {
        "domain": "marom-serv.co.il",
        "expert": "מיכה איתן",
        "wrong_experts": ["דניאל", "סמי", "אילן שמה"],
        "author_org_only": False,
        # קנוני: *2620 (הכוכבית לפני הספרות — הכרעת גיל 2026-07-05). 2620* מתקבל בעמודים קיימים.
        "phone_ok": ["*2620", "2620*"],
        "phone_bad": ["03-9799799", "039799799", "03-979-9799"],
        "nap_street": "הצורף 3",
        "nap_city": "חולון",
        "sitemap_ok": "marom-serv.co.il/sitemap/",
        # v1.6.0: sameAs קנוני, חובה בכל Organization באתר
        "org_sameas": ["youtube.com/@user-marom-serv"],
        "forbidden_paths": [
            f"/{b}-{k}/"
            for b in ["sharp", "dedietrich", "bauknecht", "haier",
                      "blomberg", "delonghi", "amana", "zanussi"]
            for k in ["parts", "service"]
        ],
        "allowed_brand_links": [
            # הכרעת גיל 2026-08-16: רשימה סגורה, לא תבנית. גיל אינו מוסיף
            # עמודי שותפים חדשים, ולכן רשימה מפורשת עדיפה על regex.
            # 17 עמודי מותג. /brands/sharp-service/ הוא החזק ביותר
            # (5,739 חשיפות, 55 קליקים). lavamat ו-bauknecht אושרו על ידי
            # גיל אף שאין להם נתוני GSC.
            "/brands/sharp-service/", "/brands/moulinex-service/",
            "/brands/blomberg-service/", "/brands/haier-service/",
            "/brands/delonghi-service/", "/brands/zanussi-service/",
            "/brands/philips-service/", "/brands/magimix-service/",
            "/brands/kitchenaid-service/", "/brands/tefal-service/",
            "/brands/grundig-service/", "/brands/lavamat-service/",
            "/brands/indesit-service/", "/brands/bauknecht-service/",
            "/brands/amana-service/",
            # עמודי חלפים שהם שלנו ולא של השותף, מותרים לקישור במפורש.
            "/kitchenaid-parts/", "/magimix-parts/",
        ],
        "forbidden_pc": False,  # product-category מותר
    },
    "plrom": {
        "domain": "plrom.co.il",
        # הכרעת גיל 2026-08-16: לפלרום אין מומחה נקוב מאומת. עוגן ארגוני
        # במקום ישות Person. "דניאל" הופיע בלינט אך מעולם לא הופיע בקובץ
        # התוכן עם תפקיד או הוכחה חיצונית, ולכן ייצר ישות אדם ריקה.
        # expert=None מכבה את בדיקת ההתאמה; כל שם פרטי בתוכן פלרום שגוי.
        "expert": None,
        "wrong_experts": ["מיכה", "סמי", "אילן שמה", "דניאל"],
        "author_org_only": True,
        "phone_ok": ["073-2625600", "0732625600", "073-262-5600"],
        "phone_bad": [],
        "nap_street": "ישראל זמורה 2",
        "nap_city": "לוד",
        "sitemap_ok": "plrom.co.il/sitemap/",
        "org_sameas": ["youtube.com/@plrom"],
        "forbidden_paths": [
            "/sauter-service/", "/liebherr-service/",
            "/miele-service/", "/miele-parts/",
        ],
        "allowed_brand_links": None,
        "forbidden_pc": True,  # כל product-category אסור בפלרום
    },
}

# טרמינולוגיה: אסור => חלופה
TERMS_ERROR = {
    "פד שוחק": "ספוג שוחק",
    "ווי פח": "תופסני מתכת",
    "פריג'": "מקרר",
    "כלונסאות": "מסילות הצד",
    "סילוני מים": "ממטרה",
    "פלינטוס": "צוקל",
    "בורוסיליקט": "עמיד בחום / זכוכית עמידה",
    "פולימר": "פלסטיק קשיח",
}
TERMS_WARN = {
    "פקקים": "ספייסר (אם הכוונה לחלק מרווח)",
    "פיר": "מוט החיבור (אם הכוונה לחלק המסתובב)",
    "תרמי": "עמיד בחום (אם מדובר בחומר)",
    "סירקולציה": "שפת יצרן — נסח בשפת לקוח",
    "נקבוביות": "שפת יצרן — נסח בשפת לקוח",
    "תא התנור": "שפת יצרן — נסח בשפת לקוח (חלל התנור / בתוך התנור)",
}

FORBIDDEN_DOMAINS = ["jeepolog.com"]

# v1.6.0: ספקי לידים שמתחרים על אותן שאילתות שירות. מותר לכרות מהם שפת לקוח,
# אסור לצטט, לקשר או לאזכר בשם בתוכן שמתפרסם.
COMPETITOR_DOMAINS = ["midrag.co.il", "pro.co.il", "prog.co.il", "mitmachim.top"]

# נכסי הקבוצה בדומיינים נפרדים. אינם מתחרים ואינם מתחזים.
# csb-service.co.il מנוהל על ידי ORM ניהול מוניטין, שותף עסקי (אומת 2026-08-09).
# סשן אימות סימן אותו כ"דומיין מתחזה" — מסקנה סבירה ושגויה. רשום כאן
# כדי שסשן עתידי לא יגלה זאת מחדש ולא ידווח שגוי.
GROUP_ASSETS = ["csb-service.co.il"]
COMPETITOR_NAMES = ["מידרג", "המקצוענים", "פרוג"]

HEB_RANGE = "\u0590-\u05FF"

# מילון transitions אחד (מקור יחיד; מחליף את הרשימות המקומיות בסקילים).
# "כמו כן" הוצא — PPM מסווג אותה כשפה ארכאית; לא נספרת ולא אסורה.
TRANSITIONS = [
    "לכן", "בנוסף", "לעומת זאת", "כתוצאה מכך", "עם זאת", "כלומר", "מסיבה זו",
    "חשוב לציין", "אם כך", "למרות ש", "מכיוון ש", "אחרי ש", "נוסף על כך",
    "בגלל ש", "ראשית", "שנית", "לסיכום", "יתרה מזאת", "במילים אחרות",
    "לדוגמה", "למשל", "אך", "אבל", "אולם", "כדי", "מפני ש",
]

PASSIVE_HINTS = ["נעשה", "בוצע", "הוחלף", "יוחלף", "יותקן", "הותקן", "נבדק",
                 "ייבדק", "נוקה", "ינוקה", "הוזמן", "יוזמן", "נמצא כי"]

WORD_TARGETS = {"blog": (1800, 2000), "brandhub": (1600, 2200)}  # product: אין יעד אורך

# ---------------------------------------------------------------- עזרים

def strip_blocks(html, tag):
    return re.sub(rf"<{tag}\b.*?</{tag}>", " ", html, flags=re.S | re.I)

def visible_text(html):
    t = strip_blocks(strip_blocks(html, "script"), "style")
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return t

def heb_bound(term):
    """התאמת מונח עם גבולות מילה עבריים + תחיליות שימוש (ב/ל/מ/ה/ו/כ/ש)."""
    return rf"(?<![{HEB_RANGE}])(?:[ובלכמש]{{0,2}}ה?)?{re.escape(term)}(?![{HEB_RANGE}])"

def line_of(html, pos):
    return html.count("\n", 0, pos) + 1

def snippet(html, pos, span=45):
    s = html[max(0, pos - span):pos + span].replace("\n", " ")
    return "…" + s.strip() + "…"

class Report:
    def __init__(self):
        self.errors, self.warns, self.info = [], [], []

    def err(self, rule, msg, line=None):
        self.errors.append({"rule": rule, "msg": msg, "line": line})

    def warn(self, rule, msg, line=None):
        self.warns.append({"rule": rule, "msg": msg, "line": line})

    def note(self, msg):
        self.info.append(msg)

# ---------------------------------------------------------------- בדיקות

def check_emdash(html, rep):
    for m in re.finditer("\u2014", html):
        rep.err("EMDASH", f"קו מפריד ארוך (—) שורה {line_of(html, m.start())}: {snippet(html, m.start())}", line_of(html, m.start()))
    for m in re.finditer("\u2013", html):
        rep.warn("ENDASH", f"en dash (–) שורה {line_of(html, m.start())} — מומלץ מקף רגיל", line_of(html, m.start()))

def check_css(html, rep):
    styles = re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.S | re.I)
    inline = re.findall(r'style="([^"]*)"', html)
    all_css = "\n".join(styles + inline)
    for m in re.finditer(r"var\(\s*--", all_css):
        rep.err("CSS_VAR", "שימוש ב-var(--…) — Elementor דורש hex קשיח בלבד (v7.7/v1.16)")
    for m in re.finditer(r"(?:^|[{;])\s*--[\w-]+\s*:", all_css, flags=re.M):
        rep.err("CSS_CUSTOM_PROP", "הגדרת CSS custom property (--x:) אסורה")
    for s in styles:
        if re.search(r"/\*.*?\*/", s, flags=re.S):
            rep.err("CSS_COMMENT", "CSS comment בתוך <style> — v7.7 מחייב אפס הערות")
        for m in re.finditer(r"\b[\d.]+rem\b", s):
            rep.err("CSS_REM", f"יחידת rem ב-CSS ({m.group(0)}) — px מפורש בלבד")

def check_backslash(html, rep):
    body = strip_blocks(html, "script")
    for m in re.finditer(r"\\", body):
        rep.err("BACKSLASH", f"backslash ב-HTML גלוי (חוסם publish, בד\"כ geresh escaped) שורה {line_of(body, m.start())}: {snippet(body, m.start())}")

def check_elementor_blockers(html, rep):
    if "unicode-bidi" in html:
        rep.err("UNICODE_BIDI", "unicode-bidi — חוסם שמירת Elementor בכל וריאציה")
    for m in re.finditer(r"<svg\b", html, flags=re.I):
        rep.err("SVG_INLINE", f"<svg> inline שורה {line_of(html, m.start())} — השתמש ב-HTML entity (&#9733; &#9742;)")
    if "data-ga-event" in html:
        rep.err("GA_EVENT", "data-ga-event — אסור בווידג'ט Elementor")
    for m in re.finditer(r'target="_blank"', html):
        rep.err("TARGET_BLANK", f'target="_blank" שורה {line_of(html, m.start())} — אסור')
    for cp, nm in ((0x2011, "U+2011 non-break hyphen"), (0x00AD, "U+00AD soft hyphen"), (0x200B, "U+200B zero-width")):
        for m in re.finditer(chr(cp), html):
            rep.err("CHAR_BLOCKER", f"{nm} שורה {line_of(html, m.start())} — מקף = '-' רגיל")
    for s in re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.S | re.I):
        o, c = s.count("{"), s.count("}")
        if o != c:
            rep.err("CSS_UNBALANCED", f"CSS לא מאוזן: {{ ={o}, }} ={c} — הגורם הנפוץ ל'החיבור אבד'")
        if re.search(r"@media[^{]*\{[^{}]*@media", s):
            rep.err("MEDIA_NESTED", "@media מקונן — אסור")
    for m in re.finditer(r'href=(""|"\s*"|(?=[\s>]))', html):
        rep.err("HREF_EMPTY", f"href ריק שורה {line_of(html, m.start())}")
    for tag in ("article", "style", "script"):
        if len(re.findall(rf"<{tag}\b", html, flags=re.I)) != len(re.findall(rf"</{tag}>", html, flags=re.I)):
            rep.err("TAG_UNBALANCED", f"<{tag}> לא מאוזן")

def check_percent_encoding(html, rep, doc_type):
    urls = re.findall(r'(?:href|src)="([^"]+)"', html)
    urls += re.findall(r'"url"\s*:\s*"([^"]+)"', html)
    for u in urls:
        if re.search(r"%[0-9a-f]?[A-F]|%[A-F]", u):
            rep.err("PCT_UPPER", f"percent-encoding באותיות גדולות => 404. URL: {u[:90]}")
    # WAF: רצף %XX ארוך ב-href. חל על כל ווידג'ט Elementor — blog וגם brandhub (v7.12+/v1.8+).
    # url ב-schema (offers) נשאר verbatim percent-encoded לפי v1.12 — לא נבדק כאן.
    if doc_type in ("blog", "brandhub"):
        for u in re.findall(r'href="([^"]+)"', html):
            if re.search(r"(?:%[0-9a-fA-F]{2}){10,}", u):
                rep.err("WAF_ENCODED", f"רצף 10+ %XX ב-href — WAF חוסם; ווידג'ט Elementor מחייב URL עברי גולמי (decode בלבד): {u[:90]}")

FORBIDDEN_ANCHORS = {"כאן", "לחץ כאן", "לחצו כאן", "למידע נוסף", "קישור", "קרא עוד", "קראו עוד"}

# הכרעת גיל 2026-08-16: כל עמוד באתרים מתורגם לכמה שפות, ועמוד מתורגם הוא
# אותו עמוד. /en/brands/amana-service/ ו-/ru/brands/moulinex-service/ קיימים
# בפועל ב-GSC. לכן כל בדיקה שנוגעת בנתיב מנרמלת קודם את קידומת השפה.
LANG_PREFIX = re.compile(r"^/(?:en|ru|ar|fr)(?=/)", re.I)


def base_brand_path(url, cfg):
    """נתיב /brands/... מנורמל: בלי דומיין, בלי קידומת שפה, בלי סלאש סוגר."""
    p = re.sub(r"^https?://", "", url.strip(), flags=re.I)
    if p.lower().startswith(cfg["domain"]):
        p = p[len(cfg["domain"]):]
    p = p.split("?")[0].split("#")[0]
    if not p.startswith("/"):
        p = "/" + p
    p = LANG_PREFIX.sub("", p)
    return "/" + p.strip("/").lower() + "/"


def check_links(html, rep, site, doc_type):
    cfg = SITES[site]
    # --- משמעת anchor (v1.3.0) ---
    anchors = [(u, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", t)).strip())
               for u, t in re.findall(r'<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.S)]
    seen = {}
    for u, t in anchors:
        if cfg["domain"] not in u and not u.startswith("/"):
            continue
        if t in FORBIDDEN_ANCHORS:
            rep.err("ANCHOR_FORBIDDEN", f"עוגן אסור \"{t}\" — עוגן חייב להיות תיאורי בשפת לקוח: {u[:70]}")
        key = (t, u)
        seen[key] = seen.get(key, 0) + 1
    for (t, u), n in seen.items():
        if n > 1 and t:
            rep.warn("ANCHOR_DUPLICATE", f"אותו עוגן \"{t[:40]}\" לאותו יעד {n} פעמים — לגוון ניסוח")
    # --- תקציב קישורים (v1.3.0, blog בלבד) ---
    if doc_type == "blog":
        n_int = len([1 for u, _ in anchors if cfg["domain"] in u or u.startswith("/")])
        if n_int < 4 or n_int > 14:
            rep.warn("LINK_BUDGET", f"{n_int} קישורים פנימיים — מחוץ לטווח 4-14 (תקציב גוף 4-7 + cluster/brand-hub/CTA)")
    urls = set(re.findall(r'(?:href|src)="([^"]+)"', html))
    urls |= set(re.findall(r'"url"\s*:\s*"([^"]+)"', html))
    for u in urls:
        low = u.lower()
        for d in FORBIDDEN_DOMAINS:
            if d in low:
                rep.err("FORBIDDEN_SOURCE", f"מקור אסור ({d}): {u[:90]}")
        for p in cfg["forbidden_paths"]:
            if p in low and "/brands/" not in low:
                rep.err("FORBIDDEN_LINK", f"קישור אסור באתר {site}: {u[:90]}")
        if cfg["forbidden_pc"] and "/product-category/" in low and cfg["domain"] in low:
            rep.err("FORBIDDEN_PC", f"product-category אסור בפלרום: {u[:90]}")
        # v1.12.0: MAROM_PC_LINK נמחק. הכלל טען ש-product-category במרום הוא
        # "כמעט תמיד 301/404", וזה שגוי: 420 עמודים, 308,604 חשיפות, 12,847
        # קליקים, 73 מהם במיקום 1-3 (/product-category/sharp/ לבדו 1,520
        # קליקים במיקום 1.0). הכלל חסם 308K כדי להגן על מוסכמה שמחזיקה 11K,
        # ו-preflight המליץ בדיוק על העמודים שהוא חסם — חזרה של כשל v8.12.
        # הבעיה האמיתית שהוא נועד לפתור, כתובות מומצאות, מכוסה במלואה
        # ב-link_audit שנכנס באותה גרסה ומחייב check_url 200 חי לכל קישור.
        if cfg.get("allowed_brand_links") is not None and "/brands/" in low:
            if base_brand_path(u, cfg) not in cfg["allowed_brand_links"]:
                rep.err("BRAND_LINK_UNKNOWN",
                        f"קישור /brands/ שאינו ברשימת עמודי המותג המאושרים של {site}. "
                        f"בדוק כתיב או הוסף לרשימה: {u[:90]}")
        if ".xml" in low and "sitemap" in low:
            rep.err("XML_SITEMAP", f"sitemap XML אסור — HTML בלבד ({cfg['sitemap_ok']}): {u[:90]}")
        if "myarea." in low and not re.search(r"/login/?$", low):
            rep.err("CTA_LOGIN", f"קישור myarea בלי /login/ בסוף — יעד CTA אחיד חובה: {u[:90]}")
        for other, ocfg in SITES.items():
            if other != site and ocfg["domain"] in low:
                rep.warn("CROSS_SITE_LINK", f"קישור לדומיין של אתר אחר ({other}): {u[:90]}")
    # link_audit: כל קישור פנימי חייב אימות check_url חי (200 + canonical זהה) לפני הגשה.
    # HTTP ישיר מהסנדבוקס חסום ב-WAF (403), לכן האימות דרך WooCommerce MCP check_url.
    # זו דרישת פרוטוקול חוסמת — קישור לא מאומת = לא מגישים (כלל גיל: מקור לא מאומת = לא קיים).
    internal = sorted({u for u in re.findall(r'href="([^"#][^"]*)"', html)
                       if cfg["domain"] in u})
    if internal:
        rep.note("link_audit — חובה check_url חי (200 + canonical זהה) לכל קישור פנימי לפני הגשה:")
        for i, u in enumerate(internal, 1):
            rep.note(f"   [{i}] {u}")
        rep.note("   ↑ אמת כל אחד ב-check_url. product-category במרום = כמעט תמיד שגוי.")

def check_terms(html, rep, doc_type):
    text = visible_text(html)
    for bad, good in TERMS_ERROR.items():
        for m in re.finditer(heb_bound(bad), text):
            rep.err("TERM", f"מונח אסור \"{bad}\" => \"{good}\"")
    for bad, good in TERMS_WARN.items():
        for m in re.finditer(heb_bound(bad), text):
            rep.warn("TERM_CTX", f"מונח חשוד \"{bad}\" — {good}")
    for m in re.finditer(heb_bound("מוסך"), text):
        rep.err("TERM_GARAGE", "\"מוסך\" אסור למוצרי חשמל => מעבדת שירות / מעבדת תיקונים / טכנאי")
    if doc_type == "product":
        for m in re.finditer(heb_bound("חיקוי"), text):
            rep.err("TERM_IMITATION", "\"חיקוי\" אסור בדפי מוצר (PPM) => \"חלק לא מקורי\" או \"תחליף לא מאושר\"")

def check_expert(html, rep, site):
    cfg = SITES[site]
    text = visible_text(html) + " " + " ".join(
        re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, flags=re.S | re.I))
    for wrong in cfg["wrong_experts"]:
        pat = rf"(?<![{HEB_RANGE}]){re.escape(wrong)}(?![{HEB_RANGE}])"
        if re.search(pat, text):
            correct = cfg["expert"] or "אין מומחה נקוב — עוגן ארגוני בלבד"
            rep.err("EXPERT", f"שם מומחה שגוי לאתר {site}: \"{wrong}\" (נכון: {correct})")
    # v1.13.0: אתר בלי מומחה נקוב מאומת אינו מייצר ישות Person.
    # ישות אדם בלי jobTitle ובלי sameAs אינה E-E-A-T, היא ישות שאי אפשר
    # לאמת ולכן אי אפשר לצטט. author מצביע על Organization במקומה.
    if cfg["author_org_only"]:
        for blob in re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, flags=re.S | re.I):
            if re.search(r'"@type"\s*:\s*"Person"', blob):
                rep.err("PERSON_ENTITY_FORBIDDEN",
                        f"ישות Person ב-@graph של {site}. לאתר אין מומחה נקוב מאומת, "
                        f"ו-author חייב להצביע על #content-organization")
            if re.search(r'"author"\s*:\s*\{[^}]*#content-author', blob):
                rep.err("AUTHOR_NOT_ORG",
                        f"author מצביע על #content-author ב-{site}. "
                        f"חייב להצביע על #content-organization")

def check_phones(html, rep, site):
    cfg = SITES[site]
    for bad in cfg["phone_bad"]:
        if bad in html:
            rep.err("PHONE", f"טלפון אסור {bad} (נכון: {cfg['phone_ok'][0]})")
    # v1.5.0: שתי הצורות תקפות במרום, אבל *2620 הוא הקנוני לתוכן חדש (הכרעת גיל 2026-07-05)
    if site == "marom" and "2620*" in html:
        rep.warn("PHONE_CANON", 'נמצא "2620*" — אינו שגוי, אבל הצורה הקנונית לתוכן חדש היא "*2620"')

def check_brand_scope(html, rep, site):
    text = visible_text(html)
    h1 = " ".join(re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I))
    title = " ".join(re.findall(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I))
    head = re.sub(r"<[^>]+>", " ", h1 + " " + title)
    if site == "marom":
        # "בקו" העברי דו-משמעי: מותג Beko או צירוף ב+קו ("המתנה בקו", "בקושי").
        # מזהים מותג רק כש: (א) Beko לטיני (חד-משמעי), או
        # (ב) "בקו" צמוד למונח מכשיר/שירות (מקרר/מכונה/תנור/מדיח/שירות/מותג/דגם).
        _dev = r"מקרר|מכונ|תנור|מדיח|מקפיא|שירות|מותג|דגם|חלקי|תיקון"
        beko_re = (
            r"(?<![A-Za-z])Beko(?![A-Za-z])"
            r"|בקו\s+(?:" + _dev + r")"
            r"|(?:" + _dev + r")\s+בקו(?![א-ת])"
        )
        if re.search(beko_re, head, flags=re.I):
            rep.err("BRAND_BEKO", "תוכן Beko במרום אסור (כבר לא שירות רשמי)")
        elif re.search(beko_re, text, flags=re.I):
            rep.warn("BRAND_BEKO", "אזכור Beko בגוף תוכן מרום — לוודא שאין claim לשירות רשמי")
        if re.search(r"דלונגי|DeLonghi|De'Longhi", text, flags=re.I):
            for para in re.split(r"</p>|</h[1-6]>|\n\n", visible_text(html)):
                if re.search(r"מכונ(ת|ות)\s+(ה)?קפה", para) and "שירות רשמי" in para:
                    rep.err("DELONGHI_COFFEE", "claim של \"שירות רשמי\" למכונות קפה דלונגי — מרום מתקנת אך לא רשמית (Brimag היבואן)")
        # מקרר+דלונגי: יורה רק כשהשניים באותה פסקת תוכן (כמו כלל COFFEE).
        # מונע false-positive מ"מקרר" בעמוד מותג אחר + "דלונגי" ברשימת מותגים/schema.
        for para in re.split(r"</p>|</h[1-6]>|</li>|\n\n", visible_text(html)):
            if re.search(r"מקרר", para) and re.search(r"דלונגי|DeLonghi", para, flags=re.I):
                rep.warn("DELONGHI_FRIDGE", "מקרר + דלונגי באותה פסקה — אין מקררים בליין דלונגי ישראל, לוודא")
                break
    if site == "plrom":
        if re.search(r"אלקטרה|Electra", head, flags=re.I):
            rep.err("BRAND_ELECTRA", "תוכן אלקטרה בפלרום אסור")
        elif re.search(r"אלקטרה|Electra", text, flags=re.I):
            rep.warn("BRAND_ELECTRA", "אזכור אלקטרה בגוף תוכן פלרום — לבדוק הקשר")

def check_jsonld(html, rep, site, doc_type):
    cfg = SITES[site]
    blocks = re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, flags=re.S | re.I)
    if not blocks:
        if doc_type != "product":
            rep.warn("SCHEMA_MISSING", "לא נמצא JSON-LD — לוודא שזה מכוון")
        return
    for i, b in enumerate(blocks, 1):
        try:
            data = json.loads(b)
        except json.JSONDecodeError as e:
            rep.err("SCHEMA_PARSE", f"JSON-LD בלוק {i} לא נפרס: {e}")
            continue
        graph = data.get("@graph", [data]) if isinstance(data, dict) else data
        if not isinstance(graph, list):
            graph = [graph]
        # --- רזולוציית @id (knowledge graph שלם) ---
        ids = {e.get("@id") for e in graph if isinstance(e, dict) and e.get("@id")}
        def refs(o):
            if isinstance(o, dict):
                if set(o) == {"@id"}:
                    yield o["@id"]
                else:
                    for v in o.values():
                        yield from refs(v)
            elif isinstance(o, list):
                for v in o:
                    yield from refs(v)
        for r in refs(graph):
            if r not in ids:
                rep.err("SCHEMA_ID", f"@id מאוזכר אך לא מוגדר ב-@graph: {r}")
        for ent in graph:
            if not isinstance(ent, dict):
                continue
            t = ent.get("@type", "")
            types = t if isinstance(t, list) else [t]
            eid = ent.get("@id")
            if eid and any(eid.endswith(suf) for suf in YOAST_GRAPH_ID_SUFFIXES):
                rep.err("SCHEMA_ID_YOAST_COLLISION",
                        f"@id \"{eid}\" מסתיים בסיומת קבועה של ה-@graph האוטומטי של Yoast "
                        f"({'/'.join(YOAST_GRAPH_ID_SUFFIXES)}) — מתנגש בין שני <script> ld+json באותו עמוד "
                        f"וגורם ל-Rich Results Test לדווח breadcrumb/schema כלא תקין (אומת חי 2026-07-16). "
                        f"מוסכמה: content-machine→#content-*, brand-hub-machine→#brandhub-*")
            if "Product" in types and doc_type == "blog":
                rep.err("SCHEMA_PRODUCT_BLOG", "ישות Product ב-@graph של בלוג — אסורה (v7.15): דף המוצר מחזיק את ה-Product/offer; בבלוג mentions=Brand בלבד")
            if "Product" in types and "offers" not in ent and doc_type != "blog":
                rep.err("SCHEMA_OFFERS", "Product schema בלי offers block (שגיאת GSC ידועה, v1.12)")
            if "Product" in types and "offers" in ent:
                off = ent["offers"]
                offs = off if isinstance(off, list) else [off]
                for o in offs:
                    if isinstance(o, dict) and o.get("priceCurrency") not in (None, "ILS"):
                        rep.err("SCHEMA_CURRENCY", f"priceCurrency={o.get('priceCurrency')} — חייב ILS")
            if "FAQPage" in types:
                h3s = {re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip()
                       for h in re.findall(r"<h3[^>]*>(.*?)</h3>", html, flags=re.S)}
                for q in ent.get("mainEntity", []):
                    qn = re.sub(r"\s+", " ", q.get("name", "")).strip()
                    if qn and qn not in h3s:
                        rep.err("SCHEMA_FAQ_H3", f"שאלת FAQPage לא זהה ל-H3 בעמוד: {qn[:60]}")
            if doc_type in ("blog", "brandhub") and ("Article" in types or "WebPage" in types):
                spk = json.dumps(ent.get("speakable", {}), ensure_ascii=False)
                if "direct-answer" not in spk:
                    rep.warn("SPEAKABLE_MISSING", f"ישות {types[0]} בלי speakable שמצביע על .direct-answer (v7.4/v1.x)")
            if "Article" in types and ent.get("dateModified"):
                lu = re.search(r'class="last-updated"[^>]*>(.*?)</', html, flags=re.S)
                if lu:
                    y, mo, dy = (int(x) for x in ent["dateModified"][:10].split("-"))
                    nums = {int(n) for n in re.findall(r"\d+", lu.group(1))}
                    if not {y, mo, dy} <= nums:
                        rep.err("SCHEMA_DATE", f"dateModified ({ent['dateModified'][:10]}) לא תואם את .last-updated בטקסט")
            if "LocalBusiness" in types:
                addr = json.dumps(ent.get("address", {}), ensure_ascii=False)
                tel = str(ent.get("telephone", ""))
                if cfg["nap_street"] not in addr:
                    rep.err("NAP_ADDR", f"כתובת LocalBusiness לא תואמת NAP ({cfg['nap_street']}, {cfg['nap_city']})")
                if cfg["phone_ok"] and not any(p in tel for p in cfg["phone_ok"]):
                    rep.err("NAP_PHONE", f"טלפון LocalBusiness \"{tel}\" לא תואם NAP (נכון: {cfg['phone_ok'][0]})")

def check_wcag(html, rep):
    if "<article" not in html and "<style" not in html:
        return  # Markdown / לא HTML
    if len(re.findall(r"<h1[\s>]", html)) != 1:
        rep.err("WCAG_H1", "חייב H1 אחד בדיוק")
    levels = [int(t) for t in re.findall(r"<h([1-6])", html)]
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            rep.err("WCAG_HEADING_SKIP", f"דילוג בהיררכיית כותרות: h{a} => h{b}")
            break
    for img in re.findall(r"<img[^>]*>", html):
        if "alt=" not in img:
            rep.err("WCAG_IMG_ALT", f"img בלי alt: {img[:60]}")
    for ifr in re.findall(r"<iframe[^>]*>", html):
        if "title=" not in ifr:
            rep.err("WCAG_IFRAME_TITLE", "iframe בלי title")
    for th in re.findall(r"<th(?![a-z])[^>]*>", html):
        if "scope=" not in th:
            rep.err("WCAG_TH_SCOPE", f"th בלי scope: {th[:50]}")
    if "<table" in html and "table-wrap" not in html:
        rep.err("WCAG_TABLE_WRAP", "טבלה בלי עטיפת table-wrap")

def check_content_quality(html, rep, doc_type):
    """Zero Hallucination + מבנה (v7.9/v7.12/v1.14, נקלט מהסקילים)."""
    body = visible_text(html)
    for m in re.finditer(r".{0,35}\d+\s*%.{0,35}", body):
        rep.warn("PERCENT_CLAIM", f'אחוז בטקסט: "...{m.group().strip()}..." — ודא מקור מאומת; "לדברי הצוות" אינו מקור, אחרת "רוב/לרוב" בלי מספר')
    # מקף בקצה הוא פורמט אמיתי במק"טי Ralco/מרום (אומת חי מול MCP: 89-04-02630-00-) — לכן WARN, לא ERROR
    for sku in re.findall(r'"sku":\s*"([^"]*)"', html):
        if sku != sku.strip() or sku.endswith("-") or sku.startswith("-"):
            rep.warn("SKU_TRUNC", f'מק"ט עם מקף/רווח בקצה: {sku!r} — פורמט Ralco תקין במרום, אבל אמת מול MCP שזה המק"ט המלא')
    if doc_type in ("blog", "brandhub"):
        toc = set(re.findall(r'href="#([^"]+)"', html))
        for hid in re.findall(r'<h2 id="([^"]+)"', html):
            if toc and hid not in toc:
                rep.err("TOC_MISSING", f'H2 id="{hid}" חסר ב-TOC')

def check_responsive(html, rep, doc_type):
    """גייט responsive + sticky-cta — brandhub בלבד (לקח דלונגי v1.11)."""
    if doc_type != "brandhub":
        return
    css = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.S | re.I))
    if not css:
        return
    if "service-grid" in html and not re.search(r"service-grid\s*\{\s*grid-template-columns:\s*1fr", css):
        rep.err("RESPONSIVE_GRID", "חסר .service-grid{grid-template-columns:1fr} ב-@media(max-width) — הגריד יישאר 3 עמודות במובייל")
    if "sticky-cta" in html:
        if not re.search(r"sticky-cta\s*\{\s*display:\s*none", css):
            rep.err("RESPONSIVE_STICKY", "חסר .sticky-cta{display:none} ב-@media(min-width:768px) — ה-sticky יופיע גם בדסקטופ")
        seg = re.search(r'class="sticky-cta".*?</div>', html, flags=re.S)
        if seg and "&#9742;" not in seg.group(0):
            rep.err("PHONE_ENTITY", "sticky-cta בלי &#9742; בקישור החיוג — חובה entity, לא טקסט ולא SVG")
    if css.count("@media") < 3:
        rep.err("RESPONSIVE_MEDIA", f"רק {css.count('@media')} בלוקי @media — ה-CSS חסר responsive (תקין: 4)")

def check_video(html, rep):
    for m in re.finditer(r'class="[^"]*video-container[^"]*"', html):
        seg = html[m.start():m.start() + 1200]
        src = re.search(r'src="([^"]*)"', seg)
        if not src or not re.search(r"youtube\.com/embed/[\w-]{6,}", src.group(1)):
            rep.err("VIDEO_PLACEHOLDER", "video-container בלי embed תקין — הכלל: אין וידאו רשמי מאומת = למחוק את הבלוק כולו")
    if re.search(r"PLACEHOLDER|VIDEO_ID_HERE|YOUR_VIDEO", html):
        rep.err("PLACEHOLDER", "placeholder גולמי נשאר בקובץ")

def check_yoast(html, rep, doc_type, keyword=None):
    """מדדי Yoast בקוד (v7.12 — לא ספירה ידנית). ERROR רק על משפטים; השאר WARN/דוח."""
    text = re.sub(r"\s+", " ", visible_text(html)).strip()
    words = re.findall(rf"[{HEB_RANGE}]+", text)
    sents = [s.strip() for s in re.split(r"(?<=[.!?:])\s+", text) if len(s.split()) > 2]
    heb = [s for s in sents if len(re.findall(rf"[{HEB_RANGE}]", s)) > 10]
    rep.note(f"מילים בעברית: {len(words)} | משפטים: {len(heb)}")
    if doc_type in WORD_TARGETS and heb:
        lo, hi = WORD_TARGETS[doc_type]
        if not (lo * 0.95 <= len(words) <= hi * 1.05):
            rep.warn("YOAST_WORDS", f"{len(words)} מילים — יעד {doc_type}: {lo}-{hi}")
    if heb:
        long_s = [s for s in heb if len(s.split()) > 15]
        pct = round(100 * len(long_s) / len(heb))
        rep.note(f"משפטים ארוכים (>15 מילים): {len(long_s)} ({pct}%)")
        if pct > 25:
            rep.warn("YOAST_LEN", f"{pct}% מהמשפטים מעל 15 מילים (Yoast עברית) — לקצר לפני הגשה")
        tr = sum(1 for s in heb if any(re.search(heb_bound(t) if " " not in t else re.escape(t), s) for t in TRANSITIONS))
        tp = round(100 * tr / len(heb))
        rep.note(f"transitions: {tp}% (יעד 30-45)")
        if tp < 30 or tp > 45:
            rep.warn("YOAST_TRANS", f"transitions {tp}% — מחוץ ליעד 30-45%")
        pas = [s[:60] for s in heb if any(re.search(heb_bound(p) if " " not in p else re.escape(p), s) for p in PASSIVE_HINTS)]
        if pas:
            rep.note(f"מועמדי פסיבי לשיפוט ידני ({len(pas)}, יעד ≤10% = {len(heb) // 10}):")
            for p in pas[:12]:
                rep.note(f"   • {p}")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S)
    if h1:
        h1t = re.sub(r"<[^>]+>", "", h1.group(1)).strip()
        rep.note(f"H1: {len(h1t)} תווים (עד 65/70)")
        if len(h1t) > 70:
            rep.warn("H1_LEN", f"H1 באורך {len(h1t)} תווים — מעל 70")
        if keyword and keyword.split()[0] not in " ".join(h1t.split()[:3]):
            rep.warn("H1_KEYWORD", "מילת המפתח לא ב-3 המילים הראשונות של ה-H1")
    if keyword:
        kw_words = keyword.split()
        kd_full = round(100 * text.count(keyword) * len(kw_words) / max(len(words), 1), 2)
        rep.note("צפיפות ביטוי מלא: " + str(kd_full) + "%")
        # v1.6.0: ביטוי בן 3+ מילים לא מגיע ל-1% בעברית טבעית. היעד נמדד על ראש הביטוי.
        head = " ".join(kw_words[:2])
        kd_head = round(100 * text.count(head) * len(head.split()) / max(len(words), 1), 2)
        rep.note("צפיפות ראש הביטוי (" + head + "): " + str(kd_head) + "% — יעד 1-2")
        if len(kw_words) >= 3 and not (0.8 <= kd_head <= 2.5):
            rep.warn("KEYWORD_DENSITY", "ראש הביטוי " + head + " ב-" + str(kd_head) + "% — יעד 1-2%")
        for tok in kw_words:
            if len(tok) > 2:
                rep.note("   • כיסוי " + tok + ": " + str(text.count(tok)) + " מופעים")

INTERNAL_TOOLS = [
    "Search Console", "search console", "סרץ' קונסול", "Bing Webmaster", "bing webmaster",
    "GSC", "WooCommerce", "woocommerce", "MCP", "content-ledger", "Autocomplete", "autocomplete",
]

def check_sources_internal(html, rep, doc_type):
    """v1.5.0: כלי מחקר פנימיים אסורים ברשימת המקורות הגלויה."""
    if doc_type == "product":
        return
    for m in re.finditer(r'<div class="sources-list".*?</div>', html, flags=re.S | re.I):
        block = visible_text(m.group())
        for tool in INTERNAL_TOOLS:
            if tool in block:
                rep.err("SOURCES_INTERNAL_TOOL",
                        f'כלי מחקר פנימי ברשימת המקורות: "{tool}" — מקורות הם ליצרן/תקן/ניסיון שטח, לא לכלי המדידה שלנו')
                break

def check_connectors(html, rep, doc_type):
    """v1.5.0: מחבר ניגוד תלוש + גודש מילות קישור."""
    if doc_type == "product":
        return
    text = re.sub(r"\s+", " ", visible_text(html)).strip()
    for m in re.finditer(r"([^.!?:;]{0,80}),\s*(אך|אבל|אולם|ואילו)\s", text):
        clause = m.group(1).strip()
        if 0 < len(clause.split()) < 4:
            rep.warn("DANGLING_CONNECTOR",
                     f'מחבר ניגוד "{m.group(2)}" אחרי פסוקית של {len(clause.split())} מילים: "...{clause}, {m.group(2)}..." — בדוק שהמשפט שלם תחבירית')
    sents = [x.strip() for x in re.split(r"(?<=[.!?:])\s+", text) if len(x.split()) > 2]
    heb = [x for x in sents if len(re.findall(rf"[{HEB_RANGE}]", x)) > 10]
    # מחברי שיח בלבד. "כדי/מכיוון ש/אחרי ש/בגלל ש/מפני ש/למרות ש" הם משעבדים טבעיים בעברית
    # ואינם מעידים על גודש — הכללתם ייצרה רעש על טקסט תקין.
    stack_pool = [t for t in TRANSITIONS if t not in
                  ("כדי", "מכיוון ש", "אחרי ש", "בגלל ש", "מפני ש", "למרות ש")]
    for x in heb:
        hits = [t for t in stack_pool
                if re.search(heb_bound(t) if " " not in t else re.escape(t), x)]
        if len(hits) >= 2:
            rep.warn("TRANSITION_STACK", f'{len(hits)} מילות קישור באותו משפט ({", ".join(hits[:3])}): "{x[:70]}..."')
    paras = [visible_text(m.group(1)).strip() for m in re.finditer(r"<p[^>]*>(.*?)</p>", html, flags=re.S | re.I)]
    paras = [x for x in paras if len(x.split()) > 8]
    if len(paras) >= 6:
        opens = sum(1 for x in paras
                    if any(x.startswith(t) or x.split(" ")[0].startswith(t) for t in TRANSITIONS))
        pct = round(100 * opens / len(paras))
        rep.note(f"פסקאות שנפתחות במילת קישור: {pct}%")
        if pct > 50:
            rep.warn("TRANSITION_STACK", f"{pct}% מהפסקאות נפתחות במילת קישור — קריאה מכנית, גוון את הפתיחות")

def check_competitor_sources(html, rep, doc_type):
    """v1.6.0: אסור לצטט/לקשר/לאזכר ספק לידים מתחרה."""
    if doc_type == "product":
        return
    low = html.lower()
    for d in COMPETITOR_DOMAINS:
        if d in low and not any(g in low for g in GROUP_ASSETS):
            rep.err("COMPETITOR_SOURCE", "דומיין מתחרה בתוכן: " + d +
                    " — כרייה למחקר מותרת, ציטוט או קישור אסורים")
    text = visible_text(html)
    for n in COMPETITOR_NAMES:
        if re.search(heb_bound(n), text):
            rep.err("COMPETITOR_SOURCE", "אזכור ספק לידים מתחרה בשם: " + n +
                    " — החלף במקור יצרן, תקן או ניסיון מעבדה")


def check_org_schema(html, rep, site, doc_type):
    """v1.6.0: Organization היא ישות יציבה ברמת האתר — אסור דריפט בין מאמרים."""
    if doc_type == "product" or not site:
        return
    cfg = SITES[site]
    pat = re.compile(r'\{[^{}]*"@type":\s*"Organization".*?\}(?=\s*[,\]])', re.S)
    for b in re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, re.S | re.I):
        m = pat.search(b)
        if not m:
            continue
        org = m.group()
        if not any(ph in org for ph in cfg["phone_ok"]):
            rep.err("ORG_SCHEMA_DRIFT", "Organization בלי telephone תקין")
        if cfg["domain"] not in org:
            rep.err("ORG_SCHEMA_DRIFT", "Organization בלי url של " + cfg["domain"])
        for req in cfg.get("org_sameas", []):
            if req not in org:
                rep.err("ORG_SCHEMA_DRIFT", "Organization חסר sameAs קנוני: " + req +
                        " — הבלוק נלקח verbatim מקובץ הפרויקט")
        return
    if doc_type in ("blog", "brandhub"):
        rep.err("ORG_SCHEMA_DRIFT", "אין ישות Organization ב-@graph")


LISTICLE_PAT = [
    r"תקלות\s+נפוצות", r"בעיות\s+נפוצות", r"סיבות\s+נפוצות", r"טעויות\s+נפוצות",
    r"\d+\s+(סיבות|דרכים|טיפים|שלבים|דברים|תקלות|בעיות)",
]


# "מוביל" הוא גם פועל תקין ("מוביל את הצוות"). רק הצורה המיודעת היא סופרלטיב שיווקי.
SUPERLATIVES = ["המוביל", "המובילה", "מהפכני", "מהפכנית", "הטוב ביותר", "הטובה ביותר",
                "חסר תקדים", "חסרת תקדים", "ברמה הגבוהה ביותר", "פריצת דרך",
                "ללא תחרות", "הכי טוב בעולם", "מספר 1 בישראל", "אין תחליף"]


def check_plrom_name(html, rep, site, doc_type):
    """v1.8.0: "שירות פלרום" הוא השם. "חברת פלרום" אסור (project-plrom)."""
    if site != "plrom":
        return
    if re.search(heb_bound("חברת פלרום"), visible_text(html)):
        rep.err("TERM_PLROM_NAME", 'השם הוא "שירות פלרום", לא "חברת פלרום"')


def check_superlatives(html, rep, doc_type):
    """v1.8.0: שיווקיות ריקה. אסורה במאסטר-פרומפט ולא נאכפה עד היום."""
    t = visible_text(html)
    for s in SUPERLATIVES:
        if re.search(heb_bound(s) if " " not in s else re.escape(s), t):
            rep.err("SUPERLATIVE", f'שיווקיות אסורה: "{s}" — החלף בעובדה מאומתת')


def check_focus_outline(html, rep, doc_type):
    """v1.8.0: outline: none בלי חלופה שובר ניווט מקלדת."""
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S | re.I))
    if not style:
        return
    for m in re.finditer(r"([^{}]*:focus[^{}]*)\{([^{}]*)\}", style):
        if re.search(r"outline:\s*(none|0)", m.group(2)) and "box-shadow" not in m.group(2):
            rep.err("FOCUS_OUTLINE", f"{m.group(1).strip()[:40]} מסיר outline בלי חלופה")
    if ":focus" not in style:
        rep.warn("FOCUS_OUTLINE", "אין מצב :focus-visible ב-CSS — ניווט מקלדת לא מסומן")


def check_pref_strip_order(html, rep, doc_type):
    """v1.8.0: רצועת bh-pref-mini אחרונה בזרימה. לעולם לא לפני ה-CTA הכספי."""
    i = html.find("bh-pref-mini")
    if i < 0:
        return
    for cls, name in (("cta-box", "cta-box"), ("author-bio", "author-bio")):
        j = html.find(cls)
        if 0 <= j > i or (j > i):
            rep.err("PREF_STRIP_ORDER", f"bh-pref-mini מופיע לפני {name} — חייב להיות אחרון")


def check_permalink_case(html, rep, doc_type):
    """v1.8.0: uppercase ב-%XX גורם 404. ה-permalink מועתק verbatim מ-MCP."""
    # permalink מ-MCP הוא lowercase percent-encoded. כל אות גדולה ב-%XX = קידוד מחדש = 404.
    for m in re.finditer(r'href="([^"]*%[0-9A-Fa-f]{2}[^"]*)"', html):
        if re.search(r"%[0-9A-Fa-f]*[A-F]", m.group(1)):
            rep.err("PERMALINK_CASE",
                    f"%XX עם אות גדולה בקישור (גורם 404, קודד lowercase): {m.group(1)[:55]}")


def check_h1_listicle(html, rep, doc_type):
    """v1.7.0: דפוס ליסטיקל ב-H1. נדחה שלוש פעמים; מועדף הד לשאילתה."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    if not m:
        return
    h1 = visible_text(m.group(1)).strip()
    for pat in LISTICLE_PAT:
        if re.search(pat, h1):
            rep.warn("H1_LISTICLE",
                     'H1 בדפוס ליסטיקל: "' + h1[:60] + '" — עבור לפורמט הד-לשאילתה. '
                     'מספר מותר רק אם הוא נושא משמעות')
            return


BRAND_ENTITIES = {
    "שארפ": ["Q53227", "Sharp_Corporation"],
    "מילה": ["Q695230", "wiki/Miele"],
    "קונסטרוקטה": ["Q326933", "Constructa"],
    "מג'ימיקס": ["Q3276973", "wiki/Magimix"],
    "מגימיקס": ["Q3276973", "wiki/Magimix"],
    "גגנאו": ["Gaggenau_Hausger"],
    "דלונגי": ["De%27_Longhi", "De'_Longhi"],
    "האייר": ["wiki/Haier"],
    "זנוסי": ["wiki/Zanussi"],
    "בוש": ["Q614920", "BSH_Hausger"],
    "סימנס": ["Q614920", "BSH_Hausger"],
    "נף": ["Q326933", "Neff_GmbH"],
    "קיטשן אייד": ["Q1743850", "wiki/KitchenAid"],
    "קיצ'נאייד": ["Q1743850", "wiki/KitchenAid"],
    "באוקנכט": ["Q467116", "Bauknecht"],
    "בלומברג": ["Q884951", "Blomberg"],
    "טפאל": ["wiki/Tefal"],
    "מולינקס": ["wiki/Moulinex"],
    "ברוויל": ["Breville_Group"],
}


def check_brand_sameas(html, rep, doc_type):
    """v1.10.0: Entity Disambiguation. הרישום המאומת: pal-state/brand-entities.md."""
    if doc_type == "product":
        return
    for m in re.finditer(r'\{[^{}]*"@type":\s*"Brand".*?\}', html, flags=re.S):
        blk = m.group()
        nm = re.search(r'"name":\s*"([^"]+)"', blk)
        if not nm:
            continue
        brand = nm.group(1).strip()
        keys = BRAND_ENTITIES.get(brand)
        if not keys:
            continue
        if not any(k in blk for k in keys):
            rep.warn("BRAND_SAMEAS_MISSING",
                     f'ישות Brand "{brand}" בלי sameAs לגרף הידע. '
                     f'ראה pal-state/brand-entities.md')
        if brand in ("בוש", "סימנס") and re.search(r"Robert_Bosch_GmbH|wiki/Siemens\b", blk):
            rep.err("BRAND_SAMEAS_WRONG",
                    f'"{brand}" מקושר לתאגיד האם ולא ליצרן מוצרי החשמל. הנכון: BSH (Q614920)')


# שאלות עם כוונה מסחרית. הקורא מחפש מספר, לא הפניה.
COMMERCIAL_Q = [
    "כמה עולה", "מה המחיר", "מה העלות", "כמה זה עולה", "כמה עולים",
    "כמה זמן לוקח", "תוך כמה זמן", "מתי מגיע", "כמה זמן ממתינים",
    "מה מחיר", "עלות ביקור", "מחיר ביקור", "כמה יעלה",
]
# ניסוחים שמחליפים מספר בהפניה. אלה הדגלים האדומים.
EVASION = [
    "תלוי בסוג", "תלוי במיקום", "משתנה בהתאם", "לקבלת הצעת מחיר",
    "פנו אלינו", "צרו קשר לקבלת", "נשמח לעדכן", "בהתאם לאבחון",
    "לפרטים נוספים פנו", "יימסר בשיחה",
]


def check_tel_format(html, rep, doc_type):
    """v1.11.1: href="tel:" עם מקפים אינו אמין בכל המכשירים."""
    for m in re.finditer(r'href="tel:([^"]+)"', html):
        v = m.group(1)
        if re.search(r"[-\s()]", v):
            rep.warn("TEL_FORMAT",
                     f'href="tel:{v}" מכיל מקפים. השתמש בספרות בלבד '
                     f'({re.sub(chr(92)+"D", "", v)}); הטקסט הגלוי יכול להישאר עם מקפים')


def check_evasive_answers(html, rep, doc_type):
    """
    v1.11.0: שאלה מסחרית בלי מספר בתשובה.
    הכלל אינו על ניסוח אלא על ערך: קורא שמחפש "כמה עולה טכנאי" ומקבל
    "העלות תלויה, פנו אלינו" חוזר לגוגל. זה מה שמייצר CTR של 0.25%.
    מחיר מאומת קיים בזיכרון לכל אתר — יש להשתמש בו.
    """
    if doc_type == "product":
        return
    blocks = re.findall(r"<h3[^>]*>(.*?)</h3>\s*(.*?)(?=<h[23]|</article|<div class=\"cta)",
                        html, flags=re.S | re.I)
    blocks += [(q, a) for q, a in re.findall(
        r'"name":\s*"([^"]*?)".{0,120}?"text":\s*"([^"]{20,})"', html, flags=re.S)]
    for q, a in blocks:
        qt = visible_text(q)
        if not any(c in qt for c in COMMERCIAL_Q):
            continue
        at = visible_text(a)
        # ש״ח בגרשיים עברי (U+05F4) ובגרש כפול ASCII — שניהם תקפים בתוכן קיים
        has_number = re.search(
            "\\d{2,}\\s*(?:₪|ש[\"\u05f4\u2033]ח|שקל)|₪\\s*\\d{2,}"
            "|\\d+\\s*(?:ימי עסקים|ימים|שעות|שבועות)", at)
        if has_number:
            continue
        why = next((e for e in EVASION if e in at), None)
        rep.err("EVASIVE_ANSWER",
                f'שאלה מסחרית בלי מספר בתשובה: "{qt[:55]}"'
                + (f' — ניסוח מתחמק: "{why}"' if why else "")
                + ". מחיר/זמן מאומת חייב להופיע. המאמר נועד להמיר")


def check_brand_hub_link(html, rep, site, doc_type):
    """v1.9.0: כל מאמר בלוג מזין את עמודי המותג שלנו, לא את עמודי השותפים."""
    if doc_type != "blog" or not site:
        return
    dom = SITES[site]["domain"]
    hubs = [u for u in re.findall(r'href="([^"]+)"', html)
            if "/brands/" in u.lower() and (dom in u or u.startswith("/brands/"))]
    if not hubs:
        rep.err("BRAND_HUB_MISSING",
                "אין קישור לעמוד מותג תחת /brands/. חובה אחד לפחות — "
                "זה הערוץ להעברת סמכות מעמודי השותפים אלינו")
    else:
        rep.note(f"קישורי brand hub: {len(hubs)}")


def check_bauknecht(html, rep, doc_type):
    """v1.6.1: כתיב מותג שגוי שמקורו בעמוד שירות ישן."""
    if re.search(heb_bound("באוכנט"), visible_text(html)):
        rep.err("TERM_BAUKNECHT", 'כתיב שגוי "באוכנט" — הכתיב בשוק ואצל היבואן ניופאן הוא "באוקנכט"')


def check_encoding_junk(html, rep):
    for ch in ("\ufffd",):
        if ch in html:
            rep.err("ENCODING", "תו replacement (�) — קידוד שבור")
    for m in re.finditer(r"[\u200e\u200f\u202a-\u202e]", html):
        rep.warn("BIDI_MARK", f"תו כיווניות נסתר בשורה {line_of(html, m.start())} — לוודא שהוא מכוון")

# ---------------------------------------------------------------- ניהול

def detect_site(html):
    counts = {s: html.count(c["domain"]) for s, c in SITES.items()}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else None

def detect_type(path, html):
    if str(path).endswith(".md"):
        return "product"
    # bh-pref-mini קיים גם בבלוגים — הזיהוי לפי סמנים ייחודיים של brandhub בלבד
    if any(k in html for k in ("diagnostic-box", "brand-grid", "sticky-cta", "brand-chip", "brands-index")):
        return "brandhub"
    return "blog"

def run(path, site=None, doc_type=None, keyword=None):
    html = Path(path).read_text(encoding="utf-8")
    html = unicodedata.normalize("NFC", html)
    rep = Report()
    site = site or detect_site(html)
    if site is None:
        rep.warn("SITE_UNKNOWN", "לא זוהה אתר — בדיקות per-site דולגו. העבר --site")
    doc_type = doc_type or detect_type(path, html)
    rep.note(f"pal-lint v{VERSION} | site={site or '?'} | type={doc_type} | {Path(path).name}")

    check_emdash(html, rep)
    check_terms(html, rep, doc_type)
    check_encoding_junk(html, rep)
    check_content_quality(html, rep, doc_type)
    check_sources_internal(html, rep, doc_type)
    check_competitor_sources(html, rep, doc_type)
    check_bauknecht(html, rep, doc_type)
    check_brand_hub_link(html, rep, site, doc_type)
    check_evasive_answers(html, rep, doc_type)
    check_tel_format(html, rep, doc_type)
    check_brand_sameas(html, rep, doc_type)
    check_h1_listicle(html, rep, doc_type)
    check_plrom_name(html, rep, site, doc_type)
    check_superlatives(html, rep, doc_type)
    check_focus_outline(html, rep, doc_type)
    check_pref_strip_order(html, rep, doc_type)
    check_permalink_case(html, rep, doc_type)
    check_connectors(html, rep, doc_type)
    check_yoast(html, rep, doc_type, keyword)
    if doc_type != "product":
        check_css(html, rep)
        check_backslash(html, rep)
        check_elementor_blockers(html, rep)
        check_percent_encoding(html, rep, doc_type)
        check_video(html, rep)
        check_wcag(html, rep)
        check_responsive(html, rep, doc_type)
    for d in FORBIDDEN_DOMAINS:
        if d in html.lower():
            rep.err("FORBIDDEN_SOURCE", f"אזכור מקור אסור: {d}")
    if site:
        check_links(html, rep, site, doc_type)
        check_expert(html, rep, site)
        check_phones(html, rep, site)
        check_brand_scope(html, rep, site)
        if doc_type != "product":
            check_jsonld(html, rep, site, doc_type)
            check_org_schema(html, rep, site, doc_type)
    return rep, site, doc_type

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--site", choices=list(SITES))
    ap.add_argument("--type", dest="doc_type", choices=["blog", "brandhub", "product"])
    ap.add_argument("--keyword")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not Path(a.file).exists():
        print(f"קובץ לא קיים: {a.file}", file=sys.stderr)
        sys.exit(2)
    rep, site, dt = run(a.file, a.site, a.doc_type, a.keyword)
    if a.json:
        print(json.dumps({"site": site, "type": dt, "errors": rep.errors,
                          "warnings": rep.warns, "info": rep.info,
                          "pass": not rep.errors}, ensure_ascii=False, indent=2))
    else:
        for n in rep.info:
            print(f"ℹ️  {n}")
        for w in rep.warns:
            print(f"⚠️  [{w['rule']}] {w['msg']}")
        for e in rep.errors:
            print(f"❌ [{e['rule']}] {e['msg']}")
        print(f"\nתוצאה: {'✅ ירוק — מותר להגיש' if not rep.errors else f'🔴 {len(rep.errors)} שגיאות — אסור להגיש'} | אזהרות: {len(rep.warns)}")
    sys.exit(0 if not rep.errors else 1)

if __name__ == "__main__":
    main()
