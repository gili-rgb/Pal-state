#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pal-lint — שכבת אכיפה דטרמיניסטית לכל פלט HTML של Pal Group.
stdlib בלבד. אפס תלויות. אפס צעדים ידניים.

שימוש:
    python3 pal_lint.py FILE.html [--site csb|marom|plrom] [--type blog|brandhub|product] [--json]

Exit code: 0 = ירוק (מותר להגיש) | 1 = ERROR קיים (אסור להגיש) | 2 = שגיאת קלט
site לא סופק => זיהוי אוטומטי לפי דומיינים בקובץ.
type לא סופק => auto (brandhub אם יש bh- classes, אחרת blog).
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

VERSION = "1.1.0"  # v1.1.0 (2026-07-05): נוספו חוסמי Elementor שחסרו מול VALIDATE של הסקילים — unicode-bidi, SVG inline, data-ga-event, target=_blank, U+2011/U+00AD/U+200B, איזון סוגריי CSS, @media מקונן, href ריק, תגיות לא מאוזנות

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
        "phone_ok": ["*2620"],
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

# טרמינולוגיה: אסור => (חלופה, חומרה)
TERMS_ERROR = {
    "פד שוחק": "ספוג שוחק",
    "ווי פח": "תופסני מתכת",
    "פריג'": "מקרר",
    "כלונסאות": "מסילות הצד",
    "סילוני מים": "ממטרה",
    "פלינטוס": "צוקל",
}
TERMS_WARN = {
    "פקקים": "ספייסר (אם הכוונה לחלק מרווח)",
    "פיר": "מוט החיבור (אם הכוונה לחלק המסתובב)",
}

FORBIDDEN_DOMAINS = ["jeepolog.com"]

HEB_RANGE = "\u0590-\u05FF"

# ---------------------------------------------------------------- עזרים

def strip_blocks(html, tag):
    return re.sub(rf"<{tag}\b.*?</{tag}>", " ", html, flags=re.S | re.I)

def visible_text(html):
    t = strip_blocks(strip_blocks(html, "script"), "style")
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return t

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
        rep.err("CSS_VAR", "שימוש ב-var(--…) — Elementor דורש hex קשיח בלבד")
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
    """חוסמי Elementor שהיו רק ב-VALIDATE המוטמע בסקילים — v1.1.0 מיישר לכיסוי מלא."""
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
    if doc_type == "brandhub":
        for u in re.findall(r'href="([^"]+)"', html):
            if u.count("%D7") + u.count("%d7") >= 4:
                rep.err("BRANDHUB_ENCODED", f"widget של brand-hub חייב URL עברי גולמי (WAF חוסם %XX ארוך): {u[:90]}")

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
            if p in low:
                rep.err("FORBIDDEN_LINK", f"קישור אסור באתר {site}: {u[:90]}")
        if cfg["forbidden_pc"] and "/product-category/" in low and cfg["domain"] in low:
            rep.err("FORBIDDEN_PC", f"product-category אסור בפלרום: {u[:90]}")
        if ".xml" in low and "sitemap" in low:
            rep.err("XML_SITEMAP", f"sitemap XML אסור — HTML בלבד ({cfg['sitemap_ok']}): {u[:90]}")
        # כתובות אחרים: קישור פנימי לדומיין של אתר אחר
        for other, ocfg in SITES.items():
            if other != site and ocfg["domain"] in low:
                rep.warn("CROSS_SITE_LINK", f"קישור לדומיין של אתר אחר ({other}): {u[:90]}")

def check_terms(html, rep):
    text = visible_text(html)
    for bad, good in TERMS_ERROR.items():
        for m in re.finditer(re.escape(bad), text):
            rep.err("TERM", f"מונח אסור \"{bad}\" => \"{good}\"")
    for bad, good in TERMS_WARN.items():
        pat = rf"(?<![{HEB_RANGE}]){re.escape(bad)}(?![{HEB_RANGE}])"
        for m in re.finditer(pat, text):
            rep.warn("TERM_CTX", f"מונח חשוד \"{bad}\" — אם מדובר בחלק: \"{good}\"")

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
        # דלונגי מכונות קפה + שירות רשמי
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

def check_jsonld(html, rep, site):
    cfg = SITES[site]
    blocks = re.findall(r"<script[^>]*ld\+json[^>]*>(.*?)</script>", html, flags=re.S | re.I)
    if not blocks:
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
        for ent in graph:
            if not isinstance(ent, dict):
                continue
            t = ent.get("@type", "")
            types = t if isinstance(t, list) else [t]
            if "Product" in types and "offers" not in ent:
                rep.err("SCHEMA_OFFERS", "Product schema בלי offers block (שגיאת GSC ידועה)")
            if "Product" in types and "offers" in ent:
                off = ent["offers"]
                offs = off if isinstance(off, list) else [off]
                for o in offs:
                    if isinstance(o, dict) and o.get("priceCurrency") not in (None, "ILS"):
                        rep.err("SCHEMA_CURRENCY", f"priceCurrency={o.get('priceCurrency')} — חייב ILS")
            if "LocalBusiness" in types:
                addr = json.dumps(ent.get("address", {}), ensure_ascii=False)
                tel = str(ent.get("telephone", ""))
                if cfg["nap_street"] not in addr:
                    rep.err("NAP_ADDR", f"כתובת LocalBusiness לא תואמת NAP ({cfg['nap_street']}, {cfg['nap_city']})")
                if cfg["phone_ok"] and not any(p in tel for p in cfg["phone_ok"]):
                    rep.err("NAP_PHONE", f"טלפון LocalBusiness \"{tel}\" לא תואם NAP (נכון: {cfg['phone_ok'][0]})")

def check_video(html, rep):
    for m in re.finditer(r'class="[^"]*video-container[^"]*"', html):
        seg = html[m.start():m.start() + 1200]
        src = re.search(r'src="([^"]*)"', seg)
        if not src or not re.search(r"youtube\.com/embed/[\w-]{6,}", src.group(1)):
            rep.err("VIDEO_PLACEHOLDER", "video-container בלי embed תקין — הכלל: אין וידאו רשמי מאומת = למחוק את הבלוק כולו")
    if re.search(r"PLACEHOLDER|VIDEO_ID_HERE|YOUR_VIDEO", html):
        rep.err("PLACEHOLDER", "placeholder גולמי נשאר בקובץ")

def check_sentences(html, rep):
    text = visible_text(html)
    # רק משפטים עבריים בגוף
    sents = re.split(r"[.!?:]\s", text)
    heb = [s.strip() for s in sents if len(re.findall(rf"[{HEB_RANGE}]", s)) > 10]
    if not heb:
        return
    long_s = [s for s in heb if len(s.split()) > 15]
    pct = round(100 * len(long_s) / len(heb))
    rep.note(f"משפטים: {len(heb)} | ארוכים (>15 מילים): {len(long_s)} ({pct}%)")
    if pct > 25:
        rep.warn("YOAST_LEN", f"{pct}% מהמשפטים מעל 15 מילים (Yoast עברית) — לקצר לפני הגשה")
    words = re.findall(rf"[{HEB_RANGE}]+", text)
    rep.note(f"מילים בעברית: {len(words)}")

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

def detect_type(html):
    if "bh-" in html or "brand-hub" in html:
        return "brandhub"
    return "blog"

def run(path, site=None, doc_type=None):
    html = Path(path).read_text(encoding="utf-8")
    html = unicodedata.normalize("NFC", html)
    rep = Report()
    site = site or detect_site(html)
    if site is None:
        rep.warn("SITE_UNKNOWN", "לא זוהה אתר — בדיקות per-site דולגו. העבר --site")
    doc_type = doc_type or detect_type(html)
    rep.note(f"pal-lint v{VERSION} | site={site or '?'} | type={doc_type} | {Path(path).name}")

    check_emdash(html, rep)
    check_css(html, rep)
    check_backslash(html, rep)
    check_elementor_blockers(html, rep)
    check_percent_encoding(html, rep, doc_type)
    check_terms(html, rep)
    check_video(html, rep)
    check_encoding_junk(html, rep)
    check_sentences(html, rep)
    for d in FORBIDDEN_DOMAINS:
        if d in html.lower():
            rep.err("FORBIDDEN_SOURCE", f"אזכור מקור אסור: {d}")
    if site:
        check_links(html, rep, site)
        check_expert(html, rep, site)
        check_phones(html, rep, site)
        check_brand_scope(html, rep, site)
        check_jsonld(html, rep, site)
    return rep, site, doc_type

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--site", choices=list(SITES))
    ap.add_argument("--type", dest="doc_type", choices=["blog", "brandhub", "product"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not Path(a.file).exists():
        print(f"קובץ לא קיים: {a.file}", file=sys.stderr)
        sys.exit(2)
    rep, site, dt = run(a.file, a.site, a.doc_type)
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
        print("—" * 0)
        print(f"\nתוצאה: {'✅ ירוק — מותר להגיש' if not rep.errors else f'🔴 {len(rep.errors)} שגיאות — אסור להגיש'} | אזהרות: {len(rep.warns)}")
    sys.exit(0 if not rep.errors else 1)

if __name__ == "__main__":
    main()
