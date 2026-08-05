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

def check_topic(html, brief):
    """המאמר חייב להיות על נושא מהרשימה המאושרת."""
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
    match = next((p for p in products if p.get("permalink", "").rstrip("/") == href.rstrip("/")), None)
    if not match:
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
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I)
    h1 = visible(m.group(1)).strip() if m else ""
    qs = [o["query"] for o in brief.get("allowed_topics", [])][:5]
    return f"| {date.today()} | {url or '[URL אחרי פרסום]'} | {h1} | {'; '.join(qs)} |"


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

    run_pal_lint(a.site, a.file, a.keyword)
    check_topic(html, brief)
    check_terms(html, brief)
    check_hero(html, brief)
    check_h2_ratio(html)
    check_citations(html)
    check_seo_title(html, a.seo_title)

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
    print("\nשורת ledger להוספה:")
    print(ledger_row(html, brief, a.url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
