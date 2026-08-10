#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_postflight.py — כיסוי בדיקות ל-postflight.

למה זה קיים: עד 2026-08-10 `selftest.py` בדק רק את `pal_lint.py`.
`postflight.py` — 15 כללים, כולל כל הבדיקות מול ה-brief — לא נבדק בשום מקום.
זו הסיבה שבאג `_inherited_bg` (ניגודיות בלי פתרון ירושה) הגיע עד גיל
פעמיים ברצף: פעם אחת כשהבודק התעלם מירושה, ופעם שנייה כשהוא קיצץ
`::before`/`:hover` לפני החיפוש.

רץ ב-CI לצד selftest.py ו-test_flight.py. exit 1 בכשל.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import postflight as PO  # noqa: E402

FAILED = []


def reset():
    PO.ERRORS.clear()
    PO.WARNS.clear()
    PO.NOTES.clear()


def check(name, got, want):
    if got == want:
        print(f"✅ {name}")
    else:
        FAILED.append(f"{name}: קיבלתי {got!r}, ציפיתי {want!r}")


def rules(kind="ERRORS"):
    return {r for r, _ in (PO.ERRORS if kind == "ERRORS" else PO.WARNS)}


# ---------- ניגודיות ----------
TPL = """<style>
.cta-box { background: #140C3C; color: #fff; }
.cta-box h2 { color: #fff; }
.cta-box p { color: #CFC9F0; }
.cta-primary { background: #D01F26; color: #fff !important; }
.cta-primary:hover { background: #B81A21; color: #fff !important; }
.expert-tip { background: #FBEFD6; }
.expert-tip-title { color: #140C3C; }
.expert-tip-title::before { content: "x"; color: #140C3C; }
.blog-article a { color: #B81A21; }
</style><article><h1>x</h1></article>"""

reset()
PO.check_contrast(TPL)
check("ניגודיות: התבנית הרשמית נקייה", len(PO.ERRORS), 0)

reset()
PO.check_contrast(TPL.replace("</style>", ".bad{color:#CCCCCC;}</style>"))
check("ניגודיות: אפור חלש נתפס", "CONTRAST_RATIO" in rules(), True)

reset()
PO.check_contrast('<style>.x{background:#140C3C;} .x b{color:#333;}</style><article></article>')
check("ניגודיות: כהה על כהה בירושה נתפס", "CONTRAST_RATIO" in rules(), True)

check("ניגודיות: חישוב שחור/לבן", PO.contrast("#000000", "#ffffff"), 21.0)

# ---------- ציטוטים ----------
CIT = '<div class="citation"><p>x<cite>מקור: ראלקו</cite></p></div>'
reset()
PO.check_citations("<article>" + CIT * 3 + "</article>")
check("ציטוטים: שלוש קפסולות עוברות", len(PO.ERRORS), 0)

reset()
PO.check_citations("<article>" + CIT * 2 + "</article>")
check("ציטוטים: שתיים נחסמות", "CITATION_COUNT" in rules(), True)

reset()
PO.check_citations('<article><div class="citation"><p>x<cite></cite></p></div></article>')
check("ציטוטים: cite ריק לא נספר", "CITATION_COUNT" in rules(), True)

# ---------- SEO Title ----------
H1 = "<article><h1>מדיח בוש לא מנקז מים</h1></article>"
reset()
PO.check_seo_title(H1, "מדיח בוש לא מנקז? כך מטפלים | סי.אס.בי")
check("SEO Title תקין", len(PO.ERRORS), 0)

reset()
PO.check_seo_title(H1, "מדיח בוש לא מנקז מים")
check("SEO Title זהה ל-H1 נחסם", "SEO_TITLE" in rules(), True)

reset()
PO.check_seo_title(H1, "א" * 61)
check("SEO Title מעל 60 תווים נחסם", "SEO_TITLE" in rules(), True)

reset()
PO.check_seo_title(H1, None)
check("SEO Title חסר נחסם", "SEO_TITLE" in rules(), True)

# ---------- Hero ----------
BRIEF_HERO = {"products": [{
    "name": "פילטר מקורי למדיח בוש וסימנס", "price": "120",
    "image": "https://i/x.jpg",
    "permalink": "https://csb.co.il/product/פילטר-מקורי-למדיח-בוש-וסימנס/"}]}


def card(href, price="120 ₪", img="https://i/x.jpg",
         title="פילטר מקורי למדיח בוש וסימנס"):
    return (f'<a class="product-card" href="{href}">'
            f'<img class="product-card-img" src="{img}">'
            f'<span class="product-card-price">{price}</span>'
            f'<span class="product-card-title">{title}</span></a>')


reset()
PO.check_hero(card(BRIEF_HERO["products"][0]["permalink"]), BRIEF_HERO)
check("Hero: התאמה מלאה", len(PO.ERRORS), 0)

reset()
PO.check_hero(card("https://csb.co.il/product/פילטר-מקורי-למדיח-בוש-וסימנ/"), BRIEF_HERO)
check("Hero: slug חתוך = אזהרה ולא שגיאה",
      ("HERO_SLUG_DRIFT" in rules("WARNS"), len(PO.ERRORS)), (True, 0))

reset()
PO.check_hero(card(BRIEF_HERO["products"][0]["permalink"], price="99 ₪"), BRIEF_HERO)
check("Hero: מחיר שגוי נחסם", "HERO_MISMATCH" in rules(), True)

reset()
PO.check_hero(card(BRIEF_HERO["products"][0]["permalink"], img="https://i/other.jpg"),
              BRIEF_HERO)
check("Hero: תמונה שגויה נחסמת", "HERO_MISMATCH" in rules(), True)

reset()
PO.check_hero(card("https://csb.co.il/product/מוצר-אחר-לגמרי-שונה/"), BRIEF_HERO)
check("Hero: permalink זר נחסם", "HERO_MISMATCH" in rules(), True)

# ---------- נושא מאושר / Refresh ----------
BRIEF = {
    "allowed_topics": [{"query": "מדיח בוש לא מנקז מים", "video": None}],
    "refresh_queue": [{
        "url": "csb.co.il/שירות-בוש-כיצד-מזמינים-תיקון",
        "existing_h1": "שירות בוש: כיצד מזמינים תיקון?",
        "total_impressions": 73539,
        "gap_queries": [{"query": "טכנאי מדיח כלים בוש", "position": 14,
                         "impressions": 300}],
        "triggers": [{"query": "טכנאי מדיח כלים בוש", "impressions": 300}],
        "ranking_for": [], "frozen": ["URL"]}],
}

reset()
PO.check_topic("<article><h1>מדיח בוש לא מנקז מים: מה בודקים</h1></article>", BRIEF)
check("נושא: מ-allowed_topics עובר", len(PO.ERRORS), 0)

reset()
PO.check_topic("<article><h1>שירות בוש: כיצד מזמינים תיקון?</h1></article>", BRIEF)
check("נושא: Refresh לא נחסם (הבאג של v8.5)", len(PO.ERRORS), 0)

reset()
PO.check_topic("<article><h1>מתכון לעוגת שוקולד</h1></article>", BRIEF)
check("נושא: לא מאושר נחסם", "TOPIC_UNAUTHORIZED" in rules(), True)

today = date.today().isoformat()
REF_OK = (f'<article><h1>שירות בוש: כיצד מזמינים תיקון?</h1>'
          f'<p class="last-updated">עודכן: {today}</p>'
          f'<h2>טכנאי מדיח כלים בוש?</h2>'
          f'<a href="https://csb.co.il/שירות-בוש-כיצד-מזמינים-תיקון/">x</a></article>')
reset()
PO.check_refresh(REF_OK, BRIEF)
check("Refresh: תקין עובר", len(PO.ERRORS), 0)

reset()
PO.check_refresh(REF_OK.replace(today, "2023-01-01"), BRIEF)
check("Refresh: תאריך לא עודכן נחסם", "REFRESH_DATE" in rules(), True)

reset()
PO.check_refresh(REF_OK.replace("שירות-בוש-כיצד-מזמינים-תיקון/", "slug-חדש/"), BRIEF)
check("Refresh: שינוי slug נחסם", "REFRESH_URL_CHANGED" in rules(), True)

reset()
PO.check_refresh(REF_OK.replace("<h2>טכנאי מדיח כלים בוש?</h2>", ""), BRIEF)
check("Refresh: אפס כיסוי פערים מתריע",
      "REFRESH_NO_GAIN" in rules("WARNS"), True)

# ---------- H2 שאלות ----------
reset()
PO.check_h2_ratio("<article><h2>למה?</h2><h2>איך?</h2><h2>מה עושים?</h2></article>")
check("H2: 100% שאלות לא מתריע", len(PO.WARNS), 0)

reset()
PO.check_h2_ratio("<article><h2>רקע</h2><h2>מבנה</h2><h2>סיכום</h2></article>")
check("H2: אפס שאלות מתריע ולא חוסם",
      ("H2_QUESTION_RATIO" in rules("WARNS"), len(PO.ERRORS)), (True, 0))

# ---------- brief במצב DRAFT ----------
reset()
PO.check_terms("<article><p>מדיח כלים בוש</p></article>",
               {"vocabulary": ["מדיח", "כלים", "בוש"]})
check("TERM_VERIFY: אוצר מילים מכוסה", len(PO.WARNS), 0)

reset()
PO.check_terms("<article><p>המגנטרון הפנימי</p></article>",
               {"vocabulary": ["מדיח", "כלים", "בוש"]})
check("TERM_VERIFY: מונח מומצא נתפס",
      "TERM_VERIFY" in rules("WARNS"), True)

# ---------- כוונת עמוד ומסלול פעולה (v8.8) ----------
BASE = '<article><h1>{}</h1>{}</article>'
LINK = '<a href="https://csb.co.il/product/x/">מוצר</a>'

for name, q, intent, extra, want in [
    ("conversion בלי מסלול נחסם", "חלקי חילוף למדיח בוש", "conversion", "", 1),
    ("conversion עם מסלול עובר", "חלקי חילוף למדיח בוש", "conversion", LINK, 0),
    ("service בלי מסלול מותר", "מדיח בוש לא מנקז מים", "service", "", 0),
    ("authority בלי מסלול מותר", "מי נותן שירות רשמי", "authority", "", 0),
]:
    reset()
    PO.check_conversion_path(BASE.format(q, extra),
                             {"allowed_topics": [{"query": q, "intent": intent}]})
    check(name, len(PO.ERRORS), want)

# ---------- EVASIVE_ANSWER (v1.11.0) ----------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pal_lint import check_evasive_answers, Report  # noqa: E402

EVA = ('<article><h3>כמה עולה ביקור טכנאי מדיח כלים בוש?</h3>'
       '<p>העלות תלויה בסוג המכשיר. לקבלת הצעת מחיר פותחים קריאת שירות.</p></article>')
OKA = ('<article><h3>כמה עולה ביקור טכנאי מדיח כלים בוש?</h3>'
       '<p>ביקור טכנאי עולה 349 ₪, לא כולל חלקים.</p></article>')
TIME_EVA = ('<article><h3>תוך כמה זמן מגיע טכנאי?</h3>'
            '<p>נשמח לעדכן בשיחה עם המוקד.</p></article>')
TIME_OK = ('<article><h3>תוך כמה זמן מגיע טכנאי?</h3>'
           '<p>טכנאי מגיע תוך 3 ימי עסקים באזור המרכז.</p></article>')
NOT_COMMERCIAL = ('<article><h3>יש שירות בוש בחיפה?</h3>'
                  '<p>כן, ברחוב ההסתדרות 224.</p></article>')

for name, html, want in [
    ("מחיר: תשובה מתחמקת נחסמת", EVA, 1),
    ("מחיר: תשובה עם מספר עוברת", OKA, 0),
    ("זמן: תשובה מתחמקת נחסמת", TIME_EVA, 1),
    ("זמן: תשובה עם מספר עוברת", TIME_OK, 0),
    ("שאלה לא מסחרית אינה נבדקת", NOT_COMMERCIAL, 0),
]:
    r = Report()
    check_evasive_answers(html, r, "blog")
    check(name, len(r.errors), want)

if FAILED:
    print("\n🔴 test_postflight נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print(f"\n✅ test_postflight עבר במלואו")
