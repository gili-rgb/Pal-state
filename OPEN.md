# OPEN — משימות פתוחות
עודכן: 2026-07-05

## audit content-machine (2026-07-05)
- [ ] התקנת content-machine v7.12 ו-brand-hub-machine v1.15 (ZIP נמסרו לגיל)
- [x] דחיפת pal-lint v1.0.0 (tools/) — בוצע 2026-07-05
- [ ] דחיפת pal-lint v1.1.0 — אימות מול הסקיל חשף ש-v1.0.0 לא כיסה 9 חוסמי Elementor (unicode-bidi, svg, ga-event, target=_blank, U+2011/AD/200B, איזון סוגריים, @media מקונן, href ריק, תגיות). v1.1.0 מוכן + selftest ירוק. רק אחרי הדחיפה מוחקים את בלוק ה-Elementor המוטמע מ-content-machine (יהיה v7.13)
- [ ] pal-lint v1.2: קליטת yoast_check / link_audit / schema_deep+WCAG+אסורים-per-site כמודולים (כרגע מוטמעים בשלב 13 של content-machine v7.12)
- [ ] בירור v7.10-v7.11: האם קיימות כ-ZIP מחוץ למותקן; אם כן — יישום השינויים שלהן מעל v7.12
- [ ] פילוח חודשי ב-gsc pull (עונתיות) — הרחבת הסקריפט, ואז הסיגנל בשלב 2 נכנס לתוקף
- [ ] מילוי content-ledger.md רטרו: המאמרים שכבר פורסמו (מ-recent_chats + היסטוריה)

## brand-hub-machine
- [ ] תיקון Product schema רטרו ל-3 עמודי מותג ב-Marom: Haier, Blomberg, DeLonghi
      (Sharp כבר תוקן ל-v1.12). נדרש: offers block עם דאטה חי מ-MCP (price, priceCurrency ILS, availability InStock, url verbatim permalink)

## Maya
- [ ] A/B test על וריאנטים של opening script
- [ ] שיפורי hebrew_pronunciation.py
- [ ] Israeli-accent voice cloning דרך HeyGen

## תשתית / ממשק
- [ ] הוספת changelog קצר בראש כל SKILL file (שורה per-version)
- [ ] שקילת VALIDATE כ-script עצמאי שרץ לפני כל submit (לא רק כצעד ב-SKILL)
- [ ] טריגר בזיכרון המובנה: "בתחילת כל משימה לא-טריוויאלית קרא pal-state"

## GBP אוטומציה
- [ ] ממתין לאישור מכסת Google API (ארכיטקטורה Python/FastAPI מתוכננת)
