#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_patch.py — עדכון שורות קיימות ב-content-ledger.md מקובץ patch קטן.

למה זה קיים: ledger_merge מוסיף שורות חדשות בלבד. עדכון שורה קיימת (תאריך
פרסום, שאילתות יעד, סיווג) חייב עד היום דחיפה של הקובץ המלא, 30KB בשביל
שינוי של 12 שורות. פעולה יקרה שחוזרת היא פגם בעיצוב.

הזרימה: כותבים ledger-patch.md → הוא נדחף → workflow מריץ את הקובץ הזה →
content-ledger.md מתעדכן, ledger-patch.md מתרוקן, ledger_lint שומר על השער.

פורמט ledger-patch.md (התאמה לפי URL, בלי תלות במספר שורה):
  - url=https://site/slug/
    date=2026-07-01
    queries=שאילתה1; שאילתה2

date ו-queries שניהם אופציונליים. שדה חסר = השדה בלדג'ר לא נוגע.
exit 0 גם כשהתור ריק. exit 1 רק על URL שלא נמצא או נמצא פעמיים.
"""
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCH = ROOT / "ledger-patch.md"
LEDGER = ROOT / "content-ledger.md"


def norm(u: str) -> str:
    return re.sub(r"^https?://", "", urllib.parse.unquote(u.strip())).rstrip("/")


def parse_patch(text: str):
    entries, cur = [], None
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("- url="):
            if cur:
                entries.append(cur)
            cur = {"url": s[6:].strip()}
        elif cur and s.startswith("date="):
            cur["date"] = s[5:].strip()
        elif cur and s.startswith("queries="):
            cur["queries"] = s[8:].strip()
    if cur:
        entries.append(cur)
    return entries


def main() -> int:
    if not LEDGER.exists():
        print(f"❌ לא נמצא {LEDGER.name}")
        return 1
    if not PATCH.exists() or not PATCH.read_text(encoding="utf-8").strip():
        print("ℹ️  ledger-patch ריק — אין מה להחיל")
        return 0

    entries = parse_patch(PATCH.read_text(encoding="utf-8"))
    lines = LEDGER.read_text(encoding="utf-8").split("\n")

    index = {}
    for i, ln in enumerate(lines):
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        url = next((c for c in cells if "http" in c), None)
        if url:
            index.setdefault(norm(url), []).append(i)

    applied, errors = 0, []
    for e in entries:
        key = norm(e["url"])
        hits = index.get(key, [])
        if len(hits) != 1:
            errors.append(f'{"לא נמצא" if not hits else f"נמצא {len(hits)} פעמים"}: {key[:70]}')
            continue
        i = hits[0]
        cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if "date" in e:
            cells[0] = e["date"]
        if "queries" in e:
            cells[-1] = e["queries"]
        lines[i] = "| " + " | ".join(cells) + " |"
        applied += 1
        print(f"✔ {key[:70]}")

    if errors:
        for m in errors:
            print(f"❌ {m}")
        print(f"\n🔴 ledger-patch נכשל: {len(errors)} רשומות. הלדג'ר לא נגע.")
        return 1

    LEDGER.write_text("\n".join(lines), encoding="utf-8")
    PATCH.write_text("# LEDGER PATCH — תור ריק\n", encoding="utf-8")
    print(f"\n✅ ledger-patch: {applied} שורות עודכנו, התור רוקן")
    return 0


if __name__ == "__main__":
    sys.exit(main())
