#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_version_guard.py — כיסוי בדיקות ל-version_guard.py.

למה זה קיים: הכלי נבנה ב-2026-08-10 כדי למנוע שתי גרסאות מקבילות עם אותו
מספר, ואז התיר במפורש עד שני מקומות לכל מספר גרסה. התוצאה: 21 רשומות
היסטוריה חיו במקביל ב-SKILL.md וב-CHANGELOG.md, וארבע מהן התפצלו לשני
טקסטים שונים תחת אותו מספר (v7.18 44.8% דמיון, v7.19 37.1%, v7.20 19.1%,
v8.10 40.5%). גרסת v8.10 ב-CHANGELOG אף נשאה מספר שגוי, 17KB במקום 42KB
שנמדדו בהרצה בפועל. השער עבר בירוק על כל זה במשך שלושה חודשים.

הכלי עצמו מעולם לא נבדק. כלל אכיפה בלי בדיקה הוא הבטחה, לא שער.

כל בדיקה רצה ב-sandbox נפרד ב-tempfile ומריצה subprocess בדיוק כמו ב-CI.
הריפו האמיתי לא נוגע.

רץ ב-CI כשער שביעי, אחרי test_ledger_tools ולפני version_guard עצמו.
exit 1 בכשל.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent.parent
FAILED = []

CUR = "8.14"
ENTRY_CUR = ("> **v8.14 (לקחי הריצה המוצלחת הראשונה, 2026-08-10):** "
             "מאמר Refresh למרום עבר את השרשרת המלאה.")
ENTRY_OLD = ("> **v8.13 (חיפוש אינו תנאי להגשה, 2026-08-10):** "
             "`competitor_headings` עבר ל-OPTIONAL_MCP.")

STATE = ("# PAL STATE\nעודכן: 2026-08-13 (v8.14, pal-lint v1.11.1)\n\n"
         "| content-machine | **v8.14** | מותקן |\n")


def check(name, got, want):
    if got == want:
        print(f"✅ {name}")
    else:
        FAILED.append(f"{name}: קיבלתי {got!r}, ציפיתי {want!r}")


def sandbox(skill_entries, changelog_entries, extra=""):
    """ריפו מינימלי: SKILL.md, CHANGELOG.md, STATE.md ושלושת הכלים שהשער דורש."""
    d = Path(tempfile.mkdtemp(prefix="version_guard_"))
    (d / "tools").mkdir()
    shutil.copy(TOOLS / "version_guard.py", d / "tools" / "version_guard.py")
    for stub in ("pal_lint.py", "preflight.py", "postflight.py"):
        (d / "tools" / stub).write_text('VERSION = "1.11.1"\n', encoding="utf-8")

    sk = d / "skills" / "content-machine"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        f"# מכונת תוכן v{CUR} — כותרת\n\n" + "\n\n".join(skill_entries) + "\n\n"
        "> היסטוריה מלאה: `CHANGELOG.md`.\n\n"
        "## גוף\nהסקיל משתמש ב-tools/pal_lint.py, tools/preflight.py "
        "ו-tools/postflight.py. pal-lint v1.11.1.\n",
        encoding="utf-8")
    (sk / "CHANGELOG.md").write_text(
        "# content-machine — CHANGELOG\n\n" + "\n\n".join(changelog_entries) + "\n",
        encoding="utf-8")
    (sk / "html-template.md").write_text(
        "# תבנית\n@graph של 6 entities תמיד.\n", encoding="utf-8")
    for site in ("csb", "marom", "plrom"):
        (sk / f"project-{site}.md").write_text(
            f"# {site}\n\n## משפטים קנוניים\nמשפט.\n" + (extra if site == "marom" else "") +
            '\n```json\n{"@type": "Organization", "sameAs": ["https://example.com"]}\n```\n',
            encoding="utf-8")
    (d / "STATE.md").write_text(STATE, encoding="utf-8")
    return d


def run(d):
    r = subprocess.run([sys.executable, str(d / "tools" / "version_guard.py")],
                       cwd=str(d), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


# ---------- המצב התקין: SKILL מחזיק את הגרסה הנוכחית בלבד ----------
d = sandbox([ENTRY_CUR], [ENTRY_CUR, ENTRY_OLD])
code, out = run(d)
check("תקין: SKILL עם הגרסה הנוכחית בלבד עובר", code, 0)
check("תקין: אין CHANGELOG_DUPLICATE", "CHANGELOG_DUPLICATE" in out, False)

# ---------- החור שהיה פתוח: רשומה ישנה בשני הקבצים ----------
d = sandbox([ENTRY_CUR, ENTRY_OLD], [ENTRY_CUR, ENTRY_OLD])
code, out = run(d)
check("רגרסיה: v8.13 בשני הקבצים נחסמת", "CHANGELOG_DUPLICATE" in out, True)
check("רגרסיה: exit 1", code, 1)
check("רגרסיה: ההודעה נוקבת בגרסה", "8.13" in out, True)

# ---------- 20 רשומות משוכפלות, המצב שהיה בריפו בפועל ----------
many = [ENTRY_CUR] + [f"> **v8.{n} (רשומה, 2026-08-03):** טקסט." for n in range(1, 14)]
d = sandbox(many, many)
code, out = run(d)
check("רגרסיה: 13 רשומות משוכפלות נחסמות", "CHANGELOG_DUPLICATE" in out, True)
check("רגרסיה: exit 1 גם בהיקף מלא", code, 1)

# ---------- הדריפט עצמו: אותו מספר, שני טקסטים ----------
drift = ENTRY_CUR.replace("השרשרת המלאה.", "טקסט אחר לגמרי, וזה בדיוק הדריפט.")
d = sandbox([ENTRY_CUR], [drift, ENTRY_OLD])
code, out = run(d)
check("דריפט: אותה גרסה עם טקסט שונה נחסמת", "CHANGELOG_DRIFT" in out, True)
check("דריפט: exit 1", code, 1)

# ---------- הגרסה הנוכחית בשניהם עם טקסט זהה מותרת ----------
d = sandbox([ENTRY_CUR], [ENTRY_CUR, ENTRY_OLD])
code, out = run(d)
check("הגרסה הנוכחית בשניהם עם טקסט זהה מותרת", "CHANGELOG_DRIFT" in out, False)

# ---------- כפילות בתוך אותו קובץ ----------
d = sandbox([ENTRY_CUR, ENTRY_CUR], [ENTRY_CUR])
code, out = run(d)
check("כפילות בתוך SKILL.md נחסמת", "VERSION_DUPLICATE" in out, True)
check("כפילות בתוך קובץ: exit 1", code, 1)

# ---------- לא נשבר: רגרסיית גרסה עדיין נתפסת ----------
ahead = "> **v9.9 (גרסה עתידית, 2026-09-01):** טקסט."
d = sandbox([ENTRY_CUR], [ENTRY_CUR, ahead])
code, out = run(d)
check("לא נשבר: VERSION_REGRESSION עדיין יורה", "VERSION_REGRESSION" in out, True)

# ---------- לא נשבר: גרסה בכותרת בלי רשומה ----------
d = sandbox([], [ENTRY_OLD])
code, out = run(d)
check("לא נשבר: VERSION_UNLOGGED עדיין יורה", "VERSION_UNLOGGED" in out, True)

# ---------- placeholder פתוח בקובץ מקור אמת ----------
d = sandbox([ENTRY_CUR], [ENTRY_CUR, ENTRY_OLD],
            extra="- **sameAs:** [גיל: אם יש לינקדאין, הוסף URL]\n")
code, out = run(d)
check("placeholder: [גיל: נחסם", "OPEN_PLACEHOLDER" in out, True)
check("placeholder: exit 1", code, 1)
check("placeholder: ההודעה נוקבת בקובץ", "project-marom.md" in out, True)

d = sandbox([ENTRY_CUR], [ENTRY_CUR, ENTRY_OLD],
            extra="- **sameAs:** אין, וזו החלטה ולא פער.\n")
code, out = run(d)
check("placeholder: החלטה מפורשת עוברת", "OPEN_PLACEHOLDER" in out, False)
check("placeholder: exit 0", code, 0)

# אזכור בתוך backticks הוא תיעוד הכלל, לא שימוש. הכלל תפס את רשומת
# ה-changelog של עצמו בריצה הראשונה, ולכן זו בדיקת רגרסיה ולא הידור.
d = sandbox([ENTRY_CUR], [ENTRY_CUR, ENTRY_OLD],
            extra="הכלל נופל על `[גיל:` בכל קובץ סקיל.\n")
code, out = run(d)
check("placeholder: אזכור ב-backticks הוא תיעוד ולא נחסם", "OPEN_PLACEHOLDER" in out, False)
check("placeholder: תיעוד exit 0", code, 0)

if FAILED:
    print("\n🔴 test_version_guard נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print("\n✅ test_version_guard עבר במלואו")
