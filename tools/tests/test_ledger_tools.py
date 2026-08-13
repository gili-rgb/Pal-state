#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_ledger_tools.py — כיסוי בדיקות ל-ledger_patch.py ול-ledger_lint.py.

למה זה קיים: `ledger_patch` כותב ישירות ל-content-ledger.md, 124 שורות שהן
מקור האמת לשער ה-dedup. עד היום הוא נבדק רק בהרצה אמיתית על הקובץ האמיתי,
כלומר הבדיקה והנזק קורים באותו רגע. באג בהתאמת URL היה משכתב שורה שגויה
בשקט, ואף שער לא היה תופס את זה.

כל בדיקה רצה ב-sandbox נפרד ב-tempfile: עותק של שני הכלים ולדג'ר מינימלי,
והרצה ב-subprocess בדיוק כמו ב-CI. הקובץ האמיתי לא נוגע.

רץ ב-CI כשער שישי, לפני version_guard. exit 1 בכשל.
"""
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
FAILED = []

URL_A = "https://marom-serv.co.il/מקרר-שארפ-מצב-שבת/"
URL_B = "https://marom-serv.co.il/תנור-שארפ-ניקוי-פירוליטי/"
ROW_B = ("| 2026-04-10 | " + URL_B + " | ניקוי פירוליטי בתנור שארפ | "
         "ניקוי פירוליטי תנור שארפ; תוכנית ניקוי תנור שארפ |")

HEAD = ("# CONTENT LEDGER (fixture)\n\n"
        "## marom-serv.co.il\n"
        "| תאריך | URL | H1 | שאילתות יעד |\n"
        "|---|---|---|---|\n")


def check(name, got, want):
    if got == want:
        print(f"✅ {name}")
    else:
        FAILED.append(f"{name}: קיבלתי {got!r}, ציפיתי {want!r}")


def ledger(*rows):
    return HEAD + "\n".join(rows) + "\n"


def sandbox(ledger_text, patch_text="# LEDGER PATCH — תור ריק\n"):
    d = Path(tempfile.mkdtemp(prefix="ledger_tools_"))
    (d / "tools").mkdir()
    for f in ("ledger_patch.py", "ledger_lint.py"):
        shutil.copy(TOOLS / f, d / "tools" / f)
    (d / "content-ledger.md").write_text(ledger_text, encoding="utf-8")
    (d / "ledger-patch.md").write_text(patch_text, encoding="utf-8")
    return d


def run(d, script, *args):
    r = subprocess.run([sys.executable, str(d / "tools" / script), *args],
                       cwd=str(d), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def rows_of(d):
    """מיפוי URL לשורה, כדי לבדוק תא-תא ולא בהשוואת מחרוזת גסה."""
    out = {}
    for ln in (d / "content-ledger.md").read_text(encoding="utf-8").split("\n"):
        if not ln.startswith("|") or ln.startswith("|---") or "תאריך" in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        url = next((c for c in cells if "http" in c), None)
        if url:
            out[url] = cells
    return out


# ---------- patch: מחיל date ו-queries, ולא נוגע בשאר ----------
BASE = ledger("| — | " + URL_A + " | מצב שבת במקרר שארפ | אין נתונים |", ROW_B)
QUERIES_A = "מצב שבת מקרר שארפ; שבת מקרר שארפ; מקרר שארפ מצב שבת"
PATCH = ("- url=" + URL_A + "\n"
         "  date=2026-07-01\n"
         "  queries=" + QUERIES_A + "\n")

d = sandbox(BASE, PATCH)
code, out = run(d, "ledger_patch.py")
r = rows_of(d)
check("patch: exit 0", code, 0)
check("patch: date הוחל", r[URL_A][0], "2026-07-01")
check("patch: queries הוחלו", r[URL_A][-1], QUERIES_A)
check("patch: שורה אחרת לא נגעה", r[URL_B],
      [c.strip() for c in ROW_B.strip().strip("|").split("|")])
check("patch: התור התרוקן",
      "- url=" in (d / "ledger-patch.md").read_text(encoding="utf-8"), False)

# ---------- ריצה שנייה על תור ריק ----------
code2, out2 = run(d, "ledger_patch.py")
check("patch: ריצה שנייה על תור ריק exit 0", code2, 0)
check("patch: תור ריק לא שינה את הלדג'ר", rows_of(d)[URL_A][0], "2026-07-01")

# ---------- URL שלא קיים ----------
d = sandbox(BASE, "- url=https://marom-serv.co.il/עמוד-שלא-קיים/\n  date=2026-07-01\n")
before = (d / "content-ledger.md").read_text(encoding="utf-8")
code, out = run(d, "ledger_patch.py")
check("patch: URL שלא קיים exit 1", code, 1)
check("patch: הלדג'ר נשאר ללא שינוי",
      (d / "content-ledger.md").read_text(encoding="utf-8"), before)

# ---------- התאמה על URL עם percent-encoding ----------
ENC = "https://marom-serv.co.il/" + urllib.parse.quote("מקרר-שארפ-מצב-שבת") + "/"
d = sandbox(BASE, "- url=" + ENC + "\n  date=2026-07-02\n")
code, out = run(d, "ledger_patch.py")
check("patch: percent-encoding מתאים ל-URL עברי", code, 0)
check("patch: date הוחל דרך URL מקודד", rows_of(d)[URL_A][0], "2026-07-02")

# ---------- STALE_NOT_YET ----------
def not_yet_ledger(days):
    pub = date.today() - timedelta(days=days)
    return ledger("| " + pub.isoformat() + " | " + URL_A + " | מצב שבת במקרר שארפ | "
                  "טרם צבר (" + pub.strftime("%Y-%m") + ") · מצב שבת מקרר שארפ; "
                  "שבת מקרר שארפ |", ROW_B)


d = sandbox(not_yet_ledger(30))
code, out = run(d, "ledger_lint.py", "content-ledger.md")
check("STALE_NOT_YET: עמוד בן 30 יום לא נורה", "STALE_NOT_YET" in out, False)
check("STALE_NOT_YET: 30 יום exit 0", code, 0)

d = sandbox(not_yet_ledger(200))
code, out = run(d, "ledger_lint.py", "content-ledger.md")
check("STALE_NOT_YET: עמוד בן 200 יום נורה", "STALE_NOT_YET" in out, True)
check("STALE_NOT_YET: 200 יום exit 0 (אזהרה בלבד)", code, 0)

if FAILED:
    print("\n🔴 test_ledger_tools נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print("\n✅ test_ledger_tools עבר במלואו")
