# PAL STATE
עודכן: 2026-08-10 (v8.13, 108 כללים, 5 שערי CI, שישה מקורות מדידה)

> כללי ברזל (NAP, קישורים אסורים, טרמינולוגיה, פרוטוקול SKILL, Yoast) חיים בזיכרון המובנה. לא משוכפלים כאן.

---

## סקילים — גרסה + סטטוס

| סקיל | גרסה | סטטוס | פתוח |
|------|------|-------|------|
| content-machine | **v8.13** | מותקן. נהג של preflight/postflight | ריצת אימות ראשונה בוצעה; מאמר Refresh פורסם 2026-08-10 |
| brand-hub-machine | v1.17 | מותקן, **לא עודכן לארכיטקטורת v8** | לא מכיר preflight/postflight/BRAND_SAMEAS/קטלוג וידאו |
| product-page-machine | v7.0 | מותקן, **לא עודכן לארכיטקטורת v8** | אותו פער |
| ai-visibility-audit | v1.1 | פעיל | baseline 2026-07-08. לא נמדד מחדש |
| off-site-radar | v1.0 | פעיל | baseline 2026-07-08 |
| pal-lint (tools/) | **v1.11.0** | selftest ירוק | 108 כללים (עם postflight) |
| preflight.py (tools/) | v1.7 | brief רזה 41KB + מלא | allowed_topics, refresh_queue, dominant_pages, partner_dominated, pricing, ai_agent, intent |
| postflight.py (tools/) | v1.4 | שער יציאה | EVASIVE_ANSWER, NO_CONVERSION_PATH, AI_CHANNEL, DOMINANT_LINK, REFRESH_* |
| ledger_lint, version_guard, ledger_merge | v1.0 | ב-CI | 5 שערים על כל push |
| ai_visibility_pull, ga_pull, bing_ai_presence, gbp_analyze, youtube_pull | — | ב-pal-gsc-data | שישה מקורות מדידה, קרון אוטומטי |

### לקחי גרסה אחרונים (תקציר — הפירוט בזיכרון ובראש כל SKILL)
- **2026-08-10 (מדידה): השרשרת נסגרה.** שישה מדדים אוטומטיים: `ai_visibility` (Gemini, 11/15), `ai_presence` (Bing מול GSC — למה לא מצוטטים), GSC, GA4 (המרות), GBP (5,637 שיחות בחודשיים ל-CSB), קטלוג יוטיוב. **הממצא המרכזי:** מנצחים 5/5 בשאילתות מותג, מפסידים 0/4 בטכניות; עמודי מוצר ממירים 30-37% ומאמרי תוכן אפס; פי 2.5 יותר אנשים מתקשרים מאשר נכנסים לאתר.
- **2026-08-10 (הכרעות גיל):** (1) לא כל עמוד חייב להמיר — סיווג `conversion`/`authority`/`service`, וכל אחד נמדד אחרת. (2) המטרה להסיט שיחות מהמוקד לנציגת ה-AI, לא להגדיל אותן. (3) עמוד שמדורג 1-3 הוא נכס לקשר אליו, לא נושא לשכפל. (4) **לעולם לא לקשר לעמודי שותפים** — מותר לקחת מהם מילות מפתח בלבד.
- **2026-08-10 (לקח תהליכי):** שלוש פעמים הוספתי מנגנון בלי לבדוק אותו מול כללים קיימים, ונוצרה סתירה. `test_flight` מריץ עכשיו כל URL שה-brief ממליץ עליו דרך `pal_lint` האמיתי.
- **2026-08-06 (ארכיטקטורת v8, יום מרוכז): הסקיל הפסיק להיות רשימת הוראות והפך לנהג של שני סקריפטים.** שלב 0 = `preflight.py` מייצר `brief.json` (allowed_topics, refresh_queue, brand_hub_gaps, vocabulary מאומת, canonical_sentences, brand_hubs, video). שלב 13 = `postflight.py` (12 בדיקות מול ה-brief + pal_lint). **צ'קליסט השיפוט ירד מ-30 פריטים ל-2.** מקור התובנה: כל תיקון שנכתב כהוראה בפרוזה חזר; רק קוד אוכף. 96 כללים נאכפים.
- 2026-08-06 (מקורות דאטה): `gsc_page_queries.py` (page+query, 72K צמדים) → מיפוי URL לשאילתות אמיתיות, גיבוי 111/123 שורות ledger. `youtube_pull.py` → 126 סרטונים משלושת הערוצים (properties של ערוצים אינם מוחזרים מ-Search Console API). autocomplete כמקור הזדמנויות שני: מלאי נושאים 43 → 351.
- 2026-08-06 (עמודי מותג): CSB בנה 4 עמודים ביולי והם על **אפס חשיפות**, בעוד עמודי השותפים בשורש קולטים 264K. 301 אינו אפשרי עסקית. הפתרון: `BRAND_HUB_MISSING` (ERROR) — כל מאמר חייב קישור ל-/brands/.
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

מקור אמת: `preflight --phase plan` מדפיס רישום חי עם חשיפות. הנתונים מ-2026-08-06.

| אתר | קיימים | עם תנועה | על אפס |
|-----|--------|----------|--------|
| Marom | 14 | 8 (sharp 3,575 / delonghi 2,360 / haier 1,878 / blomberg 1,106) | 6 (moulinex, kitchenaid, magimix, grundig, indesit) |
| CSB | 4 | 0 | 4 (bosch, siemens, constructa, gaggenau — gaggenau 13 חשיפות) |
| Plrom | **0** | — | — |

**Plrom הוא הפער הגדול ביותר:** אפס עמודי מותג, ו-`/miele-service/` של השותף קולט "שירות מילה" 11,105 + "מילה שירות לקוחות" 9,954 חשיפות.

## content-ledger
- `content-ledger.md` בריפו זה = רשומה קנונית של כל מאמר בלוג שפורסם (תאריך, אתר, URL, H1, שאילתות יעד).
- מקור dedup ראשון בשלב 2 של content-machine (v7.12+). שורה חדשה נוספת אחרי אישור פרסום של גיל (טיוטה מופקת בשלב 14).
- עתידי: הצלבה אוטומטית מול משיכת GSC שבועית לדוח before/after.

## מבנה URL ונקודות תורפה ידועות
- Brand hub: /brands/[brand]-service/
- Pillar pages (/blomberg-service/) לא ניתנים לקישור ישיר → השתמש ב-/product-category/[brand]/
- MCP permalinks: lowercase percent-encoded verbatim. Exception: Elementor HTML widgets → raw Hebrew URLs (WAF חוסם %XX ארוכים)
- MCP freeze → Cmd+Q מלא ל-Claude Desktop. list_sites = probe מהיר. get_categories על marom = lock גלובלי, להימנע
