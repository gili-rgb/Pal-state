# OPEN — משימות פתוחות
עודכן: 2026-07-05

## audit content-machine (2026-07-05)
- [ ] התקנת content-machine v7.15, brand-hub-machine v1.16, product-page-machine v7.1 (ZIPs נמסרו 2026-07-05; מחליפים את v7.13/v1.15)
- [x] דחיפת pal-lint v1.0.0 (tools/) — בוצע 2026-07-05
- [x] דחיפת pal-lint v1.1.0 (כיסוי מלא של חוסמי Elementor) — בוצע 2026-07-05
- [x] content-machine v7.13 נוצר — בלוק ה-Elementor המוטמע נמחק, שלב 13 מריץ pal-lint בלבד. ZIP אצל גיל, ממתין להתקנה
- [x] pal-lint v1.2.0: קליטת yoast_check / link_audit / schema_deep+WCAG + responsive/CTA/WAF-blog — בוצע 2026-07-05, selftest ירוק (12 fixtures)
- [ ] בירור v7.10-v7.11: האם קיימות כ-ZIP מחוץ למותקן; אם כן — יישום השינויים שלהן מעל v7.13
- [ ] פילוח חודשי ב-gsc pull (עונתיות) — הרחבת הסקריפט, ואז הסיגנל בשלב 2 נכנס לתוקף
- [ ] מילוי content-ledger.md רטרו: המאמרים שכבר פורסמו (מ-recent_chats + היסטוריה)

## brand-hub-machine
- [ ] רטרו ל-3 עמודי מותג ב-Marom (Haier, Blomberg, DeLonghi) בסבב אחד: offers block מ-MCP + המרת CSS ל-hex + לקחי v1.16 (Sharp כבר תוקן)

## Maya
- [ ] A/B test על וריאנטים של opening script
- [ ] שיפורי hebrew_pronunciation.py
- [ ] Israeli-accent voice cloning דרך HeyGen

## תשתית / ממשק
- [x] changelog בראש כל SKILL — בוצע (כל שלושת הסקילים, 2026-07-05)
- [ ] מחיקת סקיל global-notes מההתקנה של גיל (זומבי; pal-state + הזיכרון המובנה החליפו)
- [ ] הכרעה: האם לאסור "חיקוי" גם ב-brand-hub (כרגע ERROR רק ב-product; תבנית brand-hub משתמשת "מקורי מול חיקוי")
- [ ] שקילת VALIDATE כ-script עצמאי שרץ לפני כל submit (לא רק כצעד ב-SKILL)
- [ ] טריגר בזיכרון המובנה: "בתחילת כל משימה לא-טריוויאלית קרא pal-state"

## GBP אוטומציה
- [ ] ממתין לאישור מכסת Google API (ארכיטקטורה Python/FastAPI מתוכננת)
