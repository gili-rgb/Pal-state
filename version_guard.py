#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
version_guard.py — שלב E: ממשל גרסאות.

הבעיה שנצפתה ב-2026-08-03: שני סשנים ערכו את אותם קבצים במקביל, שניהם קראו לתוצאה
v7.22, ומי שהועלה אחרון דרס את השני בשקט. אין נעילה בין סשנים, ואף אחד מהם לא רואה
מה השני עושה.

הפתרון: הריפו הוא מקור האמת. קבצי הסקיל חיים ב-skills/content-machine/, ה-ZIP נוצר
מהריפו ולא להפך, וכל bump נבדק מכנית לפני שהוא מגיע לאוויר.

הבדיקות:
  VERSION_DUPLICATE   מספר גרסה שכבר קיים ב-CHANGELOG
  VERSION_REGRESSION  הגרסה בכותרת אינה גדולה מהאחרונה בהיסטוריה
  VERSION_UNLOGGED    גרסה בכותרת בלי רשומת CHANGELOG
  LINT_VERSION_AHEAD  הסקיל מפנה לגרסת pal-lint שאינה קיימת בריפו
  TOOL_MISSING        הסקיל מפנה לסקריפט שאינו קיים ב-tools/
  CROSS_FILE          סתירה בין SKILL לקבצים הנלווים (לקח דריפט ה-Product)

שימוש: python3 tools/version_guard.py [skills_dir]
exit 1 בכל כשל. רץ ב-CI על כל push.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ERRORS, NOTES = [], []


def err(rule, msg):
    ERRORS.append((rule, msg))


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v))


def check_versions(skill_dir):
    sk = skill_dir / "SKILL.md"
    ch = skill_dir / "CHANGELOG.md"
    if not sk.exists():
        err("TOOL_MISSING", f"{sk} חסר")
        return None
    s = sk.read_text(encoding="utf-8")
    m = re.search(r"^#\s+.*?v(\d+\.\d+(?:\.\d+)?)", s, re.M)
    if not m:
        err("VERSION_UNLOGGED", "לא נמצא מספר גרסה בכותרת SKILL.md")
        return None
    cur = m.group(1)
    NOTES.append(f"גרסת SKILL: v{cur}")

    hist = re.findall(r">\s*\*\*v(\d+\.\d+(?:\.\d+)?)\s*\(", s)
    hist += re.findall(r">\s*\*\*v(\d+\.\d+(?:\.\d+)?)\s*\(",
                       ch.read_text(encoding="utf-8") if ch.exists() else "")
    if cur not in hist:
        err("VERSION_UNLOGGED", f"v{cur} בכותרת בלי רשומת changelog")
    dupes = {v for v in hist if hist.count(v) > 2}
    if dupes:
        err("VERSION_DUPLICATE",
            f"מספר גרסה מופיע ביותר משני מקומות (SKILL+CHANGELOG): {sorted(dupes)}")
    others = [v for v in hist if v != cur]
    if others and vtuple(cur) <= max(vtuple(v) for v in others):
        err("VERSION_REGRESSION",
            f"v{cur} אינה גדולה מהגרסה הגבוהה בהיסטוריה "
            f"(v{max(others, key=vtuple)}). שני סשנים במקביל?")
    return s


def check_lint_reference(s):
    real = re.search(r'VERSION\s*=\s*"([\d.]+)"',
                     (ROOT / "tools" / "pal_lint.py").read_text(encoding="utf-8"))
    if not real:
        err("TOOL_MISSING", "אין VERSION ב-pal_lint.py")
        return
    real = real.group(1)
    NOTES.append(f"pal-lint בריפו: v{real}")
    for ref in set(re.findall(r"pal-lint v(\d+\.\d+\.\d+)", s)):
        if vtuple(ref) > vtuple(real):
            err("LINT_VERSION_AHEAD",
                f"הסקיל מפנה ל-pal-lint v{ref} אבל בריפו יש v{real}. "
                f"דחוף את הלינט לפני העלאת הסקיל")


def check_tools(s):
    for name in set(re.findall(r"tools/(\w+\.py)", s)):
        if not (ROOT / "tools" / name).exists():
            err("TOOL_MISSING", f"הסקיל מפנה ל-tools/{name} שאינו קיים בריפו")
        else:
            NOTES.append(f"tools/{name} קיים")


def check_cross_file(skill_dir, s):
    """הלקח מדריפט ה-Product: אודיט שבודק קובץ אחד מחמיץ סתירות."""
    tpl = skill_dir / "html-template.md"
    if tpl.exists():
        t = tpl.read_text(encoding="utf-8")
        if '"@type": "Product"' in t or "7 entities" in t:
            err("CROSS_FILE",
                "html-template מכיל ישות Product או '7 entities' — סותר את SKILL (6 תמיד)")
        if "6 entities" not in t:
            err("CROSS_FILE", "html-template אינו מצהיר על 6 entities")
    for site in ("csb", "marom", "plrom"):
        f = skill_dir / f"project-{site}.md"
        if not f.exists():
            err("TOOL_MISSING", f"project-{site}.md חסר")
            continue
        p = f.read_text(encoding="utf-8")
        if '"@type": "Organization"' not in p:
            err("CROSS_FILE",
                f"project-{site}.md בלי בלוק Organization קנוני — "
                f"ORG_SCHEMA_DRIFT יאכוף כלל בלי מקור")
        if '"sameAs"' not in p:
            err("CROSS_FILE", f"project-{site}.md: Organization בלי sameAs")
        if "משפטים קנוניים" not in p:
            err("CROSS_FILE", f"project-{site}.md בלי משפטים קנוניים — NARRATIVE_MISSING יידלג")
    # אזכור בשורה שמכילה גם את הצורה הנכונה הוא תיעוד תיקון, לא שימוש.
    banned = {"באוכנט": "באוקנכט"}
    for f in skill_dir.glob("*.md"):
        if f.name == "CHANGELOG.md":
            continue
        for i, ln in enumerate(f.read_text(encoding="utf-8").split("\n"), 1):
            for bad, right in banned.items():
                if bad in ln and right not in ln:
                    err("CROSS_FILE",
                        f"{f.name}:{i} שימוש במונח אסור '{bad}' (הנכון: {right})")


def check_state_freshness(cur_skill, lint_ver):
    """
    v1.1: STATE.md חייב לשקף את המציאות.
    לקח 2026-08-10: STATE.md נשאר על v8.3 בזמן שהמערכת הייתה ב-v8.13 —
    ארבעה ימי פיגור. סשן חדש שקורא אותו מקבל תמונה שגויה, וזה בדיוק
    מה שהקובץ נועד למנוע.
    """
    f = ROOT / "STATE.md"
    if not f.exists():
        err("STATE_MISSING", "STATE.md חסר")
        return
    t = f.read_text(encoding="utf-8")
    ok = True
    if f"v{cur_skill}" not in t:
        err("STATE_STALE",
            f"STATE.md אינו מזכיר את v{cur_skill}. עדכן אותו באותו commit")
        ok = False
    if lint_ver not in t:
        err("STATE_STALE", f"STATE.md אינו מזכיר את pal-lint {lint_ver}")
        ok = False
    if ok:
        NOTES.append(f"STATE.md משקף v{cur_skill} ו-pal-lint {lint_ver}")


def main():
    skill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "skills" / "content-machine"
    if not skill_dir.exists():
        print(f"ℹ️  {skill_dir} אינו קיים — דילוג (הסקיל טרם נדחף לריפו)")
        return 0
    s = check_versions(skill_dir)
    if s:
        m = re.search(r"^#\s+.*?v(\d+\.\d+(?:\.\d+)?)", s, re.M)
        lm = re.search(r'VERSION\s*=\s*"([\d.]+)"',
                       (ROOT / "tools" / "pal_lint.py").read_text(encoding="utf-8"))
        if m and lm:
            check_state_freshness(m.group(1), lm.group(1))
        check_lint_reference(s)
        check_tools(s)
        check_cross_file(skill_dir, s)
    for n in NOTES:
        print(f"ℹ️  {n}")
    for r, m in ERRORS:
        print(f"❌ [{r}] {m}")
    if ERRORS:
        print(f"\n🔴 version-guard נכשל: {len(ERRORS)} שגיאות")
        return 1
    print("\n✅ version-guard עבר")
    return 0


if __name__ == "__main__":
    sys.exit(main())
