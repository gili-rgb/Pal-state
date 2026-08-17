#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
preflight.py — שער כניסה לכל ריצת content-machine.

הרעיון: המודל לא בוחר נושא ולא ממציא מונח. הוא מקבל brief.json שנבנה מדאטה מאומת בלבד.
מה שאין ב-brief — אסור להשתמש בו.

שני שלבים, כי חלק מהמקורות זמינים רק ככלי MCP ברמת המודל ולא לסקריפט:

  שלב plan     — הכל מהריפו וה-GSC. מייצר brief_partial.json + רשימת קריאות MCP נדרשות.
  שלב finalize — מקבל את פלט ה-MCP ומייצר brief.json מלא.

שימוש:
  python3 preflight.py --site marom --phase plan
  # (המודל מריץ את mcp_requests ושומר ל-mcp_results.json)
  python3 preflight.py --site marom --phase finalize --mcp mcp_results.json

exit 1 בכל כשל. אין brief = אין כתיבה.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
from collections import Counter, defaultdict
from pathlib import Path

GSC = Path("/home/claude/pal-gsc/cats")
STATE = Path("/home/claude/pal-state")
OUT = Path("/home/claude/brief")
SITES = {
    "csb": "csb.co.il",
    "marom": "marom-serv.co.il",
    "plrom": "plrom.co.il",
}
# ספי ההכרעה. מקור: מחקר אהרפס (80 מילות מפתח, מקרה אחד דרש טיפול) —
# חפיפת שאילתות אינה אינדיקטור. המיקום הוא האינדיקטור.
RANK_HELD = 20        # עמוד שמדורג מעל זה לא מחזיק את השאילתה
RANK_STRONG = 4       # 4-20 = "שמור וחזק", לא ליצור מתחרה
RANK_DOMINANT = 3     # 1-3 = שולטים. מאמר חדש יתחרה בנכס קיים

# עמודי שותפים בדומיין שלנו. מדורגים היטב אך אינם נכסים שלנו לקישור —
# pal_lint אוסר לקשר אליהם (FORBIDDEN_LINK). מקור: כללי הברזל.
# בלי הרשימה הזו preflight המליץ לקשר לעמודים ש-postflight חוסם.
PARTNER_PATHS = {
    "csb": ["/bosch-service/", "/siemens-service/",
            "/bosch-parts/", "/siemens-parts/"],
    "marom": ["/sharp-parts/", "/sharp-service/", "/dedietrich-parts/",
              "/dedietrich-service/", "/bauknecht-parts/", "/bauknecht-service/",
              "/haier-parts/", "/haier-service/", "/blomberg-parts/",
              "/blomberg-service/", "/delonghi-parts/", "/delonghi-service/",
              "/amana-parts/", "/amana-service/", "/zanussi-parts/",
              "/zanussi-service/"],
    "plrom": ["/sauter-service/", "/liebherr-service/",
              "/miele-service/", "/miele-parts/"],
}


def is_partner_page(url, site):
    u = "/" + url.split(".co.il")[-1].lstrip("/")
    return any(p.rstrip("/") == u.rstrip("/").split("#")[0]
               for p in PARTNER_PATHS.get(site, []))
MIN_IMPR = 30         # סף רעש לשאילתת יעד

# שאילתות ניווט למותג שלנו. הן מדורגות מצוין בזכות דף הבית ואינן נושא לבלוג.
NAV_TERMS = {
    "marom": ["מרום", "marom", "שרות מרום"],
    "csb": ["סי אס בי", "csb", "סי.אס.בי", "סיאסבי", "סי בי אס", "bsh israel"],
    "plrom": ["פלרום", "plrom", "פל רום", "palrom", "פלרם", "פרלום"],
}

# מותגים מוחרגים לצמיתות. החלטות עסקיות, לא העדפה.
EXCLUDED_BRANDS = {
    "marom": ["בקו", "beko"],
    "plrom": ["אלקטרה", "electra"],
    "csb": [],
}

# אות כוונה. שאילתה בלי אף אחד מאלה היא ניווט או פער brand hub, לא נושא בלוג.
INTENT_TOKENS = [
    "תקלה", "תקלות", "לא עובד", "לא עובדת", "לא מתחיל", "לא מקרר", "לא מחמם",
    "קוד", "שגיאה", "איך", "למה", "מה עושים", "החלפת", "החלפה", "תיקון", "לתקן",
    "ניקוי", "לנקות", "אטם", "גומי", "מסנן", "הוראות", "הפעלה", "מצב שבת",
    "מחיר", "עולה", "כמה", "דגם", "מתאים", "הבדל", "בין", "תחזוקה", "ריח",
    "רועשת", "רועש", "נתקע", "דולף", "מים", "מהבהב", "אביזר", "אביזרים", "חלקי חילוף",
]


def is_navigational(query, site):
    """שם החברה שלנו, כולל שגיאות כתיב = ניווט."""
    q = query.lower().strip()
    return any(t.lower() in q for t in NAV_TERMS[site])


def is_excluded_brand(query, site):
    q = query.lower()
    return any(b.lower() in q for b in EXCLUDED_BRANDS.get(site, []))


# סיווג כוונת עמוד (הכרעת גיל, 2026-08-10). לא כל עמוד חייב להמיר,
# וכל סוג נמדד אחרת. הסדר בעידן AI Overview:
#   להיות מצוטט ← להביא תנועה ← לתת ערך ← לאפשר פעולה
PAGE_INTENT = {
    "conversion": {
        "signals": ["מחיר", "כמה עולה", "עלות", "לקנות", "רכישה", "חלקי חילוף",
                    "חלפים", "אביזר", "אביזרים", "מקורי", "להזמין", "טכנאי",
                    "תיקון", "החלפת", "מומלץ", "השוואה", "יד 2", "סדרה"],
        "measure": "אירועי המרה ב-GA4",
        "requires": "מסלול פעולה: כרטיס מוצר או קישור לעמוד המרה",
    },
    "authority": {
        "signals": ["שירות רשמי", "יבואן", "אחריות", "מי נותן", "הסמכה",
                    "תקן", "מעבדה מוסמכת"],
        "measure": "ציטוט במנועי AI וקישורים נכנסים",
        "requires": "מקורות מאומתים, נרטיב קנוני, קישור לעמוד המותג",
    },
    "service": {
        "signals": ["איך", "מדריך", "הוראות", "הפעלה", "התקנה", "ניקוי",
                    "תחזוקה", "קוד", "שגיאה", "לא עובד", "לא מנקז", "לא מתחמם",
                    "מצב שבת", "איפוס", "פירוק"],
        "measure": "פתרון הבעיה. חיסכון בשיחות למוקד",
        "requires": "אבחון אמיתי. אין חובת כפתור מכירה",
    },
}


def page_intent(query):
    """
    כוונת העמוד קובעת איך הוא נמדד ומה נדרש ממנו.
    לקח 2026-08-10: /סרטוני-הדרכה/ עם 7,031 צפיות ואפס אירועי המרה סומן
    בטעות ככישלון. הוא עמוד service — הוא עשה את עבודתו כשלקוח התקין לבד
    ולא התקשר למוקד. מדידה אחידה בהמרות מייצרת מסקנות שגויות.
    """
    q = query.lower()
    hits = {k: sum(1 for s in v["signals"] if s in q)
            for k, v in PAGE_INTENT.items()}
    best = max(hits, key=lambda k: hits[k])
    return best if hits[best] else "service"


def classify(query):
    """
    blog      = יש אות כוונה (בעיה, פעולה, השוואה)
    brandhub  = שם מותג בלי אות כוונה. פער עמוד מותג, לא פער בלוג.
    """
    q = query.lower()
    return "blog" if any(t in q for t in INTENT_TOKENS) else "brandhub"


def die(msg):
    print(f"❌ preflight נכשל: {msg}", file=sys.stderr)
    sys.exit(1)


def norm_url(u):
    u = urllib.parse.unquote(u.strip())
    return re.sub(r"^https?://", "", u).rstrip("/")


# ---------- מקורות ----------

def load_lint_version():
    f = STATE / "tools" / "pal_lint.py"
    if not f.exists():
        die("tools/pal_lint.py חסר ב-pal-state. כלל ברזל: חוסם הגשה")
    m = re.search(r'VERSION\s*=\s*"([\d.]+)"', f.read_text(encoding="utf-8"))
    return m.group(1) if m else "unknown"


def load_ledger(site):
    f = STATE / "content-ledger.md"
    if not f.exists():
        die("content-ledger.md חסר")
    domain = SITES[site]
    rows, in_site = [], False
    for ln in f.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("## "):
            in_site = domain in ln
        if not in_site or not ln.startswith("|") or ln.startswith("|---") or "תאריך" in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        url = next((c for c in cells if "http" in c), None)
        if not url:
            continue
        queries = [q.strip() for q in cells[-1].split(";") if q.strip()] \
            if cells[-1] not in ("אין נתונים", "—", "-", "") else []
        rows.append({"url": norm_url(url), "h1": cells[2] if len(cells) > 2 else "",
                     "queries": queries})
    if not rows:
        die(f"אין שורות ledger ל-{site}")
    return rows


def load_page_queries(site):
    f = GSC / f"{site}_page_queries.json"
    if not f.exists():
        die(f"{f.name} חסר. הרץ את ה-Action 'GSC Page Queries'")
    raw = json.load(open(f, encoding="utf-8"))
    return {norm_url(p): qs for p, qs in raw.items()}


# ---------- לוגיקה ----------

def build_vocabulary(pages, site):
    """אוצר מילים מאומת: כל מילה שלקוח אמיתי הקליד. מונח שאינו כאן — אסור."""
    vocab = Counter()
    for qs in pages.values():
        for q in qs:
            for w in re.findall(r"[\u0590-\u05FFA-Za-z0-9''\"-]+", q["query"]):
                if len(w) > 1:
                    vocab[w] += q["impressions"]
    ac = GSC / "autocomplete_customer_language.md"
    if ac.exists():
        for w in re.findall(r"[\u0590-\u05FF]{2,}", ac.read_text(encoding="utf-8")):
            vocab[w] += 1
    return vocab


def rank_for_query(pages, query, scope=None):
    """
    המיקום הטוב ביותר על שאילתה.
    scope = קבוצת URL להשוואה. קניבליזציה קיימת רק בין עמודים מאותו סוג:
    מאמר בלוג מול מאמר בלוג. עמוד מותג שמדורג על שם המותג, או דף בית שמדורג
    על שם החברה, אינם מתחרים במאמר תקלה — לכן ה-scope הוא ה-ledger בלבד.
    """
    best = None
    for url, qs in pages.items():
        if scope is not None and url not in scope:
            continue
        for q in qs:
            if q["query"] == query:
                if best is None or q["position"] < best[1]:
                    best = (url, q["position"], q["impressions"])
    return best


def dominant_page(pages, query, site=None):
    """
    העמוד שמדורג 1-3 על השאילתה, מכל סוג — לא רק בלוג.
    לקח 2026-08-10: "חלקי חילוף למקרר שארפ" (19,558 חשיפות, מיקום 1.0,
    CTR 8.7%) סומן NEW כי ה-scope היה מאמרי בלוג בלבד, ועמוד הקטגוריה
    ששולט בשאילתה היה בלתי נראה. מאמר חדש שם היה מתחרה בנכס אמיתי.
    """
    best = rank_for_query(pages, query)      # ללא scope — כל סוגי העמודים
    if not best or best[1] > RANK_DOMINANT:
        return None
    partner = site and is_partner_page(best[0], site)
    return {"url": best[0], "position": round(best[1], 1),
            "impressions": best[2], "partner": bool(partner)}


def cannibalization_verdict(pages, query, blog_urls):
    """
    מיקום, לא אחוז חפיפה.
      4-20  → Refresh חובה (העמוד מחזיק את השאילתה)
      >20   → מאמר חדש מותר
      אין   → מאמר חדש
    """
    hit = rank_for_query(pages, query, scope=blog_urls)
    if not hit:
        return {"verdict": "NEW", "reason": "אין מאמר בלוג שמדורג על השאילתה"}
    url, pos, impr = hit
    if pos <= RANK_HELD:
        return {"verdict": "REFRESH", "url": url, "position": round(pos, 1),
                "reason": f"מאמר בלוג קיים מדורג {round(pos,1)} — 4-20 = שמור וחזק, לא ליצור מתחרה"}
    return {"verdict": "NEW", "url": url, "position": round(pos, 1),
            "reason": f"העמוד הקיים במיקום {round(pos,1)}, מעל {RANK_HELD} — אינו מחזיק את השאילתה"}


def opportunities(pages, ledger, blog_urls, site, limit=25):
    """הזדמנות = שאילתה עם ביקוש, בלי עמוד שמחזיק אותה, ובלי כיסוי בלדג'ר."""
    covered = set()
    for r in ledger:
        covered.update(q.lower() for q in r["queries"])
    agg = defaultdict(lambda: {"impressions": 0, "clicks": 0, "best_pos": 999})
    for url, qs in pages.items():
        for q in qs:
            if q["impressions"] < MIN_IMPR:
                continue
            a = agg[q["query"]]
            a["impressions"] += q["impressions"]
            a["clicks"] += q["clicks"]
            a["best_pos"] = min(a["best_pos"], q["position"])
    out, dominated = [], []
    for query, a in agg.items():
        if query.lower() in covered:
            continue
        if is_navigational(query, site) or is_excluded_brand(query, site):
            continue
        blog_hit = rank_for_query(pages, query, scope=blog_urls)
        if blog_hit and blog_hit[1] <= RANK_STRONG:   # מאמר בלוג כבר מדורג מצוין
            continue
        intent = page_intent(query)
        dom = dominant_page(pages, query, site)
        # עמוד שותף ששולט: אין לכתוב עליו מאמר מתחרה, אבל גם אסור
        # לקשר אליו. הוא נרשם בנפרד כדי שנדע שהשאילתה תפוסה על ידי
        # נכס שאינו שלנו — וזו הזדמנות לעמוד /brands/ במקומו.
        if dom and intent == "conversion":
            # שאילתה מסחרית שכבר במקום 1-3: העמוד הקיים עונה עליה טוב
            # יותר ממאמר. הוא נכס לקשר אליו, לא נושא לשכפל.
            dominated.append({"query": query, "impressions": a["impressions"],
                              "clicks": a["clicks"], **dom})
            continue
        v = cannibalization_verdict(pages, query, blog_urls)
        out.append({"query": query, "kind": classify(query),
                    "intent": page_intent(query),
                    "impressions": a["impressions"],
                    "clicks": a["clicks"], "best_position": round(a["best_pos"], 1),
                    **v})
    out.sort(key=lambda x: -x["impressions"])
    dominated.sort(key=lambda x: -x["impressions"])
    ours = [d for d in dominated if not d.get("partner")]
    partner = [d for d in dominated if d.get("partner")]
    return out[:limit], ours[:20], partner[:15]


def h1_variant(pages, query):
    """הווריאנט הדומיננטי: הניסוח שהכי הרבה אנשים הקלידו, לא מה שנשמע טוב."""
    head = " ".join(query.split()[:2])
    cands = Counter()
    for qs in pages.values():
        for q in qs:
            if head in q["query"]:
                cands[q["query"]] += q["impressions"]
    return [{"query": k, "impressions": v} for k, v in cands.most_common(5)]


# ---------- ראשי ----------

SKILL_DIR = Path(os.environ.get("CM_SKILL_DIR", "/mnt/skills/user/content-machine"))


def canonical_sentences(site):
    """המשפטים הקנוניים מקובץ הפרויקט. מקור יחיד, נכנס ל-brief."""
    f = SKILL_DIR / f"project-{site}.md"
    if not f.exists():
        return []
    s = f.read_text(encoding="utf-8")
    i = s.find("משפטים קנוניים")
    if i < 0:
        return []
    out = []
    for ln in s[i:i + 2500].split("\n"):
        m = re.match(r"\s*\d+\.\s+(.{15,})", ln)
        if m:
            out.append(m.group(1).strip())
    return out


SITE_HEADING = {"csb": "CSB", "marom": "Marom", "plrom": "Plrom"}


def load_autocomplete(site, blog_urls, pages, ledger):
    """
    מקור הזדמנויות שני (v1.2). GSC מראה רק שאילתות שכבר יש לנו עליהן חשיפות,
    ולכן אוקיינוס כחול — ביקוש שאיננו נוכחים בו כלל — בלתי נראה לו לחלוטין.
    autocomplete_customer_language.md מחזיק 1,054 "יהלומים": הצעות של גוגל
    שאינן מופיעות ב-GSC. זה מה שהופך מלאי של 7 שבועות למלאי של 60.
    """
    f = GSC / "autocomplete_customer_language.md"
    if not f.exists():
        return []
    want = SITE_HEADING[site]
    cur_site = cur_brand = None
    gems = []
    for ln in f.read_text(encoding="utf-8").split("\n"):
        if ln.startswith("## "):
            cur_site = ln[3:].strip()
        elif ln.startswith("### "):
            cur_brand = ln[4:].strip()
        elif ln.startswith("- ") and cur_site == want and cur_brand:
            gems.append((ln[2:].strip(), cur_brand))

    covered = {q.lower() for r in ledger for q in r["queries"]}
    out = []
    for q, brand in gems:
        if len(q) < 8 or q.lower() in covered:
            continue
        if is_navigational(q, site) or is_excluded_brand(q, site):
            continue
        if classify(q) != "blog":
            continue
        # אם כבר יש לנו מאמר בלוג שמדורג על זה, זה Refresh ולא הזדמנות חדשה
        hit = rank_for_query(pages, q, scope=blog_urls)
        if hit and hit[1] <= RANK_HELD:
            continue
        out.append({"query": q, "kind": "blog", "brand": brand,
                    "intent": page_intent(q),
                    "impressions": 0, "clicks": 0, "best_position": None,
                    "verdict": "NEW", "source": "autocomplete",
                    "reason": "יהלום autocomplete — ביקוש שאיננו נוכחים בו ב-GSC כלל"})
    return out


def brand_hubs_from_ledger(site):
    """
    סעיף ה-brand hub בלדג'ר בפורמט נפרד: נתיב יחסי, בלי דומיין.
    load_ledger מסנן לפי דומיין ולכן מפספס אותו, וכך preflight דיווח
    "אין עמוד מותג" על ארבעה עמודים שנבנו ביולי (נצפה 2026-08-09).
    """
    f = STATE / "content-ledger.md"
    if not f.exists():
        return []
    dom = SITES[site]
    out = []
    for ln in f.read_text(encoding="utf-8").split("\n"):
        if not ln.startswith("|") or "/brands/" not in ln:
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        path = next((c for c in cells if c.startswith("/brands/")), None)
        if not path:
            continue
        alias = next((c for c in cells if c in SITES), None)
        if alias and SITES[alias] != dom:
            continue
        out.append(dom + path.rstrip("/"))
    return out


def discover_brand_hubs(pages, ledger_hubs=None):
    """
    v1.3: רישום עמודי המותג הקיימים + מצב החשיפות שלהם.
    הרקע (2026-08-06): עמודי /brands/ של CSB פורסמו ביולי ועמדו על אפס חשיפות,
    בעוד עמודי השותפים בשורש קלטו 264K. הכלי לא ראה אותם כלל ודיווח "אין עמוד",
    ולכן דיווח שגוי. מעכשיו הם ב-brief, גם כשהחשיפות אפס — במיוחד אז.
    """
    hubs = {}
    for url, qs in pages.items():
        if "/brands/" not in url:
            continue
        base = url.split("#")[0].rstrip("/")
        if base.endswith("/brands"):
            continue
        h = hubs.setdefault(base, {"url": base, "impressions": 0, "clicks": 0})
        h["impressions"] += sum(q["impressions"] for q in qs)
        h["clicks"] += sum(q["clicks"] for q in qs)
    # עמוד מותג עם אפס חשיפות אינו קיים בדאטת GSC, ולכן דווח "אין עמוד"
    # על עמודים שנבנו ביולי (נצפה 2026-08-09). הלדג'ר הוא המקור המשלים.
    for u in (ledger_hubs or []):
        if u not in hubs:
            hubs[u] = {"url": u, "impressions": 0, "clicks": 0}
    out = sorted(hubs.values(), key=lambda h: -h["impressions"])
    for h in out:
        h["status"] = "פעיל" if h["impressions"] >= 100 else "אפס תנועה — דורש הזנת קישורים"
    return out


def load_video_catalog(site):
    """
    v1.4: קטלוג הסרטונים של הערוץ (youtube_pull.py).
    properties של ערוצי יוטיוב אינם מוחזרים מ-sites.list ב-Search Console
    (אומת 2026-08-06), ולכן YouTube Data API הוא המקור.
    """
    f = GSC / "youtube_catalog.json"
    if not f.exists():
        return []
    return json.load(open(f, encoding="utf-8")).get(site, {}).get("videos", [])


# שמות מוצר ומותג. חפיפה בהם בלבד אינה מעידה על התאמה נושאית.
APPLIANCE_TOKENS = {
    "מדיח", "כלים", "כביסה", "מכונה", "מקרר", "תנור", "מייבש", "כיריים",
    "מיקרוגל", "מיקסר", "קפה", "שואב", "אבק", "קולט", "אדים", "מקפיא",
    "בלנדר", "מעבד", "מזון", "מגהץ",
}

BRAND_TOKENS = {
    "בוש", "סימנס", "קונסטרוקטה", "גגנאו", "שארפ", "בלומברג", "האייר",
    "זנוסי", "דלונגי", "מילה", "ליבהר", "סאוטר", "פיליפס", "ברוויל",
    "טפאל", "מולינקס", "אלקטרה", "טושיבה", "וירפול", "מגימיקס",
}

ENTITY_TOKENS = APPLIANCE_TOKENS | BRAND_TOKENS

# טוקני פעולה. חפיפה באחד מהם היא התנאי להתאמה — שם מוצר ומותג אינם מספיקים.
ACTION_TOKENS = {
    "ניקוי", "לנקות", "פילטר", "מסנן", "מסננים", "התקנה", "התקנת", "להתקין", "פירוק",
    "הרכבה", "נזילה", "נזילות", "דולף", "שבת", "מנגנון", "כשרות", "תקלה",
    "תקלות", "קוד", "שגיאה", "החלפה", "להחליף", "החלפת", "איפוס", "לאפס",
    "הפעלה", "להפעיל", "נעילה", "ילדים", "ריח", "אבנית", "מלח", "אטם", "גומי",
    "תוף", "משאבה", "ניקוז", "צינור", "ברגי", "ריתום", "תחזוקה", "הובלה", "רעש", "מרעישה", "חימום", "מחמם", "סחיטה",
    "תוכנית", "סלסלה", "מגירה", "מגירת", "ירקות", "זרוע", "התזה", "אינדוקציה", "טיימר",
}

VID_STOP = {"סרטון", "הדרכה", "הוראות", "מדריך", "שירות", "מרום", "אחזקה",
            "שירותים", "הסבר", "לכל", "הדגמים", "עצמית", "בעצמך"}


def _vnorm(w):
    # "כ" כתחילית נדירה בעברית ושוברת מילים לגיטימיות ("כיריים" → "יריים").
    for pre in ("וה", "שה", "בה", "לה", "מה", "כש", "ה", "ו", "ב", "ל", "מ", "ש"):
        if w.startswith(pre) and len(w) - len(pre) >= 3:
            w = w[len(pre):]
            break
    for suf in ("יות", "ים", "ות", "י"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _vsame(a, b):
    """
    השוואה דו-כיוונית ולא נרמול לחלל משותף.
    נרמול חד-כיווני מייצר גזעים לא עקביים: "מקרר" הופך ל"קרר" אבל "למקררי"
    הופך ל"מקררי", והשניים לא נפגשים. זה אותו באג שתוקן בשכבת הדדופ.
    """
    return a == b or _vnorm(a) == b or a == _vnorm(b) or _vnorm(a) == _vnorm(b)


def _vsig(text):
    """טוקנים גולמיים. מילות מסגרת כמו "סרטון"/"מדריך" אינן מזהות נושא."""
    return [w for w in re.findall(r"[\u0590-\u05FFA-Za-z0-9]{3,}", text)
            if w not in VID_STOP and _vnorm(w) not in VID_STOP]


def _hits(qs, ts):
    return [a for a in qs if any(_vsame(a, b) for b in ts)]


def _in_set(tok, pool):
    return any(_vsame(tok, x) for x in pool)


def match_video(query, videos):
    """
    התאמת סרטון לנושא. שלושה תנאים מצטברים, כולם נדרשים:
      1. לפחות 2 טוקנים משותפים, וכיסוי 60% מטוקני השאילתה
      2. טוקן פעולה משותף (ניקוי/תקלה/שבת/החלפה...) — לא רק שם מוצר
      3. סוג מוצר משותף — לא רק מותג
    סרטון לא רלוונטי גרוע מאין סרטון. ההתאמה הגסה הדביקה סרטון התקנה
    למאמר על קוד תקלה E15 רק בזכות "מדיח כלים בוש".
    """
    qs = _vsig(query)
    if len(qs) < 2:
        return None
    best = None
    for v in videos:
        ts = _vsig(v["title"])
        hits = _hits(qs, ts)
        if len(hits) < 2:
            continue
        # כותרות סרטונים כמעט לא מכילות שם מותג, ולכן מותג במכנה מנפח
        # את הדרישה ומייצר החמצות. הוא עדיין נספר כהתאמה במונה.
        denom = [t for t in qs if not _in_set(t, BRAND_TOKENS)] or qs
        cover = len([h for h in hits if not _in_set(h, BRAND_TOKENS)]) / len(denom)
        # 0.5 ולא 0.6: שערי הפעולה והמוצר עושים את העבודה האמיתית,
        # וסף כיסוי גבוה מדי ייצר החמצות על שאילתות ארוכות.
        if cover < 0.5:
            continue
        if not any(_in_set(h, ACTION_TOKENS) for h in hits):
            continue
        if not any(_in_set(h, APPLIANCE_TOKENS) for h in hits):
            continue
        tags = _vsig(" ".join(v.get("tags", [])))
        score = len(hits) + 0.5 * len(_hits(qs, tags))
        cand = (score, cover, v.get("views", 0))
        if best is None or cand > best[0]:
            best = (cand, v, cover)
    if not best:
        return None
    _, v, cover = best
    return {"video_id": v["video_id"], "title": v["title"], "embed": v["embed"],
            "views": v.get("views", 0), "published": v.get("published", ""),
            "coverage": round(cover, 2)}


def enrich_refresh(items, pages, ledger, site=None):
    """
    v1.5: תור Refresh ברמת **עמוד**, לא ברמת שאילתה.
    הגרסה הראשונה החזירה שורה לכל שאילתה, ולכן אותו עמוד הופיע שש פעמים.
    רענון מתבצע על עמוד אחד; כל השאילתות שהפעילו אותו הן הטריגר המצטבר.

    לכל עמוד מצורף מה שדרוש כדי לרענן בלי להרוס:
      • ranking_for — מה העמוד כבר מנצח בו. אסור לפגוע בזה
      • gap_queries — ביקוש שהעמוד נוגע בו וחלש (מיקום 11-40). שם מוסיפים
      • frozen — מה שלא נוגעים בו
    """
    by_url = {r["url"]: r for r in ledger}
    grouped = {}
    for it in items:
        url = it.get("url")
        if not url:
            continue
        g = grouped.setdefault(url, {"url": url, "kind": "blog",
                                     "verdict": "REFRESH", "triggers": []})
        g["triggers"].append({"query": it["query"],
                              "position": it.get("position"),
                              "impressions": it.get("impressions", 0)})
    out = []
    for url, g in grouped.items():
        # הכרעת גיל 2026-08-16: מותג מוחרג אינו נכנס לתור ה-Refresh.
        # הרקע: /שירות-לקוחות-אלקטרה-.../ ישב במקום 2 בתור של פלרום עם
        # 23,698 חשיפות ומיקום 1.6, בזמן ש-BRAND_ELECTRA חוסם כל תוכן
        # אלקטרה שם. is_excluded_brand הופעל על allowed_topics ועל
        # autocomplete, ולא כאן. preflight המליץ על מה ש-postflight חוסם,
        # בפעם השלישית (v8.12, MAROM_PC_LINK, וזה).
        if site and (is_excluded_brand(urllib.parse.unquote(url), site)
                     or is_excluded_brand(by_url.get(url, {}).get("h1", ""), site)):
            continue
        rows = pages.get(url, [])
        ranked = sorted(rows, key=lambda q: -q["impressions"])
        led = by_url.get(url, {})
        # פער = ביקוש אמיתי במיקום חלש. מעל 40 זה כבר לא אותו עמוד בפועל.
        gaps = [q for q in ranked if 10 < q["position"] <= 40 and q["impressions"] >= 15]
        # v1.8 (2026-08-16): best_position הוא השאילתה הטובה ביותר מתוך מאות,
        # והוא הוצג לצד total_impressions כאילו הוא ביצועי העמוד. בפועל
        # /שירות-בוש-כיצד-מזמינים-תיקון/ הציג "72,697 חשיפות | pos 1.1"
        # בזמן שהמיקום המשוקלל האמיתי הוא 5.6 (271 שאילתות). גיל תכנן
        # ריענון על סמך המספר הזה. מעכשיו הממוצע המשוקלל הוא השדה הראשי.
        _imp = sum(q["impressions"] for q in rows) or 1
        _clk = sum(q["clicks"] for q in rows)
        g.update({
            "existing_h1": led.get("h1", ""),
            "ledger_queries": led.get("queries", []),
            "total_impressions": sum(q["impressions"] for q in rows),
            "total_clicks": _clk,
            "avg_position": round(
                sum(q["position"] * q["impressions"] for q in rows) / _imp, 1),
            "best_position": round(min((q["position"] for q in ranked), default=99), 1),
            "ctr": round(_clk / _imp * 100, 2),
            "query_count": len(rows),
            "ranking_for": [{"query": q["query"], "position": round(q["position"], 1),
                             "impressions": q["impressions"], "clicks": q["clicks"]}
                            for q in ranked[:10]],
            "gap_queries": [{"query": q["query"], "position": round(q["position"], 1),
                             "impressions": q["impressions"]} for q in gaps[:12]],
            "frozen": ["URL", "slug", "datePublished", "@id של הישויות"],
        })
        g["triggers"] = sorted(g["triggers"], key=lambda t: -t["impressions"])[:8]
        out.append(g)
    out.sort(key=lambda x: -x["total_impressions"])
    return out


# נציגת AI לתיאום התקנות. יעד הסטה (הכרעת גיל 2026-08-10): 5,637 שיחות
# לחודשיים מכבידות על המוקד. הערוץ הזה מוצג ראשון, המוקד כחלופה.
AI_AGENT = {
    "csb": {
        "name": "מאיה",
        "url": "https://csb.co.il/ai-install/?dept=csb",
        "phone": "079-9198357",
        "note": ("תיאום, שינוי מועד וביטול התקנת מוצר חדש בלבד. שני ערוצים: "
                 "שיחה קולית וצ'אט. 24/7, 365 ימים, בלי המתנה לנציג"),
        "channels": ["שיחה קולית", "צ'אט"],
    },
    "marom": {
        "name": "דנה",
        "url": "https://marom-serv.co.il/ai-install/?dept=marom",
        "phone": "079-920-5886",
        "note": ("תיאום, שינוי מועד וביטול התקנת מוצר חדש בלבד. שני ערוצים: "
                 "שיחה קולית וצ'אט. 24/7, 365 ימים, בלי המתנה לנציג"),
        "channels": ["שיחה קולית", "צ'אט"],
    },
    "plrom": None,
}

# אזור אישי — מסלול השירות העצמי. הכרעת גיל 2026-08-17: כל נושא שנציגת
# ה-AI אינה מטפלת בו (אחריות, קריאת שירות, תיקון, מעקב) נסגר כאן, ולא
# בטלפון. חיוג למוקד הוא עדיפות אחרונה. הכתובות של מרום ופלרום טרם
# התקבלו — None פירושו ש-SELF_SERVICE_MISSING אינו פעיל שם.
SELF_SERVICE = {
    "csb": {
        "url": "https://myarea.csb.co.il",
        "name": "האזור האישי",
        "note": ("בדיקת אחריות מקוונת, פתיחת קריאת שירות בטופס בלי טלפון, "
                 "ומעקב אחר סטטוס. זמין 24/7"),
    },
    "marom": {
        "url": "https://myarea.marom-serv.co.il/login/",
        "name": "האזור האישי",
        "note": ("בדיקת אחריות מקוונת, פתיחת קריאת שירות בטופס בלי טלפון, "
                 "ומעקב אחר סטטוס. זמין 24/7"),
    },
    # לפלרום אין נציגת AI, אבל **כן יש אזור אישי**. זהו מסלול הפעולה
    # הדיגיטלי היחיד שלה, ולכן הוא קריטי שם יותר מאשר בשני האחרים.
    "plrom": {
        "url": "https://myarea.plrom.co.il/login/",
        "name": "האזור האישי",
        "note": ("בדיקת אחריות מקוונת, פתיחת קריאת שירות בטופס בלי טלפון, "
                 "ומעקב אחר סטטוס. זמין 24/7"),
    },
}

# מחירי שירות מאומתים. מקור: גיל, 2026-08-10. מוזרמים ל-brief כדי שהמודל
# יענה במספר ולא יפנה. תשובה בלי מספר נחסמת ב-EVASIVE_ANSWER.
PRICING = {
    "csb": {
        "ביקור טכנאי בבית": "349 ₪, לא כולל חלקים",
        "הערה": "בתקופת האחריות ללא עלות",
    },
    "plrom": {
        "ביקור טכנאי בבית — מילה או ליבהר": "390 ₪ כולל מע\"מ",
        "ביקור טכנאי בבית — סאוטר או TCL": "340 ₪ כולל מע\"מ",
        "בדיקת מעבדה — מוצר קטן": "290 ₪ כולל מע\"מ",
        "בדיקת מעבדה — מכונת קפה ברוויל או סייג'": "390 ₪ כולל מע\"מ",
        "הערה": "ביקור בית רק למוצרים גדולים: כביסה, מייבש, מדיח, תנור, מקרר, כיריים",
    },
    "marom": {
        "ביקור טכנאי בבית": "290 ₪ לכל המוצרים",
        "חריג": "וייקינג ופיאבה — מחיר שונה, טרם התקבל. אל תנחש",
    },
}


def phase_plan(site):
    OUT.mkdir(exist_ok=True)
    lint = load_lint_version()
    ledger = load_ledger(site)
    pages = load_page_queries(site)
    vocab = build_vocabulary(pages, site)
    blog_urls = {r["url"] for r in ledger}
    brand_hubs = discover_brand_hubs(pages, brand_hubs_from_ledger(site))
    videos = load_video_catalog(site)
    opps, dominated, partner_dom = opportunities(
        pages, ledger, blog_urls, site, limit=150)
    for o in opps:
        o.setdefault("source", "gsc")
    allowed = [o for o in opps if o["verdict"] == "NEW" and o["kind"] == "blog"]
    gems = load_autocomplete(site, blog_urls, pages, ledger)
    seen = {o["query"].lower() for o in allowed}
    allowed += [g for g in gems if g["query"].lower() not in seen]
    refresh = enrich_refresh(
        [o for o in opps if o["verdict"] == "REFRESH"], pages, ledger, site)
    hub_gaps = [o for o in opps if o["kind"] == "brandhub"][:10]

    if not allowed and not refresh:
        die("רשימת הנושאים המותרים ריקה. אין הזדמנות שעוברת את השערים")

    for o in allowed:
        o["video"] = match_video(o["query"], videos)
    # v1.6: התאמת וידאו רצה רק על allowed_topics. מאמר Refresh לא קיבל
    # סרטון כלל, למרות ש-VIDEO_MISSING אמור לחול גם עליו (נצפה 2026-08-10).
    for r in refresh:
        q = r.get("existing_h1") or (r["triggers"][0]["query"] if r.get("triggers") else "")
        r["video"] = match_video(q, videos) if q else None
    n_vid = sum(1 for o in allowed if o["video"]) + sum(1 for r in refresh if r.get("video"))

    brief = {
        "site": site, "domain": SITES[site],
        "pal_lint_version": lint,
        "ledger_rows": len(ledger),
        "gsc_pages": len(pages),
        "vocabulary_size": len(vocab),
        "vocabulary": sorted(vocab),               # מלא. TERM_VERIFY מצליב מולו
        "vocabulary_top": [w for w, _ in vocab.most_common(60)],   # לתצוגה בלבד

        "allowed_topics": allowed,
        "refresh_queue": refresh,
        "brand_hub_gaps": hub_gaps,
        # עמודים ששולטים בשאילתה מסחרית (מיקום 1-3). אסור לכתוב עליהם
        # מאמר מתחרה. הם כתובת לקישור פנימי ממאמרים חדשים ומרועננים.
        "dominant_pages": dominated,
        "dominant_rule": ("אלה נכסים שלנו במקום 1-3. אל תכתוב מאמר על השאילתה "
                          "שלהם, וקשר אליהם ממאמרים רלוונטיים כדי לחזק אותם."),
        # שאילתות שתפוסות על ידי עמוד שותף בדומיין שלנו
        "partner_dominated": partner_dom,
        "partner_rule": ("עמודי שותפים. אסור לקשר אליהם (FORBIDDEN_LINK) ואין "
                         "לכתוב עליהם מאמר מתחרה. ההזדמנות היא עמוד /brands/."),
        "brand_hubs": brand_hubs,        # עמודי המותג הקיימים — חובה לקשר אליהם
        "pricing": PRICING.get(site, {}),   # שאלה מסחרית = תשובה במספר
        "ai_agent": AI_AGENT.get(site),
        "self_service": SELF_SERVICE.get(site),
        "channel_priority": (
            "כשמזכירים תיאום התקנה או יצירת קשר: ערוץ ה-AI ראשון ומומלץ "
            "(24/7, בלי המתנה), מוקד טלפוני כחלופה. המטרה להסיט עומס מהמוקד."
        ) if AI_AGENT.get(site) else None,
        "page_intent_rules": PAGE_INTENT,
        "conversion_rule": ("שאלה על מחיר או זמן חייבת תשובה עם המספר מ-pricing. "
                            "\"תלוי, פנו אלינו\" נחסם ב-EVASIVE_ANSWER."),
        "video_catalog_size": len(videos),
        "brand_hub_link_rule": "כל מאמר חייב לפחות קישור אחד ל-/brands/ (BRAND_HUB_MISSING)",
        "canonical_sentences": canonical_sentences(site),
        "h1_variants": h1_variant(pages, allowed[0]["query"]) if allowed else [],
        "mcp_requests": [
            {"tool": "woocommerce:get_page_html",
             "args": {"site": site, "url": f"https://{SITES[site]}/blog/"},
             "purpose": "רשימת כותרות חיות — שכבת דדופ שלישית"},
            {"tool": "woocommerce:search_products",
             "args": {"site": site, "query": "<מונח מהנושא הנבחר>"},
             "purpose": "מוצרים לכרטיס Hero, permalink/מחיר/תמונה verbatim"},
            {"tool": "web_search + web_fetch",
             "args": {"query": "<שאילתת היעד>", "top": 5},
             "purpose": "H2 של המתחרים → competitor_headings, ל-INFO_GAIN_DIFF"},
        ],
    }
    # v1.7: פיצול ל-brief רזה ולנספח כבד.
    # ה-brief המלא היה 197KB (~90K טוקנים) — הסשן קרא אותו בשלמותו וזה
    # מה שאכל את חלון הפלט וגרם ללחיצות "המשך" חוזרות (נצפה 2026-08-10).
    # המודל צריך נושא אחד ואוצר מילים לבדיקה, לא 185 נושאים ו-6,235 מילים.
    # רק אוצר המילים באמת כבד (62KB) והוא כלי הצלבה של postflight,
    # לא חומר קריאה. כל השאר נשאר שלם: גיל עובד אוטונומית ואינו אמור
    # לבקש רשימה מלאה — הבחירה חייבת להיות שלמה מלכתחילה.
    HEAVY = ("vocabulary",)
    full = OUT / f"brief_full_{site}.json"
    full.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")

    slim = {k: v for k, v in brief.items() if k not in HEAVY}
    # כל הנושאים נשארים, אבל רק השדות שדרושים לבחירה. הטקסטים הארוכים
    # (reason, ranking_for המלא, all_domains) יורדים.
    # פורמט טבלאי במקום 185 אובייקטים: שמות השדות חוזרים פעם אחת
    # במקום 185 פעמים. אותם נתונים בדיוק, כשליש מהנפח.
    slim["topics_columns"] = ["query", "intent", "impressions", "clicks",
                              "position", "source", "video_id"]
    slim["allowed_topics_table"] = [
        [o["query"], o.get("intent", ""), o.get("impressions", 0),
         o.get("clicks", 0), o.get("best_position"),
         "AC" if o.get("source") == "autocomplete" else "GSC",
         (o.get("video") or {}).get("video_id")]
        for o in brief["allowed_topics"]]
    # חמשת המובילים גם כאובייקטים מלאים, לנוחות הבחירה
    slim["allowed_topics"] = brief["allowed_topics"][:5]
    slim["refresh_queue"] = [
        {**{k: v for k, v in r.items() if k in
            ("url", "existing_h1", "total_impressions", "total_clicks",
             "best_position", "avg_position", "ctr", "query_count",
             "frozen", "video")},
         "gap_queries": r.get("gap_queries", []),
         "ranking_for": r.get("ranking_for", [])[:5],
         "triggers": [t["query"] for t in r.get("triggers", [])[:4]]}
        for r in brief["refresh_queue"]]
    slim["brand_hub_gaps"] = [
        {k: v for k, v in o.items() if k in ("query", "impressions", "kind")}
        for o in brief["brand_hub_gaps"]]
    slim["_vocabulary_file"] = str(full)
    slim["_vocabulary_size"] = len(brief["vocabulary"])
    slim["_note"] = ("כל הנושאים כאן. אוצר המילים בלבד הוצא לקובץ נפרד — "
                     "הוא כלי הצלבה של postflight ולא חומר קריאה. "
                     "אל תטען אותו לקונטקסט.")
    p = OUT / f"brief_partial_{site}.json"
    p.write_text(json.dumps(slim, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"✅ preflight plan | {site} | pal-lint {lint} | {len(ledger)} שורות ledger | "
          f"{len(pages)} עמודים | אוצר מילים {len(vocab)}")
    n_gsc = sum(1 for o in allowed if o["source"] == "gsc")
    n_ac = len(allowed) - n_gsc
    print(f"\n📋 נושאים מותרים ({len(allowed)}): {n_gsc} מ-GSC, {n_ac} יהלומי autocomplete")
    print(f"   🎬 {n_vid} מהם עם סרטון מאומת מהערוץ ({len(videos)} בקטלוג)")
    for o in allowed[:4]:
        if o["source"] == "gsc":
            print(f"   GSC  | {o['impressions']:6d} חשיפות | pos {o['best_position']:5.1f} | {o['query'][:48]}")
        else:
            print(f"   AC   | {'—':>6s}          | {o.get('brand',''):10s} | {o['query'][:48]}")
    live_h = [h for h in brand_hubs if h["impressions"] >= 100]
    dead_h = [h for h in brand_hubs if h["impressions"] < 100]
    print(f"\n🔗 עמודי מותג קיימים ({len(brand_hubs)}): {len(live_h)} עם תנועה, "
          f"{len(dead_h)} על אפס")
    for h in brand_hubs[:3]:
        print(f"   {h['impressions']:6d} חשיפות | {h['url'].split('.co.il')[-1][:38]}")
    if dead_h:
        print(f"   ⚠️  דורשים הזנת קישורים: "
              + ", ".join(h["url"].split("/brands/")[-1].rstrip("/") for h in dead_h[:6]))
    if partner_dom:
        print(f"\n🤝 שאילתות שתפוסות ע\"י עמוד שותף ({len(partner_dom)}) — "
              f"לא לקשר, לא לשכפל. הזדמנות ל-/brands/:")
        for d in partner_dom[:3]:
            print(f"   {d['impressions']:6d} חשיפות | pos {d['position']:4.1f} | "
                  f"{d['query'][:28]:28s} → {d['url'].split('.co.il')[-1][:28]}")
    if dominated:
        print(f"\n👑 נכסים שלנו ששולטים ({len(dominated)}) — לקשר אליהם:")
        for d in dominated[:3]:
            print(f"   {d['impressions']:6d} חשיפות | pos {d['position']:4.1f} | "
                  f"{d['query'][:30]:30s} → {d['url'].split('.co.il')[-1][:32]}")
    print(f"\n🏷️  פערי brand hub ({len(hub_gaps)}) — לא נושא בלוג:")
    for o in hub_gaps[:2]:
        print(f"   {o['impressions']:6d} | {o['query'][:45]}")
    print(f"\n🔄 תור Refresh ({len(refresh)}) — ממוין לפי פוטנציאל:")
    for o in refresh[:3]:
        print(f"   {o['total_impressions']:7d} חשיפות | pos ממוצע {o['avg_position']:4.1f} "
              f"(מיטבי {o['best_position']:4.1f}) | CTR {o['ctr']:5.2f}% | "
              f"{len(o['gap_queries']):2d} פערים | {o['url'].split('.co.il')[-1][:40]}")
    print(f"\nנכתב: {p} ({p.stat().st_size // 1024}KB) "
          f"| מלא: {full.name} ({full.stat().st_size // 1024}KB)")
    return 0


# חובה: בלעדיהם אין דדופ ואין כרטיס Hero מאומת.
REQUIRED_MCP = {
    "live_blog_titles": "כותרות /blog/ החיות — שכבת הדדופ השלישית",
    "products": "מוצרים לכרטיס Hero (permalink/מחיר/תמונה verbatim)",
}

# רצוי: משפר את המאמר אך אינו תנאי להגשה.
# לקח 2026-08-10: competitor_headings היה ב-REQUIRED, ולכן סביבה בלי
# web_search נתקעה — או ש-finalize נעצר, או שהיא סומנה DRAFT ו-postflight
# חסם. `INFO_GAIN_DIFF` הוא WARN מלכתחילה, ואין היגיון שהמקור שלו יחסום.
OPTIONAL_MCP = {
    "competitor_headings": "H2 של המתחרים — מזין את INFO_GAIN_DIFF (WARN)",
}


def phase_finalize(site, mcp_path, allow_degraded=False):
    full = OUT / f"brief_full_{site}.json"
    p = full if full.exists() else OUT / f"brief_partial_{site}.json"
    if not p.exists():
        die("brief חסר. הרץ קודם --phase plan")
    brief = json.loads(p.read_text(encoding="utf-8"))
    mcp = json.loads(Path(mcp_path).read_text(encoding="utf-8"))

    missing = [k for k in REQUIRED_MCP if not mcp.get(k)]
    if missing:
        lines = ["נתוני MCP חסרים ב-" + mcp_path + ":"]
        lines += [f"   • {k} — {REQUIRED_MCP[k]}" for k in missing]
        if not allow_degraded:
            lines += ["",
                      "השרת כנראה אינו פעיל. הפעל אותו והרץ שוב, או:",
                      "   --allow-degraded  → טיוטה מסומנת DRAFT.",
                      "                       postflight יחסום אותה. לא לפרסום."]
            die("\n".join(lines))
        print("⚠️  " + "\n⚠️  ".join(lines))
        print("⚠️  מצב DRAFT: הפלט אינו בר-פרסום.")
    live = [t.strip() for t in mcp.get("live_blog_titles", []) if t.strip()]
    if not live and not allow_degraded:
        die("live_blog_titles ריק — שכבת הדדופ השלישית לא רצה")
    # v1.1 — תיקון באג קריטי (2026-08-04): הגרסה הקודמת חיברה את כל הכותרות
    # למחרוזת אחת וספרה מילים שמופיעות *איפשהו* בבלוב, בסף 2. באתר עם היסטוריה
    # "מקרר"/"שארפ"/"חלקי" מופיעות בעשרות כותרות, ולכן 23/23 הנושאים נדחו.
    # התיקון: השוואה מול כל כותרת בנפרד, עם נרמול תחיליות וסף 80% מהמילים.
    # השכבה נועדה לתפוס מאמר שפורסם וטרם נרשם בלדג'ר, לא חפיפת מילים מקרית.
    HEB_PREFIX = ("וה", "שה", "בה", "לה", "מה", "כש", "ה", "ו", "ב", "ל", "מ", "ש", "כ")

    HEB_SUFFIX = ("יות", "ים", "ות")

    def _norm(w):
        for pre in HEB_PREFIX:
            if w.startswith(pre) and len(w) - len(pre) >= 3:
                w = w[len(pre):]
                break
        for suf in HEB_SUFFIX:          # רבים: "מקררים" = "מקרר"
            if w.endswith(suf) and len(w) - len(suf) >= 3:
                return w[: -len(suf)]
        return w

    def _sig(text):
        return [w for w in re.findall(r"[\u0590-\u05FFA-Za-z0-9]+", text) if len(w) > 3]

    def _same(a, b):
        """
        התאמה דו-כיוונית ולא נרמול חד-כיווני. "מקרר" מתחיל ב-מ ונרמול עיוור
        הופך אותו ל"קרר", בעוד "למקרר" הופך ל"מקרר" — שתי צורות שלא נפגשות.
        לכן משווים גם raw וגם מנורמל, משני הצדדים.
        """
        return a == b or _norm(a) == b or a == _norm(b) or _norm(a) == _norm(b)

    live_sets = [(t, _sig(t)) for t in live]

    def is_published(query):
        q = _sig(query)
        if len(q) < 2:
            return None
        for title, tw in live_sets:
            if not tw:
                continue
            hits = sum(1 for a in q if any(_same(a, b) for b in tw))
            if hits / len(q) >= 0.8:
                return title
        return None

    before = len(brief["allowed_topics"])
    kept, dropped = [], []
    for o in brief["allowed_topics"]:
        hit = is_published(o["query"])
        if hit:
            dropped.append((o["query"], hit))
        else:
            kept.append(o)
    brief["allowed_topics"] = kept
    for q, t in dropped:
        print(f"   סונן ככפילות: \"{q}\" ← כבר פורסם: \"{t[:45]}\"")
    brief["live_blog_titles"] = live
    brief["products"] = mcp.get("products", [])
    brief["brand_hub"] = mcp.get("brand_hub")
    brief["verified_links"] = mcp.get("verified_links", [])
    brief["competitor_headings"] = mcp.get("competitor_headings", [])
    missing_opt = [k for k in OPTIONAL_MCP if not mcp.get(k)]
    if missing_opt:
        for k in missing_opt:
            print(f"ℹ️  {k} חסר — {OPTIONAL_MCP[k]}. לא חוסם.", file=sys.stderr)
        brief["optional_missing"] = missing_opt
    brief["degraded"] = bool(missing)
    if missing:
        brief["degraded_missing"] = missing
    brief["dedup_layers"] = ["content-ledger", "GSC position", "live /blog/ titles"]
    if not brief["allowed_topics"]:
        die("כל הנושאים נפסלו בשכבת הכותרות החיות")

    out = OUT / f"brief_{site}.json"
    out.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ preflight finalize | {before} → {len(brief['allowed_topics'])} נושאים מותרים "
          f"אחרי סינון {len(live)} כותרות חיות")
    print(f"   מוצרים: {len(brief['products'])} | brand hub: {'כן' if brief['brand_hub'] else 'לא'}")
    print(f"נכתב: {out}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=list(SITES))
    ap.add_argument("--phase", required=True, choices=["plan", "finalize"])
    ap.add_argument("--mcp")
    ap.add_argument("--allow-degraded", action="store_true",
                    help="המשך בלי נתוני MCP. הפלט מסומן DRAFT ו-postflight חוסם אותו")
    a = ap.parse_args()
    if a.phase == "plan":
        return phase_plan(a.site)
    if not a.mcp:
        die("--mcp נדרש ב-finalize")
    return phase_finalize(a.site, a.mcp, a.allow_degraded)


if __name__ == "__main__":
    sys.exit(main())
