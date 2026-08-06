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
    out = []
    for query, a in agg.items():
        if query.lower() in covered:
            continue
        if is_navigational(query, site) or is_excluded_brand(query, site):
            continue
        blog_hit = rank_for_query(pages, query, scope=blog_urls)
        if blog_hit and blog_hit[1] <= RANK_STRONG:   # מאמר בלוג כבר מדורג מצוין
            continue
        v = cannibalization_verdict(pages, query, blog_urls)
        out.append({"query": query, "kind": classify(query),
                    "impressions": a["impressions"],
                    "clicks": a["clicks"], "best_position": round(a["best_pos"], 1),
                    **v})
    out.sort(key=lambda x: -x["impressions"])
    return out[:limit]


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


def phase_plan(site):
    OUT.mkdir(exist_ok=True)
    lint = load_lint_version()
    ledger = load_ledger(site)
    pages = load_page_queries(site)
    vocab = build_vocabulary(pages, site)
    blog_urls = {r["url"] for r in ledger}
    opps = opportunities(pages, ledger, blog_urls, site, limit=150)
    allowed = [o for o in opps if o["verdict"] == "NEW" and o["kind"] == "blog"]
    refresh = [o for o in opps if o["verdict"] == "REFRESH"]
    hub_gaps = [o for o in opps if o["kind"] == "brandhub"][:10]

    if not allowed and not refresh:
        die("רשימת הנושאים המותרים ריקה. אין הזדמנות שעוברת את השערים")

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
    p = OUT / f"brief_partial_{site}.json"
    p.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"✅ preflight plan | {site} | pal-lint {lint} | {len(ledger)} שורות ledger | "
          f"{len(pages)} עמודים | אוצר מילים {len(vocab)}")
    print(f"\n📋 נושאים מותרים ({len(allowed)}):")
    for o in allowed[:10]:
        print(f"   {o['impressions']:6d} חשיפות | pos {o['best_position']:5.1f} | {o['query'][:55]}")
    print(f"\n🏷️  פערי brand hub ({len(hub_gaps)}) — לא נושא בלוג:")
    for o in hub_gaps[:4]:
        print(f"   {o['impressions']:6d} | {o['query'][:45]}")
    print(f"\n🔄 תור Refresh ({len(refresh)}) — אלה נפסלו למאמר חדש:")
    for o in refresh[:5]:
        print(f"   {o['impressions']:6d} | pos {o['position']:5.1f} | {o['query'][:40]} → {o['url'][:45]}")
    print(f"\nנכתב: {p}")
    return 0


def phase_finalize(site, mcp_path):
    p = OUT / f"brief_partial_{site}.json"
    if not p.exists():
        die("brief_partial חסר. הרץ קודם --phase plan")
    brief = json.loads(p.read_text(encoding="utf-8"))
    mcp = json.loads(Path(mcp_path).read_text(encoding="utf-8"))

    live = [t.strip() for t in mcp.get("live_blog_titles", []) if t.strip()]
    if not live:
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
    a = ap.parse_args()
    if a.phase == "plan":
        return phase_plan(a.site)
    if not a.mcp:
        die("--mcp נדרש ב-finalize")
    return phase_finalize(a.site, a.mcp)


if __name__ == "__main__":
    sys.exit(main())
