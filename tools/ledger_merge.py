#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_merge.py — סוגר את החוליה הידנית האחרונה.

עד 2026-08-09 שורת content-ledger אחרי פרסום הועתקה ידנית. פעולה ידנית
חוזרת היא פגם בעיצוב, לא תהליך: השורה נשכחה חמש פעמים, ובכל פעם שער
ה-dedup נחלש והמערכת גילתה מחדש נושא שכבר כוסה.

הזרימה המלאה, בלי נגיעה:
  postflight  → כותב שורה ל-ledger-pending.md
  ledger_merge → ממזג ל-content-ledger.md בסעיף האתר הנכון
  gsc_page_queries (כל שני) → מזהה את ה-URL האמיתי
  ledger_merge → מחליף [PENDING:slug] ב-URL, ומוחק מהתור

הפעולה היחידה שנשארת אנושית היא ההעלאה לאלמנטור עצמה.

שימוש: python3 tools/ledger_merge.py [--gsc /path/to/pal-gsc]
exit 0 תמיד כשאין שגיאה אמיתית — אין תור זה מצב תקין.
"""
import argparse
import json
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PENDING = ROOT / "ledger-pending.md"
LEDGER = ROOT / "content-ledger.md"
SITES = {"csb": "csb.co.il", "marom": "marom-serv.co.il", "plrom": "plrom.co.il"}


def norm(u):
    u = urllib.parse.unquote(u.strip())
    return re.sub(r"^https?://", "", u).rstrip("/")


def parse_pending():
    if not PENDING.exists():
        return []
    out, meta = [], None
    for ln in PENDING.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"- site=(\w+) mode=(\w+) slug=(.+)", ln.strip())
        if m:
            meta = {"site": m.group(1), "mode": m.group(2), "slug": m.group(3)}
        elif ln.strip().startswith("|") and meta:
            meta["row"] = ln.strip()
            out.append(meta)
            meta = None
    return out


def live_urls(gsc_dir, site):
    """כל ה-URL שגוגל כבר מכירה לאתר. מקור ההשלמה של [PENDING:slug]."""
    f = Path(gsc_dir) / "cats" / f"{site}_page_queries.json"
    if not f.exists():
        return []
    return [norm(u) for u in json.load(open(f, encoding="utf-8"))]


def ledger_urls():
    """URL שכבר בלדג'ר. עמוד חדש לא יכול להיות אחד מהם."""
    return {norm(c.strip()) for ln in LEDGER.read_text(encoding="utf-8").split("\n")
            if ln.startswith("|") for c in ln.split("|") if "http" in c}


def resolve_pending(row, slug, urls, known):
    """
    התאמת slug ל-URL אמיתי. ה-slug בפרסום עשוי להיות מקוצר מהניחוש,
    ולכן ההשוואה היא לפי חפיפת מילים ולא לפי זהות מדויקת.
    """
    if "[PENDING:" not in row:
        return row, True
    words = [w for w in slug.split("-") if len(w) > 2]
    if len(words) < 3:
        return row, False
    # סף מחמיר: 70% מהמילים. הסף הרופף (2 מילים) התאים מאמר חדש
    # לעמוד קיים רק בזכות "מדיח" ו"בוש" (נצפה 2026-08-09).
    need = max(3, int(len(words) * 0.7))
    best, score = None, 0
    for u in urls:
        if u in known:          # URL שכבר בלדג'ר אינו העמוד החדש שלנו
            continue
        tail = u.split("/")[-1]
        hits = sum(1 for w in words if w in tail)
        if hits > score and hits >= need:
            best, score = u, hits
    if not best:
        return row, False
    return re.sub(r"\[PENDING:[^\]]+\]", "https://" + best, row), True


def merge(rows_by_site):
    """הוספה לסעיף האתר הנכון, מיד אחרי שורת המפריד."""
    lines = LEDGER.read_text(encoding="utf-8").split("\n")
    added = 0
    for site, rows in rows_by_site.items():
        domain = SITES[site]
        idx = None
        for i, ln in enumerate(lines):
            if ln.startswith("## ") and domain in ln:
                for j in range(i, min(i + 6, len(lines))):
                    if lines[j].startswith("|---"):
                        idx = j + 1
                        break
                break
        if idx is None:
            print(f"⚠️  לא נמצא סעיף {domain} בלדג'ר", file=sys.stderr)
            continue
        for r in reversed(rows):
            url = next((c.strip() for c in r.split("|") if "http" in c), "")
            if url and any(norm(url) in norm(l) for l in lines if l.startswith("|")):
                continue
            lines.insert(idx, r)
            added += 1
    LEDGER.write_text("\n".join(lines), encoding="utf-8")
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gsc", default="/home/claude/pal-gsc")
    a = ap.parse_args()

    items = parse_pending()
    if not items:
        print("אין שורות בתור")
        return 0
    print(f"בתור: {len(items)} שורות")

    ready, waiting = {}, []
    cache = {}
    known = ledger_urls()
    for it in items:
        site = it["site"]
        if site not in cache:
            cache[site] = live_urls(a.gsc, site)
        row, ok = resolve_pending(it["row"], it["slug"], cache[site], known)
        if ok:
            ready.setdefault(site, []).append(row)
            print(f"   ✅ {site}: {it['slug'][:45]}")
        else:
            waiting.append(it)
            print(f"   ⏳ {site}: {it['slug'][:45]} — טרם נמצא ב-GSC")

    added = merge(ready) if ready else 0
    print(f"\nנוספו ללדג'ר: {added}")

    if waiting:
        head = PENDING.read_text(encoding="utf-8").split("- site=")[0].rstrip()
        body = "".join(f"- site={w['site']} mode={w['mode']} slug={w['slug']}\n"
                       f"  {w['row']}\n" for w in waiting)
        PENDING.write_text(head + "\n" + body, encoding="utf-8")
        print(f"נשארו בתור: {len(waiting)} (ימתינו למשיכת GSC הבאה)")
    else:
        PENDING.unlink(missing_ok=True)
        print("התור התרוקן")
    return 0


if __name__ == "__main__":
    sys.exit(main())
