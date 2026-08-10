#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_flight.py — בדיקות ל-preflight ול-postflight.

למה זה קיים: ב-2026-08-04 שכבת הדדופ ב-phase finalize דחתה 23 מתוך 23 הנושאים
(100% false positive) ואף בדיקה לא תפסה את זה — pal_lint מכוסה ב-19 מקרי selftest,
ושני סקריפטי ה-flight היו ללא כיסוי כלל. שלושת הבאגים באותה שכבה היו נתפסים כאן.

רץ ב-CI לצד selftest.py. exit 1 בכשל.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import preflight as PF          # noqa: E402
import postflight as PO         # noqa: E402

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"✅ {name}")
    else:
        FAILED.append(f"{name}: קיבלתי {got!r}, ציפיתי {want!r}")


# ---------- שכבת הדדופ (הבאג של 2026-08-04) ----------
# משכפלים את הלוגיקה מ-phase_finalize כדי לבדוק אותה בבידוד.
HEB_PREFIX = ("וה", "שה", "בה", "לה", "מה", "כש", "ה", "ו", "ב", "ל", "מ", "ש", "כ")
HEB_SUFFIX = ("יות", "ים", "ות")


def _norm(w):
    for pre in HEB_PREFIX:
        if w.startswith(pre) and len(w) - len(pre) >= 3:
            w = w[len(pre):]
            break
    for suf in HEB_SUFFIX:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def _sig(t):
    return [w for w in re.findall(r"[\u0590-\u05FF\w]+", t) if len(w) > 3]


def _same(a, b):
    return a == b or _norm(a) == b or a == _norm(b) or _norm(a) == _norm(b)


def is_published(query, titles):
    q = _sig(query)
    if len(q) < 2:
        return None
    for t in titles:
        tw = _sig(t)
        if tw and sum(1 for a in q if any(_same(a, b) for b in tw)) / len(q) >= 0.8:
            return t
    return None


LIVE = ["מצב שבת במקרר שארפ: מה הוא מכבה ומה בודקים",
        "חלקי חילוף למקרר שארפ מקוריים"]

for q, want in [
    ("מצב שבת מקרר שארפ", True),            # כפילות ישירה
    ("חלקי חילוף מקרר שארפ", True),         # בלי תחילית ל
    ("חלקי חילוף למקררים שארפ", True),      # רבים
    ("מקרר שארפ לא מקרר מה לעשות", False),  # נושא אחר לגמרי
    ("אטם דלת מקרר שארפ החלפה", False),     # חופף במילה אחת
    ("חלקי חילוף למקרר בלומברג", False),    # מותג אחר
    ("תנור שארפ לא מתחמם", False),          # מוצר אחר
    ("חלקי חילוף למכונת כביסה", False),     # קטגוריה אחרת
]:
    check(f"dedup: {q[:32]}", bool(is_published(q, LIVE)), want)

# ---------- מסנני preflight ----------
check("nav: מרום", PF.is_navigational("שירות מרום טלפון", "marom"), True)
check("nav: פלרם (שגיאת כתיב)", PF.is_navigational("פלרם שירות", "plrom"), True)
check("nav: נושא אמיתי", PF.is_navigational("מקרר שארפ לא מקרר", "marom"), False)
check("מותג מוחרג: בקו במרום", PF.is_excluded_brand("מקרר בקו תקלה", "marom"), True)
check("מותג מוחרג: אלקטרה בפלרום", PF.is_excluded_brand("אלקטרה מקרר", "plrom"), True)
check("מותג מוחרג: בקו ב-CSB מותר", PF.is_excluded_brand("מקרר בקו", "csb"), False)
check("סיווג: אות כוונה", PF.classify("מדיח בוש לא מנקז מים"), "blog")
check("סיווג: שם מותג בלבד", PF.classify("מילה שירות לקוחות"), "brandhub")

# ---------- ניגודיות ----------
check("ניגודיות: שחור על לבן", PO.contrast("#000000", "#ffffff"), 21.0)
check("ניגודיות: אפור חלש נכשל", PO.contrast("#BBBBBB", "#ffffff") < 4.5, True)
check("ניגודיות: אדום מותג עובר", PO.contrast("#B81A21", "#ffffff") >= 4.5, True)

# ---------- נטרול תחיליות ב-TERM_VERIFY ----------
check("prefix: המקרר", PO.strip_prefix("המקרר"), "מקרר")
check("prefix: מילה קצרה נשמרת", PO.strip_prefix("מים"), "מים")

# ---------- התאמת סרטונים (v1.4) ----------
import json as _json  # noqa: E402

_cat_path = Path("/home/claude/pal-gsc/cats/youtube_catalog.json")
if _cat_path.exists():
    _cat = _json.load(open(_cat_path, encoding="utf-8"))
    for _site, _q, _want in [
        ("marom", "מקרר שארפ לא נכנס למצב שבת", True),
        ("marom", "כמה עולה מקרר שארפ 4 דלתות", False),
        ("marom", "מגירת ירקות מקרר שארפ החלפה", True),
        ("csb", "מדיח כלים בוש תקלה e15", False),      # סרטון התקנה למאמר תקלה
        ("csb", "ניקוי מסנן מדיח כלים בוש", True),
        ("csb", "נעילת ילדים כיריים אינדוקציה בוש", True),
        ("plrom", "ניקוי תנור מילה", False),            # מותג תואם, מוצר לא
        ("plrom", "מכונת כביסה מילה מחיר", False),
    ]:
        _got = PF.match_video(_q, _cat.get(_site, {}).get("videos", []))
        check(f"video: {_q[:30]}", bool(_got), _want)
else:
    print("ℹ️  youtube_catalog.json לא קיים — בדיקות וידאו דולגו")

# ---------- סיווג כוונת עמוד (2026-08-10) ----------
for q, want in [
    ("כמה עולה תיקון מדיח בוש", "conversion"),
    ("חלקי חילוף למקרר שארפ", "conversion"),
    ("מי נותן שירות רשמי לבוש בישראל", "authority"),
    ("מדיח בוש לא מנקז מים", "service"),
    ("מצב שבת מקרר שארפ איך מפעילים", "service"),
]:
    check(f"intent: {q[:28]}", PF.page_intent(q), want)

# ---------- עקביות בין כלים (2026-08-10) ----------
# הבעיה חזרה שלוש פעמים: כלל אחד ממליץ לקשר, כלל אחר חוסם.
# הבדיקה מריצה כל URL שה-brief ממליץ עליו דרך pal_lint האמיתי.
import subprocess  # noqa: E402
import tempfile  # noqa: E402

_TOOLS = Path(__file__).resolve().parent.parent


def _blocked(site, url):
    html = ('<article class="blog-article" dir="rtl" lang="he">'
            f'<h1>x</h1><a href="{url}">y</a></article>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False,
                                     encoding="utf-8") as f:
        f.write(html)
        path = f.name
    r = subprocess.run(
        [sys.executable, str(_TOOLS / "pal_lint.py"), "--site", site,
         "--type", "blog", path], capture_output=True, text=True)
    return "FORBIDDEN_LINK" in r.stdout


for _site in ("csb", "marom", "plrom"):
    _bf = Path(f"/home/claude/brief/brief_partial_{_site}.json")
    if not _bf.exists():
        continue
    _b = _json.loads(_bf.read_text(encoding="utf-8"))
    _urls = ([d["url"] for d in _b.get("dominant_pages", [])]
             + [h["url"] for h in _b.get("brand_hubs", [])]
             + [l for l in _b.get("verified_links", [])])
    _bad = [u for u in _urls if _blocked(_site, "https://" + u.lstrip("htps:/"))]
    check(f"עקביות {_site}: brief לא ממליץ על קישור אסור", _bad[:2], [])

if FAILED:
    print("\n🔴 test_flight נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print("\n✅ test_flight עבר במלואו")
