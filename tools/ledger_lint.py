#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_lint.py — שומר סף ל-content-ledger.md.

למה זה קיים: עמודת "שאילתות יעד" נשארה ריקה ב-123 שורות, ולכן שער ה-dedup עבד
ברמת כותרת ולא ברמת שאילתה. אותו אשכול התגלה ונפסל מחדש בחמישה סשנים שונים.
המילוי הרטרואקטיבי בוצע ב-2026-08-03 מ-GSC (dimensions=[page, query]).
הסקריפט הזה מונע את היפתחות החור מחדש בשורות הבאות.

exit 0 = תקין. exit 1 = יש שורה פסולה.
שימוש: python3 tools/ledger_lint.py [path]   (ברירת מחדל: content-ledger.md)

כללים:
  ERROR MISSING_QUERIES  — שורה עם URL ובלי שאילתות יעד
  ERROR BAD_SEPARATOR    — שאילתות מופרדות בפסיק במקום בנקודה-פסיק
  ERROR DUP_URL          — אותו URL מופיע פעמיים בלדג'ר
  WARN  SINGLE_QUERY     — שאילתה אחת בלבד; שער ה-dedup חלש בשורה כזו
  WARN  NO_GSC_DATA      — סומן ידנית כ"אין נתונים", מותר אבל נספר
"""
import re
import sys
from collections import Counter
from pathlib import Path

EMPTY = {"—", "-", "", "–", "TBD", "tbd"}
NO_DATA = {"אין נתונים", "טרם נמדד"}


def parse(path: Path):
    site, rows = None, []
    for i, ln in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if ln.startswith("## "):
            site = ln[3:].strip()
        if not ln.startswith("|"):
            continue
        if ln.startswith("|---") or "תאריך" in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        url = next((c for c in cells if "http" in c), None)
        if not url:
            continue
        rows.append({"line": i, "site": site, "url": url, "queries": cells[-1], "cells": cells})
    return rows


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "content-ledger.md")
    if not path.exists():
        print(f"❌ לא נמצא {path}")
        return 1
    rows = parse(path)
    errors, warns, nodata = [], [], 0

    seen = Counter(r["url"].rstrip("/") for r in rows)
    for r in rows:
        q = r["queries"]
        if q in EMPTY:
            errors.append((r["line"], "MISSING_QUERIES",
                           f'שורה בלי שאילתות יעד: {r["url"][:80]}'))
            continue
        if q in NO_DATA:
            nodata += 1
            warns.append((r["line"], "NO_GSC_DATA", f'סומן ללא נתוני GSC: {r["url"][:70]}'))
            continue
        if "," in q and ";" not in q:
            errors.append((r["line"], "BAD_SEPARATOR",
                           f'שאילתות מופרדות בפסיק, נדרש ";": {q[:60]}'))
        elif len([x for x in q.split(";") if x.strip()]) == 1:
            warns.append((r["line"], "SINGLE_QUERY", f'שאילתה בודדת: {q[:60]}'))

    for url, n in seen.items():
        if n > 1:
            errors.append((0, "DUP_URL", f"URL כפול בלדג'ר ({n} פעמים): {url[:80]}"))

    print(f"ℹ️  ledger-lint | {path.name} | {len(rows)} שורות | ללא נתוני GSC: {nodata}")
    for line, rule, msg in warns:
        print(f"⚠️  [{rule}] שורה {line}: {msg}")
    for line, rule, msg in errors:
        print(f"❌ [{rule}] שורה {line}: {msg}")
    if errors:
        print(f"\n🔴 ledger-lint נכשל: {len(errors)} שגיאות. "
              f"מלא את השאילתות מ-cats/ledger_target_queries.md בריפו pal-gsc-data.")
        return 1
    print(f"\n✅ ledger-lint עבר ({len(warns)} אזהרות)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
