# OPEN — משימות פתוחות
עודכן: 2026-07-07

## audit content-machine (2026-07-05)
- [ ] התקנת content-machine v7.15, brand-hub-machine v1.16, product-page-machine v7.1 (ZIPs נמסרו 2026-07-05; מחליפים את v7.13/v1.15)
- [x] דחיפת pal-lint v1.0.0 (tools/) — בוצע 2026-07-05
- [x] דחיפת pal-lint v1.1.0 (כיסוי מלא של חוסמי Elementor) — בוצע 2026-07-05
- [x] content-machine v7.13 נוצר — בלוק ה-Elementor המוטמע נמחק, שלב 13 מריץ pal-lint בלבד. ZIP אצל גיל, ממתין להתקנה
- [x] pal-lint v1.2.0: קליטת yoast_check / link_audit / schema_deep+WCAG + responsive/CTA/WAF-blog — בוצע 2026-07-05, selftest ירוק (12 fixtures)
- [x] pal-lint v1.2.2: תיקון שני false-positives של כללי מותג (BRAND_BEKO תפס "בקושי"; DELONGHI_FRIDGE תפס "מקרר"+"דלונגי" מרשימת מותגים) — בוצע 2026-07-08, selftest ירוק. sha f2f94584d5c8
- [x] pal-lint v1.3.0 (יישום אודיט הסקילים): ANCHOR_FORBIDDEN (ERROR) + ANCHOR_DUPLICATE/LINK_BUDGET/SPEAKABLE_MISSING (WARN) — בוצע 2026-07-08, selftest ירוק (13 fixtures). מוזג מעל v1.2.3, MAROM_PC_LINK נשמר.
- [ ] בירור v7.10-v7.11: האם קיימות כ-ZIP מחוץ למותקן; אם כן — יישום השינויים שלהן מעל v7.13
- [ ] פילוח חודשי ב-gsc pull (עונתיות) — הרחבת הסקריפט, ואז הסיגנל בשלב 2 נכנס לתוקף
- [ ] מילוי content-ledger.md רטרו: המאמרים שכבר פורסמו (מ-recent_chats + היסטוריה)

## brand-hub-machine
- [x] רטרו ל-5 עמודי מותג Marom (Haier, Blomberg, DeLonghi, Zanussi, Sharp→v1.16): offers חי מ-MCP + hex + מומחה מיכה איתן + לקחי v1.16. **הושלם 2026-07-08.**
  - [x] Haier — הושלם 2026-07-07, pal-lint v1.2.0 ירוק, ווידג'ט נמסר
  - [x] Blomberg / DeLonghi / Zanussi — הושלמו 2026-07-08 (הצינור חזר). Zanussi היה עדיין על var(--bh-*) והומר ל-hex
  - [x] Sharp — הושלם 2026-07-08, רטרו v1.12→v1.16 (var→hex + persona), pal-lint v1.2.2 ירוק
- [ ] פורward links: הגריד ב-5 העמודים מפנה ל-8 /brands/[brand]-service/ שעדיין 404 (kitchenaid/magimix/tefal/philips/moulinex/grundig/indesit/lavamat). גיל בונה בקרוב — לא לתקן ל-hubs חנות.

## תשתית — צינור MCP (חדש 2026-07-07)
- [ ] **שורש ה-lockup: auto-restart supervisor על תהליך stdio של WooCommerce MCP.** נפל 3× בשיחה אחת אחרי רצף check_url; לא קם עם reconnect ידני. הפעלה ידנית חוזרת = טיפול בסימפטום. צריך health-check שמזהה ניתוק ומרים מחדש, או wrapper עם restart-on-crash.
- [ ] באג check_url: קורס על נתיב עברי raw — `UnicodeEncodeError: 'ascii' codec` על נתיב עם תווים לא-ASCII. צריך urllib.parse.quote בשרת לפני הבקשה. עוקף כרגע ידנית עם percent-encoding.
- [ ] check_url חוסם subdomain: myarea.marom-serv.co.il מחזיר "דומיין מחוץ לאתרי Pal Group". ה-CTA הראשי בכל עמודי המותג (הזמנת טכנאי) לא ניתן לאימות דרך הכלי. להוסיף subdomains של האתרים לאלואוליסט.

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
