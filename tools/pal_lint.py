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

VERSION = "1.2.0"
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
        "phone_ok": ["08-977-7222", "089777222", "08-9777222"],
        "phone_bad": [],
        "nap_street": "הצורפים 3",
        "nap_city": "לוד",
        "sitemap_ok": "csb.co.il/sitemap-2/",
        "forbidden_paths": [
            "/bosch-service/", "/siemens-service/",
            "/bosch-parts/", "/siemens-parts/",
        ],
        "forbidden_pc": False,  # product-category מותר
    },
    "marom": {
        "domain": "marom-serv.co.il",
        "expert": "מיכה איתן",
        "wrong_experts": ["דניאל", "סמי", "אילן שמה"],
        # קנוני: *2620 (הכוכבית לפני הספרות — הכרעת גיל 2026-07-05). 2620* מתקבל בעמודים קיימים.
        "phone_ok": ["*2620", "2620*"],
        "phone_bad": ["03-9799799", "039799799", "03-979-9799"],
        "nap_street": "הצורף 3",
        "nap_city": "חולון",
        "sitemap_ok": "marom-serv.co.il/sitemap/",
        "forbidden_paths": [
            f"/{b}-{k}/"
            for b in ["sharp", "dedietrich", "bauknecht", "haier",
                      "blomberg", "delonghi", "amana", "zanussi"]
            for k in ["parts", "service"]
        ],
        "forbidden_pc": False,  # product-category מותר
    },
    "plrom": {
        "domain": "plrom.co.il",
        "expert": "דניאל",
        "wrong_experts": ["מיכה", "סמי", "אילן שמה"],
        "phone_ok": ["073-2625600", "0732625600", "073-262-5600"],
        "phone_bad": [],
        "nap_street": "ישראל זמורה 2",
        "nap_city": "לוד",
        "sitemap_ok": "plrom.co.il/sitemap/",
        "forbidden_paths": [
            "/sauter-service/", "/liebherr-service/",
            "/miele-service/", "/miele-parts/",
        ],
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

def check_links(html, rep, site):
    cfg = SITES[site]
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
        if ".xml" in low and "sitemap" in low:
            rep.err("XML_SITEMAP", f"sitemap XML אסור — HTML בלבד ({cfg['sitemap_ok']}): {u[:90]}")
        if "myarea." in low and not re.search(r"/login/?$", low):
            rep.err("CTA_LOGIN", f"קישור myarea בלי /login/ בסוף — יעד CTA אחיד חובה: {u[:90]}")
        for other, ocfg in SITES.items():
            if other != site and ocfg["domain"] in low:
                rep.warn("CROSS_SITE_LINK", f"קישור לדומיין של אתר אחר ({other}): {u[:90]}")
    # link_audit: חילוץ הקישורים הפנימיים לאימות web_fetch חי (HTTP מהסנדבוקס חסום ב-WAF)
    internal = sorted({u for u in re.findall(r'href="([^"#][^"]*)"', html)
                       if cfg["domain"] in u})
    if internal:
        rep.note("link_audit — אמת web_fetch חי (200 + canonical זהה) לכל קישור פנימי:")
        for u in internal:
            rep.note(f"   fetch: {u}")

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
            rep.err("EXPERT", f"שם מומחה שגוי לאתר {site}: \"{wrong}\" (נכון: {cfg['expert']})")

def check_phones(html, rep, site):
    cfg = SITES[site]
    for bad in cfg["phone_bad"]:
        if bad in html:
            rep.err("PHONE", f"טלפון אסור {bad} (נכון: {cfg['phone_ok'][0]})")

def check_brand_scope(html, rep, site):
    text = visible_text(html)
    h1 = " ".join(re.findall(r"<h1[^>]*>(.*?)</h1>", html, flags=re.S | re.I))
    title = " ".join(re.findall(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I))
    head = re.sub(r"<[^>]+>", " ", h1 + " " + title)
    if site == "marom":
        if re.search(r"בקו|Beko", head, flags=re.I):
            rep.err("BRAND_BEKO", "תוכן Beko במרום אסור (כבר לא שירות רשמי)")
        elif re.search(r"בקו|Beko", text, flags=re.I):
            rep.warn("BRAND_BEKO", "אזכור Beko בגוף תוכן מרום — לוודא שאין claim לשירות רשמי")
        if re.search(r"דלונגי|DeLonghi|De'Longhi", text, flags=re.I):
            for para in re.split(r"</p>|</h[1-6]>|\n\n", visible_text(html)):
                if re.search(r"מכונ(ת|ות)\s+(ה)?קפה", para) and "שירות רשמי" in para:
                    rep.err("DELONGHI_COFFEE", "claim של \"שירות רשמי\" למכונות קפה דלונגי — מרום מתקנת אך לא רשמית (Brimag היבואן)")
        if re.search(r"מקרר", text) and re.search(r"דלונגי|DeLonghi", text, flags=re.I):
            rep.warn("DELONGHI_FRIDGE", "מקרר + דלונגי באותו תוכן — אין מקררים בליין דלונגי ישראל, לוודא")
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
        kd = round(100 * text.count(keyword) / max(len(words), 1), 2)
        rep.note(f"צפיפות '{keyword}': {kd}% (יעד 1-2)")

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
        check_links(html, rep, site)
        check_expert(html, rep, site)
        check_phones(html, rep, site)
        check_brand_scope(html, rep, site)
        if doc_type != "product":
            check_jsonld(html, rep, site, doc_type)
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
