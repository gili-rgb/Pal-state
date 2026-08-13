# CHANGELOG — tools/

יומן שינויים לסקריפטים ב-`tools/` בלבד: preflight, postflight, pal_lint,
ledger_lint, ledger_patch, ledger_merge, version_guard והבדיקות שלהם.

**החלטה (2026-08-13):** תיעוד שינויים בכלים חי מהיום כאן, ולא בתוך
`skills/content-machine/SKILL.md`. הסיבה מכנית: SKILL.md הוא 71KB ו-CHANGELOG.md
הוא 30KB, וכל דחיפה שלהם דרך MCP מחייבת שליחת הקובץ המלא. שינוי של שלוש שורות
בכלי גרר עלות של קובץ שלם. זו תחילת פיצול ניהול הגרסאות לקבצים קטנים ייעודיים:
שינוי בכלי נוגע רק בקובץ הזה, וגרסת content-machine אינה זזה בגללו.

---

> **2026-08-13**

**postflight.py v1.4 → v1.5 — כלל חדש `DOMINANT_H1_DUPLICATE` (ERROR, חוסם)**
רץ מיד אחרי `check_dominant_links`. לוקח מ-`brief["dominant_pages"]` רק נכסים
שלנו (לא partner) במיקום 3.0 ומטה, ומצליב את מילות התוכן של השאילתה מול ה-H1.
כיסוי מלא של כל מילות השאילתה ב-H1 = חסימה. חריג יחיד: Refresh של אותו עמוד
דומיננטי עצמו.
הרקע: שני מאמרי שארפ במרום נכתבו על "חלקי חילוף למקרר שארפ", אשכול שעמודי
ה-product-category שלנו מחזיקים במיקום 1.0-1.5 עם 19,687 חשיפות. שני המאמרים
על אפס חשיפות. `dominant_pages` כבר היה ב-brief באותו רגע, אבל רק המליץ לקשר
(WARN), ולכן אף שער לא עצר את הכתיבה. המלצה אינה שער.

**ledger_lint.py — כלל חדש `STALE_NOT_YET` (WARN בלבד)**
תא שאילתות שמסומן `טרם צבר (YYYY-MM)` נבדק מול תאריך הפרסום בעמודה הראשונה,
ובנפילה חזרה מול החודש שבסוגריים. מעל 90 יום נרשמת אזהרה עם מספר הימים וה-URL.
הרקע: 8 שורות סומנו "טרם צבר" בסבב הסיווג של 2026-08-13, בלי שום מנגנון
שמזכיר לבדוק אותן שוב. "טרם צבר" הוא מצב זמני, ואחרי רבעון בלי חשיפות זה ממצא.
WARN ולא ERROR, כדי שלא לחסום את ה-CI על חלוף זמן בלבד.

**tools/tests/test_ledger_tools.py — קובץ בדיקות חדש, שער CI שישי**
sandbox ב-tempfile שמעתיק את `ledger_patch.py` ו-`ledger_lint.py` ומריץ אותם
ב-subprocess על לדג'ר מינימלי. מכסה: החלת date ו-queries, שורה שכנה שלא נגעה,
ריקון התור, ריצה חוזרת על תור ריק, URL שלא נמצא (exit 1 והלדג'ר לא נגע),
התאמה על URL עם percent-encoding, ו-STALE_NOT_YET על 30 יום מול 200 יום.
הרקע: `ledger_patch` כותב ישירות למקור האמת של שער ה-dedup, ועד היום נבדק רק
בהרצה אמיתית על הקובץ האמיתי. באג בהתאמת URL היה משכתב שורה שגויה בשקט.

**.github/workflows/pal-state-lint.yml — שער שישי**
`Ledger tools tests` נוסף לפני `Version guard`. סדר השערים:
ledger_lint → selftest → test_flight → test_postflight → test_ledger_tools →
version_guard.
