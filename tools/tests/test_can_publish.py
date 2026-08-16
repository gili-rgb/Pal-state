#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_can_publish.py — האם עדיין אפשר לסיים ריצה.

**זו הבדיקה שהייתה חסרה, וזו הסיבה שהיא נכתבה.**

כל שער במערכת נבדק מול fixture משלו: "האם הכלל תופס את מה שהוא אמור לתפוס".
אף בדיקה לא שאלה את השאלה ההפוכה: **"האם עדיין אפשר לכתוב מאמר".**

מה שקרה ב-2026-08-06: `BRAND_HUB_MISSING` נוסף כ-ERROR גורף שדורש קישור
ל-/brands/ בכל מאמר בלוג. לפלרום אפס עמודי /brands/. מאותו רגע **כל מאמר
פלרום היה בלתי אפשרי לפרסום**, והחסימה שרדה עשרה ימים בלי שאיש ידע: ה-CI
היה ירוק, selftest עבר, וכל 100 הכללים עבדו בדיוק כמתוכנן.

הבדיקה הזו מחזיקה מאמר מינימלי-תקין לכל אתר ודורשת ממנו `exit 0`.
כלל חדש שחוסם אותו נופל ב-CI **באותו יום שהוא נוסף**, ולא עשרה ימים אחרי.

**כלל תחזוקה:** כשמאמר כאן נכשל, בררו קודם האם הכלל צודק. אם כן, עדכנו את
המאמר. אם לא, הכלל שגוי. **אסור להחליש את הבדיקה כדי שתעבור.**

רץ ב-CI כשער שמיני. exit 1 בכשל.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
FAILED = []


def check(name, got, want):
    if got == want:
        print(f"✅ {name}")
    else:
        FAILED.append(f"{name}: קיבלתי {got!r}, ציפיתי {want!r}")


def article(*, h1, body, org, links, phone, person=None):
    person_block = f',{person}' if person else ''
    link_html = "\n".join(
        f'<p>{txt} <a href="{u}">{anchor}</a>.</p>' for u, anchor, txt in links)
    return f"""<style>
.blog-article {{ color: #16232e; font-size: 18px; }}
.blog-article h2 {{ color: #123456; margin: 16px 0; }}
</style>
<h1>{h1}</h1>
<p class="direct-answer">{body}</p>
{link_html}
<p>לתיאום שירות חייגו {phone}.</p>
<script type="application/ld+json">
{{"@context":"https://schema.org","@graph":[{org}{person_block}]}}
</script>
"""


ORG = {
    "csb": ('{"@type":"Organization","@id":"https://csb.co.il/#content-organization",'
            '"name":"סי.אס.בי מוצרי חשמל","telephone":"08-977-7222",'
            '"url":"https://csb.co.il","sameAs":["https://www.youtube.com/@csbinc"]}'),
    "marom": ('{"@type":"Organization","@id":"https://marom-serv.co.il/#content-organization",'
              '"name":"מרום שירותים ואחזקה","telephone":"*2620",'
              '"url":"https://marom-serv.co.il","sameAs":["https://www.youtube.com/@user-marom-serv"]}'),
    "plrom": ('{"@type":"Organization","@id":"https://plrom.co.il/#content-organization",'
              '"name":"פלרום שירותים ואחזקה","telephone":"073-2625600",'
              '"url":"https://plrom.co.il","sameAs":["https://www.youtube.com/@plrom"]}'),
}

CASES = {
    "csb": dict(
        h1="מדיח בוש לא מנקז מים: חמש בדיקות לפני הזמנת טכנאי",
        body="ביקור טכנאי של סי.אס.בי עולה 349 ש\"ח, לא כולל חלקים. בתקופת האחריות אין עלות.",
        phone="08-977-7222",
        links=[("https://csb.co.il/brands/bosch-service/", "עמוד המותג בוש", "פרטים מלאים"),
               ("https://csb.co.il/bosch-categories/", "חלפים מקוריים לבוש", "חלקי חילוף"),
               ("https://csb.co.il/צור-קשר-שירות-לקוחות-סי-אס-בי/", "פתיחת קריאת שירות", "לתיאום"),
               ("https://csb.co.il/sitemap-2/", "מפת האתר", "ניווט")],
        person=('{"@type":"Person","@id":"https://csb.co.il/#content-author",'
                '"name":"אילן שמה","jobTitle":"מנהל השירות הטכני",'
                '"worksFor":{"@id":"https://csb.co.il/#content-organization"}}'),
    ),
    "marom": dict(
        h1="מקרר שארפ לא מקרר: ארבע סיבות נפוצות ואיך בודקים",
        body="ביקור טכנאי של מרום עולה 290 ש\"ח לכל המוצרים.",
        phone="*2620",
        links=[("https://marom-serv.co.il/brands/sharp-service/", "עמוד המותג שארפ", "פרטים מלאים"),
               ("https://marom-serv.co.il/product-category/sharp/", "חלפים מקוריים לשארפ", "חלקי חילוף"),
               ("https://marom-serv.co.il/צור-קשר/", "פתיחת קריאת שירות", "לתיאום"),
               ("https://marom-serv.co.il/sitemap/", "מפת האתר", "ניווט")],
        person=('{"@type":"Person","@id":"https://marom-serv.co.il/#content-author",'
                '"name":"מיכה איתן","jobTitle":"מנהל טכני ויבוא",'
                '"worksFor":{"@id":"https://marom-serv.co.il/#content-organization"}}'),
    ),
    # פלרום: בלי ישות Person (v8.15) ובלי קישור /brands/ (אין עמודים כאלה).
    "plrom": dict(
        h1="מדיח מילה לא מתייבש: שלוש בדיקות לפני קריאת טכנאי",
        body="ביקור טכנאי בבית למילה או ליבהר עולה 390 ש\"ח כולל מע\"מ.",
        phone="073-2625600",
        links=[("https://plrom.co.il/miele/", "עמוד מילה", "פרטים מלאים"),
               ("https://plrom.co.il/liebherr/", "עמוד ליבהר", "מותג נוסף"),
               ("https://plrom.co.il/צור-קשר/", "פתיחת קריאת שירות", "לתיאום"),
               ("https://plrom.co.il/sitemap/", "מפת האתר", "ניווט")],
        person=None,
    ),
}

d = Path(tempfile.mkdtemp(prefix="can_publish_"))
for site, spec in CASES.items():
    f = d / f"{site}.html"
    f.write_text(article(org=ORG[site], **spec), encoding="utf-8")
    r = subprocess.run([sys.executable, str(TOOLS / "pal_lint.py"), str(f),
                        "--site", site, "--type", "blog"],
                       capture_output=True, text=True)
    out = r.stdout + r.stderr
    errors = re.findall(r"❌ \[([A-Z_]+)\]", out)
    # שדות שהמאמר המינימלי אינו מדמה (אורך, FAQ, TOC) אינם נבדקים כאן.
    blocking = [e for e in errors if e not in {"YOAST_WORDS", "SCHEMA_MISSING"}]
    check(f"{site}: מאמר מינימלי-תקין עובר את pal-lint", blocking, [])
    if blocking:
        FAILED.append(f"   {site} נחסם ב: {', '.join(blocking)}")

# הרגרסיה המדויקת של 2026-08-06: פלרום אינה דורשת קישור /brands/.
import importlib.util
spec = importlib.util.spec_from_file_location("pl", TOOLS / "pal_lint.py")
pl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pl)
check("פלרום: brand_hub_required=False (אין לה עמודי /brands/)",
      pl.SITES["plrom"]["brand_hub_required"], False)
check("CSB: brand_hub_required=True", pl.SITES["csb"]["brand_hub_required"], True)
check("מרום: brand_hub_required=True", pl.SITES["marom"]["brand_hub_required"], True)

if FAILED:
    print("\n🔴 test_can_publish נכשל — כלל חוסם מאמר תקין:")
    for f in FAILED:
        print("   " + f)
    print("\n   בררו קודם האם הכלל צודק. אל תחלישו את הבדיקה כדי שתעבור.")
    sys.exit(1)
print("\n✅ test_can_publish עבר — שלושת האתרים יכולים לפרסם")
