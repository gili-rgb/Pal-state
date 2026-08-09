#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_contamination_scan.py — סריקת זיהום תוכן בתיאורי מוצרים חיים.

הרקע (2026-08-09, ריצת אימות CSB): `get_product_by_sku` החזיר תיאורי מוצר
שמכילים תוכן שנוצר במודל שפה והודבק ישירות לאתר, כולל `class` בשם
`font-claude-response-body` בתוך ה-HTML, וטענות מספריות מומצאות:
"30 שנות ניסיון", "עמידות פי 3", "לקוחות שניסו לתקן נכשלו תוך שבועיים".

זו אינה תקלה טכנית אלא חשיפה עסקית: טענות מספריות שאין להן מקור, על עמוד
מוצר מסחרי, מול לקוחות ומול גוגל.

הסקריפט קורא בלבד. הוא אינו משנה דבר באתר.

הרצה מסשן עם WooCommerce MCP פעיל:
    1. הרץ  --emit-plan  כדי לקבל את רשימת קריאות ה-MCP
    2. שמור את התוצאות ל-products.json  (מערך של אובייקטי מוצר מה-MCP)
    3. הרץ  --scan products.json --site csb

פלט: contamination_report.md + contamination.json
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

OUT = Path("/home/claude/contamination")

# --- חתימות ודאיות: נוכחותן מספיקה כדי לסמן זיהום ---
HARD = {
    "font-claude-response-body": "class של ממשק צ'אט בתוך HTML של מוצר",
    "font-claude-response": "class של ממשק צ'אט",
    "data-start=": "מאפיין עורך של ממשק צ'אט",
    "data-end=": "מאפיין עורך של ממשק צ'אט",
    "sk-ant-": "מזהה פנימי שאינו אמור להופיע בתוכן",
    "As an AI": "טקסט מודל שדלף",
    "כמודל שפה": "טקסט מודל שדלף",
    "אני לא יכול": "סירוב של מודל שדלף לתוך התוכן",
    "[PENDING": "placeholder פנימי שלא הוחלף",
    "TODO": "placeholder שלא הוחלף",
    "lorem ipsum": "טקסט מילוי",
}

# --- טענות מספריות: כל אחת דורשת מקור, ובלעדיו אסורה ---
CLAIMS = [
    (r"\b\d{1,3}\s*(?:שנות|שנים)\s+(?:ניסיון|נסיון|מומחיות)", "טענת ותק"),
    (r"פי\s*\d+(?:\.\d+)?\s*(?:יותר|עמיד|חזק|ארוך|טוב)", "טענת יחס"),
    (r"\b\d{1,3}%\s*(?:מה?לקוחות|מהמקרים|מהתקלות|חיסכון|יותר|פחות)", "טענת אחוזים"),
    (r"(?:מעל|למעלה מ)\s*\d{2,}\s*(?:לקוחות|תיקונים|מכשירים)", "טענת היקף"),
    (r"\b\d+\s*(?:מתוך|/)\s*\d+\s*לקוחות", "טענת יחס לקוחות"),
    (r"(?:נכשל|נכשלו)\s+תוך\s+\w+", "טענת כישלון מתחרים"),
    (r"(?:הטוב ביותר|המוביל|מספר\s*1|אין תחליף|ללא תחרות)", "סופרלטיב"),
    (r"מובטח\s+ל?\d+", "התחייבות מספרית"),
]


def emit_plan(site):
    print(f"""# תוכנית סריקה — {site}

הרץ מסשן עם WooCommerce MCP פעיל:

1. `search_products` עם מונחים רחבים לכיסוי הקטלוג, למשל:
   פילטר, משאבה, אטם, מדף, מגש, ידית, תרמוסטט, מנוע, צינור, לחצן,
   ממטרה, סלסלה, גומי, נורה, מיסב, רצועה, ציר, מתג, חיישן, כבל
2. לכל מוצר שחוזר, קרא `get_product_by_sku`
3. שמור מערך JSON אחד עם: sku, name, permalink, description, short_description
4. הרץ:  python3 content_contamination_scan.py --scan products.json --site {site}

הסקריפט קורא בלבד ואינו משנה דבר באתר.
""")
    return 0


def scan_one(prod):
    blobs = {
        "description": prod.get("description") or "",
        "short_description": prod.get("short_description") or "",
    }
    hits = []
    for field, text in blobs.items():
        low = text.lower()
        for sig, why in HARD.items():
            if sig.lower() in low:
                hits.append({"type": "HARD", "field": field,
                             "signature": sig, "why": why})
        for pat, label in CLAIMS:
            for m in re.finditer(pat, text):
                hits.append({"type": "CLAIM", "field": field, "label": label,
                             "text": m.group()[:80]})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, choices=["csb", "marom", "plrom"])
    ap.add_argument("--emit-plan", action="store_true")
    ap.add_argument("--scan")
    a = ap.parse_args()

    if a.emit_plan or not a.scan:
        return emit_plan(a.site)

    prods = json.loads(Path(a.scan).read_text(encoding="utf-8"))
    if isinstance(prods, dict):
        prods = prods.get("products", [])
    OUT.mkdir(parents=True, exist_ok=True)

    flagged, n_hard, n_claim = [], 0, 0
    for p in prods:
        hits = scan_one(p)
        if not hits:
            continue
        n_hard += sum(1 for h in hits if h["type"] == "HARD")
        n_claim += sum(1 for h in hits if h["type"] == "CLAIM")
        flagged.append({"sku": p.get("sku", ""), "name": (p.get("name") or "")[:80],
                        "permalink": p.get("permalink", ""), "hits": hits})

    flagged.sort(key=lambda f: -sum(1 for h in f["hits"] if h["type"] == "HARD"))
    (OUT / "contamination.json").write_text(
        json.dumps({"site": a.site, "date": str(date.today()),
                    "scanned": len(prods), "flagged": flagged},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    L = [f"# זיהום תוכן — {a.site}", "",
         f"נסרקו **{len(prods)}** מוצרים. נמצאו **{len(flagged)}** מוצרים לטיפול.",
         "", f"- חתימות ודאיות (טקסט ממשק צ'אט שדלף): **{n_hard}**",
         f"- טענות מספריות בלי מקור: **{n_claim}**", "",
         "**הסקריפט קורא בלבד. שום דבר לא שונה באתר.**", "", "---", ""]

    hard_first = [f for f in flagged if any(h["type"] == "HARD" for h in f["hits"])]
    if hard_first:
        L += ["## דחוף — טקסט ממשק צ'אט בתוך תיאור המוצר", ""]
        for f in hard_first:
            L.append(f"### {f['name']} (`{f['sku']}`)")
            L.append(f"{f['permalink']}")
            for h in f["hits"]:
                if h["type"] == "HARD":
                    L.append(f"- 🔴 `{h['signature']}` ב-{h['field']} — {h['why']}")
            # הטענות במוצר מזוהם חשובות לא פחות מהחתימה — הן מה שהלקוח קורא
            for h in f["hits"]:
                if h["type"] == "CLAIM":
                    L.append(f"- ⚠️ {h['label']}: \"{h['text']}\"")
            L.append("")

    only_claims = [f for f in flagged if f not in hard_first]
    if only_claims:
        L += ["## טענות מספריות שדורשות מקור או הסרה", ""]
        for f in only_claims:
            L.append(f"### {f['name']} (`{f['sku']}`)")
            L.append(f"{f['permalink']}")
            for h in f["hits"]:
                L.append(f"- ⚠️ {h['label']}: \"{h['text']}\"")
            L.append("")

    L += ["---", "",
          "**מה לעשות עם כל ממצא:** חתימה ודאית = להסיר את הקטע כולו ולכתוב מחדש. ",
          "טענה מספרית = למחוק, או להחליף בעובדה מאומתת עם מקור. ",
          "אין להשאיר טענה מספרית בלי מקור בעמוד מסחרי."]
    (OUT / "contamination_report.md").write_text("\n".join(L), encoding="utf-8")

    print(f"נסרקו {len(prods)} | לטיפול {len(flagged)} | "
          f"חתימות ודאיות {n_hard} | טענות {n_claim}")
    print(f"נכתב: {OUT}/contamination_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
