#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
postflight.py — שער יציאה. חוסם הגשה עד שהכל עובר.

מה שהוא בודק ו-pal_lint לא יכול: התאמה ל-brief.
pal_lint בודק את הקובץ מול כללים. postflight בודק את הקובץ מול הדאטה שאושר מראש.

  TERM_VERIFY        מונח מוצר שלא קיים באוצר המילים המאומת (WARN, ריכוז לשיפוט)
  HERO_MISMATCH      permalink/מחיר/תמונה/מק"ט שלא זהים ל-brief (ERROR, אפס סובלנות)
  TOPIC_UNAUTHORIZED מאמר על נושא שלא ברשימת המותרים (ERROR)
  H2_QUESTION_RATIO  אחוז H2 שאלה. WARN מתחת ל-40%, לעולם לא חוסם
  CITATION_COUNT     פחות מ-3 קפסולות עם מקור (ERROR)
  SEO_TITLE          חסר, זהה ל-H1, או מעל 60 תווים (ERROR)
  LEDGER_ROW         מייצר את שורת הלדג'ר אוטומטית

שימוש:
  python3 postflight.py --site marom --brief brief/brief_marom.json --file article.html \\
      --keyword "מצב שבת במקרר שארפ" [--seo-title "..."]

exit 0 = מותר להגיש. אחרת אין הגשה.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

STATE = Path(__file__).resolve().parent.parent
ERRORS, WARNS, NOTES = [], [], []

# מילים שאינן מונחי מוצר. אין טעם להצליב אותן מול אוצר המילים.
STOP = set("""של את עם על אל מן כי אם או גם רק אבל אז כך זה זו זאת הוא היא הם הן אני אתה
אנחנו יש אין לא כן מה מי איך למה כאשר לפני אחרי בין תוך ליד מעל מתחת כדי בגלל למרות
אשר שהוא שהיא כמו יותר פחות מאוד הכי כל כמה איזה אחד אחת שני שתי שלוש ארבע חמש
בכל בלי עד מ ב ל ה ו ש כ""".split())


def err(rule, msg):
    ERRORS.append((rule, msg))


def warn(rule, msg):
    WARNS.append((rule, msg))


HEB_PREFIX = ("ה", "ו", "ב", "ל", "מ", "ש", "כ", "וה", "שה", "בה", "לה", "מה", "כש")


def strip_prefix(w):
    """נטרול תחיליות. "המקרר" ו-"מקרר" הם אותה מילה לצורך אימות מונח."""
    for p in sorted(HEB_PREFIX, key=len, reverse=True):
        if w.startswith(p) and len(w) - len(p) >= 3:
            return w[len(p):]
    return w


def visible(html):
    h = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    h = re.sub(r"<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", h)


# ---------- בדיקות ----------

def matched_topic(html, brief):
    """
    הנושא מה-brief שתואם ל-H1.
    v8.5: בודק גם את refresh_queue. הגרסה הקודמת בדקה רק את allowed_topics,
    ולכן כל מאמר Mode Refresh נחסם ב-TOPIC_UNAUTHORIZED — המכונה החליטה
    "רענן" ואז חסמה את עצמה.
    """
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    h1 = visible(m.group(1)).strip() if m else ""
    for o in brief.get("allowed_topics", []):
        head = " ".join(o["query"].split()[:2])
        if head and head in h1:
            return dict(o, mode="NEW")
    for o in brief.get("refresh_queue", []):
        if o.get("existing_h1") and o["existing_h1"][:25] in h1:
            return dict(o, mode="REFRESH", query=o.get("existing_h1", ""))
        for t in o.get("triggers", []):
            head = " ".join(t["query"].split()[:2])
            if head and head in h1:
                return dict(o, mode="REFRESH", query=t["query"])
    return None


def check_video(html, brief):
    """
    v8.2: ה-brief מחזיק מזהה סרטון מאומת מהערוץ שלנו. אם הוא קיים והמאמר
    לא הטמיע אותו, זו החמצה — סרטון רשמי משלנו על אותו נושא בדיוק.
    נצפה במאמר "מצב שבת שארפ" (2026-08-03): הסרטון היה בערוץ מאז מאי 2025.
    """
    o = matched_topic(html, brief)
    v = (o or {}).get("video")
    if not v:
        NOTES.append("אין סרטון תואם בקטלוג לנושא הזה")
        return
    if v["video_id"] in html:
        NOTES.append(f"וידאו מוטמע: {v['title'][:45]}")
        return
    warn("VIDEO_MISSING",
         f'קיים סרטון רשמי בערוץ שלנו ולא הוטמע: "{v["title"][:45]}" '
         f'({v["views"]} צפיות) — {v["embed"]}')


def check_refresh(html, brief):
    """v8.5: במצב Refresh, ה-URL וה-slug קדושים ו-dateModified חייב להתעדכן."""
    o = matched_topic(html, brief)
    if not o or o.get("mode") != "REFRESH":
        return
    NOTES.append(f"מצב Refresh על {o['url'][:60]} "
                 f"({o.get('total_impressions', 0)} חשיפות)")
    today = date.today().isoformat()
    if today not in html:
        err("REFRESH_DATE", f"dateModified ו-.last-updated חייבים להתעדכן ל-{today}")
    slug = o["url"].rstrip("/").split("/")[-1]
    if slug and slug not in html:
        err("REFRESH_URL_CHANGED",
            f"ה-slug המקורי ({slug[:40]}) אינו מופיע. ב-Refresh ה-URL קדוש")
    gaps = [g["query"] for g in o.get("gap_queries", [])]
    if gaps:
        text = visible(html)
        covered = [g for g in gaps if all(w in text for w in g.split()[:2])]
        NOTES.append(f"שאילתות פער שכוסו: {len(covered)}/{len(gaps)}")
        if not covered:
            warn("REFRESH_NO_GAIN",
                 "אף שאילתת פער לא כוסתה. רענון בלי הוספת כיסוי אינו משפר דירוג. "
                 f"פערים: {', '.join(gaps[:4])}")


def check_topic(html, brief):
    """המאמר חייב להיות על נושא מהרשימה המאושרת."""
    if matched_topic(html, brief):
        NOTES.append("נושא מאושר")
        return
    allowed = [o["query"] for o in brief.get("allowed_topics", [])]
    if not allowed:
        err("TOPIC_UNAUTHORIZED", "ה-brief אינו מכיל נושאים מותרים")
        return
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    h1 = visible(m.group(1)).strip() if m else ""
    for q in allowed:
        head = " ".join(q.split()[:2])
        if head and head in h1:
            NOTES.append(f"נושא מאושר: {q}")
            return
    err("TOPIC_UNAUTHORIZED",
        f'H1 "{h1[:50]}" אינו תואם לאף נושא ברשימה המותרת ({len(allowed)} נושאים)')


def check_terms(html, brief):
    """
    TERM_VERIFY: כל מילה בעברית בגוף המאמר מוצלבת מול אוצר המילים המאומת.
    מילה שלא הוקלדה מעולם על ידי לקוח אמיתי היא מונח שהומצא.
    """
    vocab = set(brief.get("vocabulary") or brief.get("vocabulary_top", []))
    vocab |= {strip_prefix(w) for w in vocab}
    prod = " ".join(p.get("name", "") for p in brief.get("products", []))
    vocab |= set(re.findall(r"[\u0590-\u05FF]{2,}", prod))
    if not vocab:
        warn("TERM_VERIFY", "אוצר מילים ריק ב-brief, הבדיקה דולגה")
        return
    text = visible(html)
    unknown = {}
    for w in re.findall(r"[\u0590-\u05FF]{3,}", text):
        if w in STOP or w in vocab or strip_prefix(w) in vocab:
            continue
        unknown[w] = unknown.get(w, 0) + 1
    if unknown:
        top = sorted(unknown.items(), key=lambda x: -x[1])[:15]
        warn("TERM_VERIFY",
             "מונחים שאינם באוצר המילים המאומת (בדוק שאינם מומצאים): "
             + ", ".join(f"{w}×{c}" for w, c in top))
    NOTES.append(f"TERM_VERIFY: {len(unknown)} מונחים לא מוכרים מתוך אוצר של {len(vocab)}")


def check_hero(html, brief):
    """אפס סובלנות ל-permalink/מחיר/תמונה. שם להצגה מותר לקצר אם הוא רצף מהמקור."""
    products = brief.get("products", [])
    m = re.search(r'<a class="product-card" href="([^"]+)".*?</a>', html, flags=re.S)
    if not m:
        NOTES.append("אין כרטיס Hero במאמר")
        return
    card, href = m.group(0), m.group(1)
    if not products:
        err("HERO_MISMATCH", "יש כרטיס Hero אבל ה-brief ריק ממוצרים")
        return
    def _slug(u):
        import urllib.parse as _u
        return _u.unquote(u).rstrip("/").split("/")[-1]

    match = next((p for p in products
                  if p.get("permalink", "").rstrip("/") == href.rstrip("/")), None)
    if not match:
        # search_products ו-get_product_by_sku מחזירים permalink שונה לאותו
        # מק"ט: אחד מהם חתוך בתו אחד (נצפה 2026-08-09, SKU 00365039 —
        # "...סימנ" במקום "...סימנס"). הגרסה החתוכה היא זו שמחזירה 200.
        hs = _slug(href)
        near = [p for p in products
                if _slug(p.get("permalink", "")).startswith(hs[:-2])
                or hs.startswith(_slug(p.get("permalink", ""))[:-2])]
        if near:
            match = near[0]
            warn("HERO_SLUG_DRIFT",
                 f"ה-slug בכרטיס שונה מה-brief בתו או שניים. אמת ב-check_url "
                 f"איזה מחזיר 200 והשתמש בו verbatim. בכרטיס: {hs[:45]}")
        else:
            err("HERO_MISMATCH", f"permalink בכרטיס אינו מופיע ב-brief: {href[:70]}")
            return
    img = re.search(r'class="product-card-img" src="([^"]+)"', card)
    if img and match.get("image") and img.group(1) != match["image"]:
        err("HERO_MISMATCH", "URL התמונה אינו זהה למה שחזר מ-MCP")
    price = re.search(r'class="product-card-price">([^<]+)<', card)
    if price and match.get("price"):
        shown = re.sub(r"[^\d.]", "", price.group(1))
        real = re.sub(r"[^\d.]", "", str(match["price"]))
        if shown != real:
            err("HERO_MISMATCH", f"מחיר בכרטיס {shown} מול {real} ב-MCP")
    title = re.search(r'class="product-card-title">([^<]+)<', card)
    if title and match.get("name") and title.group(1).strip() not in match["name"]:
        err("HERO_MISMATCH",
            "שם המוצר בכרטיס אינו רצף רציף מתוך השם ב-MCP (קיצור מותר, שינוי לא)")
    NOTES.append("כרטיס Hero תואם ל-brief")


def check_h2_ratio(html):
    h2 = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S | re.I)
    h2 = [visible(x).strip() for x in h2]
    h2 = [x for x in h2 if x and "שאלות נפוצות" not in x and "מאמרים קשורים" not in x]
    if not h2:
        return
    q = sum(1 for x in h2 if "?" in x)
    pct = round(100 * q / len(h2))
    NOTES.append(f"H2 בפורמט שאלה: {pct}% ({q}/{len(h2)})")
    if pct < 40:
        warn("H2_QUESTION_RATIO",
             f"{pct}% מה-H2 שאלות. יעד 60-70 ל-Answer-First. לא חוסם — "
             f"פורמט אינדקס (קודי תקלה) לגיטימי בלי שאלות")


def check_citations(html):
    caps = re.findall(r'<div class="citation".*?</div>', html, flags=re.S)
    good = [c for c in caps if re.search(r"<cite>\s*\S", c)]
    NOTES.append(f"קפסולות ציטוט עם מקור: {len(good)}")
    if len(good) < 3:
        err("CITATION_COUNT", f"{len(good)} קפסולות עם מקור, נדרשות 3")


def check_seo_title(html, seo_title):
    if not seo_title:
        err("SEO_TITLE", "לא סופק SEO Title (--seo-title)")
        return
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    h1 = visible(m.group(1)).strip() if m else ""
    if seo_title.strip() == h1:
        err("SEO_TITLE", "SEO Title זהה ל-H1")
    if len(seo_title) > 60:
        err("SEO_TITLE", f"SEO Title {len(seo_title)} תווים, מקסימום 60")
    NOTES.append(f"SEO Title: {len(seo_title)} תווים")


def run_pal_lint(site, path, keyword):
    lint = STATE / "tools" / "pal_lint.py"
    if not lint.exists():
        err("LINT_MISSING", "tools/pal_lint.py חסר. כלל ברזל: חוסם")
        return
    cmd = [sys.executable, str(lint), "--site", site, "--type", "blog", str(path)]
    if keyword:
        cmd[-1:-1] = ["--keyword", keyword]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout[-2500:])
    if r.returncode != 0:
        err("PAL_LINT", f"pal_lint נכשל (exit {r.returncode}). תקן והרץ מחדש")
    else:
        NOTES.append("pal_lint: exit 0")


def ledger_row(html, brief, url):
    """
    v8.6: השורה נכתבת לתור ולא רק מודפסת.
    עד היום גיל היה מעתיק אותה ידנית לריפו — פעולה ידנית חוזרת, כלומר
    פגם בעיצוב. עכשיו: postflight כותב ל-ledger-pending.md, workflow ממזג,
    וה-URL הסופי מושלם אוטומטית מ-gsc_page_queries שרץ כל שני.
    """
    o = matched_topic(html, brief)
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    h1 = visible(m.group(1)).strip() if m else ""

    if o and o.get("mode") == "REFRESH":
        # ברענון ה-URL ידוע ולא משתנה, והשאילתות הן מה שהעמוד כבר מדורג עליו
        # בתוספת הפערים שכוסו.
        url = url or ("https://" + o["url"])
        qs = [q["query"] for q in o.get("ranking_for", [])][:3] + \
             [g["query"] for g in o.get("gap_queries", [])][:2]
        mode = "refresh"
    else:
        qs = [o["query"]] if o else []
        qs += [t["query"] for t in (brief.get("allowed_topics") or [])[:4]
               if not o or t["query"] != o["query"]]
        mode = "new"

    slug = slug_guess(h1)
    url_cell = url or f"[PENDING:{slug}]"
    row = f"| {date.today()} | {url_cell} | {h1} | {'; '.join(qs[:5])} |"
    write_pending(brief.get("site", ""), row, mode, slug)
    return row


def slug_guess(h1):
    """ניחוש ה-slug מה-H1, בפורמט וורדפרס. משמש להשלמה אוטומטית מ-GSC."""
    s = re.sub(r"[^\w\u0590-\u05FF\s-]", "", h1).strip()
    return re.sub(r"\s+", "-", s)[:80]


def write_pending(site, row, mode, slug):
    """
    תור ההמתנה. ה-workflow ב-Pal-state ממזג אותו ל-content-ledger.md,
    ומחליף [PENDING:slug] ב-URL האמיתי ברגע ש-gsc_page_queries מזהה אותו.
    """
    f = STATE / "ledger-pending.md"
    head = ("# תור שורות ledger ממתינות\n\n"
            "נכתב אוטומטית ע\"י postflight. ה-workflow `ledger-merge` ממזג ל-"
            "content-ledger.md.\n[PENDING:slug] מוחלף ב-URL אמיתי כש-"
            "gsc_page_queries מזהה את העמוד.\n\n")
    cur = f.read_text(encoding="utf-8") if f.exists() else head
    entry = f"- site={site} mode={mode} slug={slug}\n  {row}\n"
    if row in cur:
        return
    f.write_text(cur.rstrip("\n") + "\n" + entry, encoding="utf-8")
    NOTES.append(f"שורת ledger נכתבה לתור: {f.name}")


# ---------- v8.1 ----------

def _lum(hexc):
    hexc = hexc.lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(fg, bg):
    a, b = _lum(fg), _lum(bg)
    hi, lo = max(a, b), min(a, b)
    return round((hi + 0.05) / (lo + 0.05), 2)


def _bg_map(style):
    """
    מפת רקעים לפי סלקטור. הבסיס לפתרון ירושה.
    ".cta-box{background:#140C3C}" קובע את הרקע לכל צאצא שלו.
    """
    out = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", style):
        bg = re.search(r"background(?:-color)?:\s*(#[0-9a-fA-F]{3,6})", m.group(2))
        if not bg:
            continue
        for sel in m.group(1).split(","):
            sel = sel.strip()
            if sel and not sel.startswith("@"):
                out[sel] = bg.group(1)
    return out


def _inherited_bg(sel, bgmap, page_bg):
    """
    רקע אפקטיבי: מהסלקטור עצמו, ואם אין — מהאב הקרוב ביותר בשרשרת.
    לקח 2026-08-09: הבודק בדק כל כלל בנפרד, ולכן ".cta-box h2{color:#fff}"
    נבדק מול לבן במקום מול הרקע הכהה של ההורה. התוצאה: **כל מאמר**
    שמשתמש ברכיב cta-box הסטנדרטי מהתבנית נכשל בשגיאה שגויה.
    """
    base = sel.split(":")[0].strip()
    if base in bgmap:
        return bgmap[base], "עצמי"
    parts = base.split()
    for k in range(len(parts) - 1, 0, -1):
        anc = " ".join(parts[:k])
        if anc in bgmap:
            return bgmap[anc], f"בירושה מ-{anc}"
        # גם סלקטור אב שמוגדר לבדו (".cta-box" מול ".cta-box h2")
        last = parts[k - 1]
        if last in bgmap:
            return bgmap[last], f"בירושה מ-{last}"
    return page_bg, "ברירת מחדל"


def check_contrast(html):
    """
    v8.7: ניגודיות עם פתרון ירושה.
    ה-CSS בתבנית מכיל hex מפורש ו-var() אסור בבלוג, ולכן החישוב דטרמיניסטי —
    אבל רקע נקבע פעם אחת על ההורה, ולכן חובה לטפס בשרשרת הסלקטורים.
    """
    style = "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S | re.I))
    if not style:
        return
    page_bg = "#ffffff"
    bgmap = _bg_map(style)
    checked = 0
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", style):
        body = m.group(2)
        fg = re.search(r"(?<!-)\bcolor:\s*(#[0-9a-fA-F]{3,6})", body)
        if not fg:
            continue
        fs = re.search(r"font-size:\s*(\d+)px", body)
        big = fs and int(fs.group(1)) >= 24
        need = 3.0 if big else 4.5
        for sel in m.group(1).split(","):
            sel = sel.strip()
            if not sel or sel.startswith("@"):
                continue
            bgv, src = _inherited_bg(sel, bgmap, page_bg)
            ratio = contrast(fg.group(1), bgv)
            checked += 1
            if ratio < need:
                err("CONTRAST_RATIO",
                    f"{sel[:38]} — {fg.group(1)} על {bgv} ({src}) = "
                    f"{ratio}:1, נדרש {need}:1")
    NOTES.append(f"ניגודיות: {checked} צמדים נבדקו, {len(bgmap)} רקעים ממופים")


def check_narrative(html, brief):
    """v8.1: לפחות משפט קנוני אחד ב-Direct Answer, ו-Organization description מהנרטיב."""
    sents = brief.get("canonical_sentences", [])
    if not sents:
        warn("NARRATIVE_MISSING", "אין משפטים קנוניים ב-brief, הבדיקה דולגה")
        return
    da = re.search(r'<div class="direct-answer".*?</div>', html, flags=re.S)
    da_txt = visible(da.group()) if da else ""
    hit = None
    for s in sents:
        core = " ".join(s.split()[:6]).rstrip(".")
        if core and core in re.sub(r"\s+", " ", da_txt):
            hit = s
            break
    if not hit:
        err("NARRATIVE_MISSING",
            "אין משפט קנוני ב-Direct Answer. חובה אחד לפחות מקובץ הפרויקט")
    else:
        NOTES.append(f"נרטיב קנוני: נמצא ({hit[:45]}...)")
    org = re.search(r'"@type":\s*"Organization".*?"description":\s*"([^"]{20,})"',
                    html, flags=re.S)
    if org:
        d = org.group(1)
        if not any(" ".join(s.split()[:5]) in d for s in sents):
            err("NARRATIVE_MISSING",
                "Organization description אינו נגזר מהמשפטים הקנוניים")


PAIN = ["לא עובד", "לא עובדת", "תקוע", "נתקע", "לא מקרר", "לא מחמם", "רועש", "רועשת",
        "דולף", "מהבהב", "שבור", "סדוק", "תקלה", "בעיה", "לא נכנס", "לא נסגר",
        "לא מתחיל", "מפסיק", "ריח", "לא בטוחים", "לא יודעים", "מתוסכל"]
ADDRESS = ["אתם", "אתן", "שלכם", "לכם", "אצלכם", "אתה", "שלך", "תמצאו", "תדעו"]


def check_audience_anchor(html, brief):
    """v8.1: העוגן חייב להיות מפורש. מצב הכשל שנצפה הוא עוגן מרומז."""
    da = re.search(r'<div class="direct-answer".*?</div>', html, flags=re.S)
    if not da:
        err("AUDIENCE_ANCHOR", "אין בלוק direct-answer")
        return
    t = re.sub(r"\s+", " ", visible(da.group()))
    words = t.split()[:200]
    seg = " ".join(words)
    vocab = set(brief.get("vocabulary") or [])
    device = [w for w in words if len(w) > 3 and (w in vocab or strip_prefix(w) in vocab)]
    miss = []
    if not any(p in seg for p in PAIN):
        miss.append("מונח כאב")
    if not any(a in seg for a in ADDRESS):
        miss.append("פנייה ישירה לקורא")
    if len(device) < 3:
        miss.append("מונחי מכשיר מאוצר המילים")
    if miss:
        warn("AUDIENCE_ANCHOR", "עוגן הקהל אינו מפורש. חסר: " + ", ".join(miss))
    else:
        NOTES.append("עוגן קהל: מפורש")


def check_info_gain(html, brief):
    """v8.1: דיף H2 מול המתחרים. הסקריפט מודד כיסוי; אתה מכריע אם הייחוד מהותי."""
    comp = brief.get("competitor_headings") or []
    if not comp:
        warn("INFO_GAIN_DIFF", "אין מיפוי H2 של מתחרים ב-brief. הרץ את מחקר המתחרים בשלב 4")
        return
    ours = [visible(x).strip() for x in
            re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S | re.I)]
    ours = [x for x in ours if x and "מאמרים קשורים" not in x]

    def toks(s):
        return {w for w in re.findall(r"[\u0590-\u05FF]{3,}", s) if w not in STOP}

    ctok = set()
    for c in comp:
        ctok |= toks(c)
    unique, shared = [], []
    for h in ours:
        (unique if len(toks(h) - ctok) >= 2 else shared).append(h)
    missing = []
    for c in comp:
        if not any(len(toks(c) & toks(h)) >= 2 for h in ours):
            missing.append(c)
    NOTES.append(f"Information Gain: {len(unique)} H2 ייחודיים לנו, "
                 f"{len(shared)} חופפים, {len(missing)} נושאים שרק המתחרים מכסים")
    if unique:
        NOTES.append("   ייחודי לנו: " + " | ".join(u[:38] for u in unique[:4]))
    if missing:
        NOTES.append("   רק אצל המתחרים: " + " | ".join(m[:38] for m in missing[:4]))
    if not unique:
        err("INFO_GAIN_DIFF",
            "אפס H2 ייחודיים מול המתחרים. המאמר אינו מוסיף מידע חדש")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["csb", "marom", "plrom"])
    ap.add_argument("--brief", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--keyword")
    ap.add_argument("--seo-title")
    ap.add_argument("--url")
    a = ap.parse_args()

    html = Path(a.file).read_text(encoding="utf-8")
    brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
    brief.setdefault("site", a.site)

    if brief.get("degraded"):
        err("DRAFT_BRIEF",
            "ה-brief נוצר במצב DRAFT (--allow-degraded). חסרים: "
            + ", ".join(brief.get("degraded_missing", []))
            + ". הפעל את שרת ה-MCP והרץ preflight מחדש. אין פרסום.")

    run_pal_lint(a.site, a.file, a.keyword)
    check_topic(html, brief)
    check_terms(html, brief)
    check_hero(html, brief)
    check_h2_ratio(html)
    check_citations(html)
    check_seo_title(html, a.seo_title)
    check_video(html, brief)
    check_refresh(html, brief)
    check_contrast(html)
    check_narrative(html, brief)
    check_audience_anchor(html, brief)
    check_info_gain(html, brief)

    print("\n" + "=" * 60)
    for n in NOTES:
        print(f"ℹ️  {n}")
    for r, m in WARNS:
        print(f"⚠️  [{r}] {m}")
    for r, m in ERRORS:
        print(f"❌ [{r}] {m}")
    print("=" * 60)
    if ERRORS:
        print(f"\n🔴 postflight נכשל: {len(ERRORS)} שגיאות. אין הגשה.")
        return 1
    print(f"\n✅ postflight עבר ({len(WARNS)} אזהרות)")
    row = ledger_row(html, brief, a.url)
    print("\nשורת ledger (נכתבה לתור אוטומטית):")
    print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
