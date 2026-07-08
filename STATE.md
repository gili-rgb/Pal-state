# PAL STATE
עודכן: 2026-07-08 (רטרו brand-hub v1.16 הושלם 5/5 + pal-lint v1.2.2)

> כללי ברזל (NAP, קישורים אסורים, טרמינולוגיה, פרוטוקול SKILL, Yoast) חיים בזיכרון המובנה. לא משוכפלים כאן.

---

## סקילים — גרסה + סטטוס

| סקיל | גרסה | סטטוס | פתוח |
|------|------|-------|------|
| content-machine | v7.15 | ZIP נמסר 2026-07-05, ממתין להתקנה (מותקן: v7.14) | בירור v7.10-v7.11 |
| brand-hub-machine | v1.16 | ZIP נמסר 2026-07-05, ממתין להתקנה (מותקן: v1.15) | רטרו hex+offers הושלם 2026-07-08: Haier ✓ Blomberg ✓ DeLonghi ✓ Zanussi ✓ Sharp ✓ (כל 5 עמודי Marom) |
| product-page-machine | v7.1 | ZIP נמסר 2026-07-05, ממתין להתקנה (מותקן: v7.0) | references נבנו מחדש (נפלו מ-ZIP v7.0) |
| ai-visibility-audit | v1.0 | פעיל | — |
| global-notes | — | מומלץ למחיקה (זומבי: NOTES.md לא persists, pal-state החליף) | — |
| pal-lint (tools/) | v1.2.2 | selftest ירוק, 12 fixtures | — |

### לקחי גרסה אחרונים (תקציר — הפירוט בזיכרון ובראש כל SKILL)
- 2026-07-08 (רטרו brand-hub v1.16 הושלם, 5/5 עמודי Marom): כל עמוד קיבל offers חי מ-MCP + persona מיושר (מיכה איתן, מנהל טכני ויבוא — לא "מיכה לוי"). Zanussi+Sharp נמצאו עדיין על var(--bh-*) הישן והומרו ל-hex קשיח (חוסם Elementor edit 27). pal-lint עלה v1.2.0→v1.2.2: שני false-positives של כללי מותג תוקנו בשורש — BRAND_BEKO ("בקו" תפס "בקושי"/"המתנה בקו") ו-DELONGHI_FRIDGE ("מקרר" מעמוד אחר + "דלונגי" מרשימת מותגים). שניהם עברו לבדיקה פסקה-פסקה/הקשר-מותג. sha f2f94584d5c8.
- 2026-07-05 (audit חוצה-סקילים): pal-lint v1.2.0 קלט את כל הבדיקות המוטמעות (Yoast, Zero-Hallucination, schema עמוק, WCAG, responsive, CTA, WAF גם בבלוג) — אפס לוגיקת בדיקה בסקילים. content-machine v7.15: אין ישות Product בבלוג (mentions=Brand). brand-hub v1.16: תבניות hex קשיח (77 var הומרו) + טבלת צבעים לפי תפקיד ואתר + שער קיום/רענון. PPM v7.1: מומחה מקובץ project (CSB=אילן שמה, לא סמי), שלב 0 MCP+GSC, pal-lint על Markdown. טלפון מרום קנוני: *2620.
- content-machine v7.13: בלוק ה-VALIDATE Elementor המוטמע נמחק — pal-lint הוא המקור היחיד.
- content-machine v7.12 (audit 2026-07-05): מרום בלי get_categories; כלל decode ל-permalink; שער אנטי-קניבליזציה (מיקום 4-25 = עמוד קיים מדורג, ברירת מחדל Refresh); content-ledger כמקור dedup ראשון; brand hub בתקציב הקישורים; אכיפת Yoast/קישורים/Schema בקוד (yoast_check, link_audit, schema_deep).
- brand-hub-machine v1.15: יישור שני הכללים המשותפים (מרום get_categories, decode).
- content-machine v7.7: כל CSS ל-hex קשיח. אפס var()/token/CSS comments ב-<style>. טבלת צבעים role-aware per-site. VALIDATE Step 13.
- brand-hub-machine v1.12: Product schema מחייב offers block עם דאטה חי מ-MCP. VALIDATE Step 11. backslash מ-geresh = חוסם publish.

---

## פרויקטים פעילים

### Maya (סוכן קולי)
- סטטוס: אודיט טכני מלא הושלם (63K שורות Python backend)
- המלצת ליבה: גילוי AI במסגור חיובי בונה אמון יותר מהסתרה
- פתוח: A/B opening script | hebrew_pronunciation.py | HeyGen Israeli-accent voice clone

### צינור GSC/Bing
- סטטוס: יציב, רץ בסנדבוקס (לא Railway)
- ריפו: gili-rgb/pal-gsc-data (ציבורי)
- GSC: csb/plrom = sc-domain | marom = URL-prefix https://marom-serv.co.il/ בלבד
- Bing: AvgImpressionPosition = מיקום שלם אמיתי, לא לחלק ב-10
- ~1,517 שאילתות מסווגות ב-md, CSV מלא לא נדחף לריפו

---

## עמודי מותג שנבנו (per-site)

### Marom
עמודים חיים (check_url 200): Sharp, Haier, Blomberg, DeLonghi, Zanussi.
סבב רטרו hex+offers+מומחה+v1.16 (סדר: get_page_html → פץ' → pal-lint → check_url → מסירה):
- Haier ✓ רטרו הושלם 2026-07-07 — offers חי 383 ILS (SKU 87-08-02526-00-), 5 var→hex, backslash הוסר, מיכה איתן, *2620, pal-lint v1.2.0 ירוק. ווידג'ט נמסר.
- Blomberg — ממתין (צינור MCP נפל אחרי סבב Haier, לא קם)
- DeLonghi — ממתין
- Zanussi — ממתין
- Sharp — ממתין (רטרו חוזר ל-v1.16; היה v1.12)
פתוח: הגריד ב-5 העמודים מקשר ל-8 /brands/[brand]-service/ שעדיין 404 (kitchenaid/magimix/tefal/philips/moulinex/grundig/indesit/lavamat). גיל בונה אותם בקרוב — הושארו כ-forward links בכוונה, לא לתקן ל-hubs חנות.

---

## content-ledger
- `content-ledger.md` בריפו זה = רשומה קנונית של כל מאמר בלוג שפורסם (תאריך, אתר, URL, H1, שאילתות יעד).
- מקור dedup ראשון בשלב 2 של content-machine (v7.12+). שורה חדשה נוספת אחרי אישור פרסום של גיל (טיוטה מופקת בשלב 14).
- עתידי: הצלבה אוטומטית מול משיכת GSC שבועית לדוח before/after.

## מבנה URL ונקודות תורפה ידועות
- Brand hub: /brands/[brand]-service/
- Pillar pages (/blomberg-service/) לא ניתנים לקישור ישיר → השתמש ב-/product-category/[brand]/
- MCP permalinks: lowercase percent-encoded verbatim. Exception: Elementor HTML widgets → raw Hebrew URLs (WAF חוסם %XX ארוכים)
- MCP freeze → Cmd+Q מלא ל-Claude Desktop. list_sites = probe מהיר. get_categories על marom = lock גלובלי, להימנע
