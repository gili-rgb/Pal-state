# OPEN — משימות פתוחות
עודכן: 2026-07-03

## brand-hub-machine
- [ ] תיקון Product schema רטרו ל-3 עמודי מותג ב-Marom: Haier, Blomberg, DeLonghi
      (Sharp כבר תוקן ל-v1.12). נדרש: offers block עם דאטה חי מ-MCP (price, priceCurrency ILS, availability InStock, url verbatim permalink)

## Maya
- [ ] A/B test על וריאנטים של opening script
- [ ] שיפורי hebrew_pronunciation.py
- [ ] Israeli-accent voice cloning דרך HeyGen

## תשתית / ממשק
- [ ] הוספת changelog קצר בראש כל SKILL file (שורה per-version)
- [x] VALIDATE כ-script עצמאי — נסגר: tools/pal_lint.py (2026-07-03)
- [ ] הוספת שורת pal-lint כצעד חובה ב-SKILL files בסבב העדכון הבא של כל סקיל
- [ ] חיבור GitHub connector/PAT ל-Claude כדי לאפשר push אוטונומי ל-pal-state (מבטל את ה-workaround של ZIP ידני לצמיתות)
- [ ] טריגר בזיכרון המובנה: "בתחילת כל משימה לא-טריוויאלית קרא pal-state"

## GBP אוטומציה
- [ ] ממתין לאישור מכסת Google API (ארכיטקטורה Python/FastAPI מתוכננת)
