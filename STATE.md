# PAL STATE
עודכן: 2026-08-16 (v8.17, pal-lint v1.14.0, version_guard v1.3, 8 שערי CI, שישה מקורות מדידה)

> כללי ברזל (NAP, קישורים אסורים, טרמינולוגיה, פרוטוקול SKILL, Yoast) חיים בזיכרון המובנה. לא משוכפלים כאן.

---

## סקילים — גרסה + סטטוס

| סקיל | גרסה | סטטוס | פתוח |
|------|------|-------|------|
| content-machine | **v8.17** | מותקן. נהג של preflight/postflight | ריצת אימות ראשונה בוצעה; מאמר Refresh פורסם 2026-08-10 |
| brand-hub-machine | v1.17 | מותקן, **לא עודכן לארכיטקטורת v8** | לא מכיר preflight/postflight/BRAND_SAMEAS/קטלוג וידאו |
| product-page-machine | v7.0 | מותקן, **לא עודכן לארכיטקטורת v8** | אותו פער |
| ai-visibility-audit | v1.1 | פעיל | baseline 2026-07-08. לא נמדד מחדש |
| off-site-radar | v1.0 | פעיל | baseline 2026-07-08 |
| pal-lint (tools/) | **v1.14.0** | selftest ירוק | 108 כללים (עם postflight) |
| preflight.py (tools/) | **v1.8** | brief רזה 42KB + מלא 123KB | allowed_topics, refresh_queue, dominant_pages, partner_dominated, pricing, ai_agent, intent |
| postflight.py (tools/) | **v1.5** | שער יציאה | EVASIVE_ANSWER, NO_CONVERSION_PATH, AI_CHANNEL, DOMINANT_LINK, **DOMINANT_H1_DUPLICATE**, REFRESH_* |
| ledger_lint (v1.1, STALE_NOT_YET), version_guard (**v1.2**), ledger_merge, ledger_patch | v1.0-1.2 | ב-CI | **8 שערים** על כל push: ledger_lint, selftest, test_flight, test_postflight, test_ledger_tools, **test_can_publish**, test_version_guard, version_guard |
| ai_visibility_pull, ga_pull, bing_ai_presence, gbp_analyze, youtube_pull | — | ב-pal-gsc-data | שישה מקורות מדידה, קרון אוטומטי |

### לקחי גרסה אחרונים (תקציר — הפירוט בזיכרון ובראש כל SKILL)
- **2026-08-16 (חסימה שקטה בת עשרה ימים + השער שהיה חסר):** `BRAND_HUB_MISSING` נוסף ב-v1.9.0 כ-ERROR גורף. **לפלרום אפס עמודי `/brands/`, ולכן כל מאמר פלרום היה בלתי אפשרי לפרסום מ-6 באוגוסט.** ה-CI היה ירוק כל הזמן. **הכרעת גיל: אין צורך בעמוד מותג כדי לכתוב מאמר בפלרום** — שדה `brand_hub_required` (plrom=False). בנוסף: מותג מוחרג יוצא מתור ה-Refresh (עמוד אלקטרה ישב במקום 2 בפלרום עם 23,698 חשיפות ומיקום 1.6, בזמן ש-`BRAND_ELECTRA` חוסם אותו).
- **שער CI שמיני `test_can_publish` — הבדיקה שהייתה חסרה.** כל שער נבדק מול fixture משלו ("האם הכלל תופס"), ואף בדיקה לא שאלה את ההפך ("האם עדיין אפשר לכתוב מאמר"). מאמר מינימלי-תקין לכל אתר חייב לעבור `exit 0`. **אומת שהוא נכשל על המצב הקודם.** **לקח: מערכת הגנות שגדלה מהר צריכה בדיקה שמודדת את היכולת לעבוד, לא רק את איכות ההגנה.**
- **2026-08-16 (D2 שלב ד, מותגי מרום):** סעיף "מותגים" מנה 8 בזמן שיש תנועה על מעל 20. **הכרעת גיל: עמוד מותג אינו תנאי לכתיבה** — מותג עם תוכן טוב וחשיפות מותר גם בלי `/brands/` (סמוראי, 13,416 חשיפות). הרשימה נבנתה ממיפוי GSC ומחולקת לשלוש שכבות, וההחרגות נכתבו לצידה. **חשיפות לבדן אינן מתירות כתיבה:** בקו אסורה לחלוטין למרות 12,131 חשיפות. הופרדה שכבת אלקטרוניקה שאינה שירות: הייסנס, TCL, בוס ו-JBL הם חלפים בלבד (שלטים ורמקולים) ומרום אינה נותנת להם שירות. **TCL כן מותג שירות של פלרום.**
- **2026-08-16 (D2 שלב ג, סגירת placeholders):** שני שדות ממוענים לגיל ישבו שישה שבועות ב-`project-marom.md`, קובץ שנקרא `verbatim`. הכרעת גיל: אלה כל הנתונים על מיכה איתן. `sameAs` מושמט מישות ה-`Person`, ואין להוסיף שנות ניסיון. **מרום שומרת `Person` ופלרום לא, כי ההבדל הוא שם ותפקיד מאומתים ולא ה-`sameAs` שחסר בשתיהן.** `version_guard` v1.3: `OPEN_PLACEHOLDER` (ERROR) על `[גיל:` בקובצי סקיל. **לקח: placeholder בקובץ מקור אמת הוא חוב שקט שאף דוח לא מציג.**
- **2026-08-16 (D2 שלב ב, סמכות ארגונית לפלרום):** `SITES` הגדיר `expert="דניאל"`, אבל `project-plrom.md` מעולם לא החזיק תפקיד או `sameAs`. התוצאה: ישות `Person` בכל מאמר פלרום בלי הוכחה חיצונית. **הכרעת גיל: עוגן סמכות ארגוני.** פלרום מייצרת מעכשיו **5 ישויות** (בלי Person, `author`→`#content-organization`), `"דניאל"` עבר ל-`wrong_experts`, ושני כללים חדשים `PERSON_ENTITY_FORBIDDEN` ו-`AUTHOR_NOT_ORG`. **הפיך** ברגע שיתקבלו שם, תפקיד ו-sameAs אמיתיים. **לקח: אדם שאי אפשר לאמת אי אפשר לצטט, וארגון אמיתי חזק מאדם ריק.**
- **2026-08-16 (D2 שלב א, שכבת הקישורים של מרום):** `MAROM_PC_LINK` **נמחק**. הכלל חסם `/product-category/` במרום בטענה שהוא "כמעט תמיד 301/404", והנתונים מראים **420 עמודים, 308,604 חשיפות, 12,847 קליקים, 73 במיקום 1-3**. `preflight` המליץ על אותם עמודים ש-`postflight` חסם, חזרה מדויקת של כשל v8.12. במקומו: **רשימות סגורות** (הכרעת גיל, לא תבנית) — 16 עמודי שותף אסורים ללא שינוי, ו-17 עמודי מותג מאושרים ב-`allowed_brand_links`, כולל `/kitchenaid-parts/` ו-`/magimix-parts/` שהם שלנו. כלל חדש `BRAND_LINK_UNKNOWN` תופס כתיב שגוי בכתובת מותג. **עמוד מתורגם = עמוד המקור** (`base_brand_path` מנרמל en/ru/ar/fr). **לקח: כלל גס ששרד אחרי שהפתרון הנכון נכנס.** `link_audit` כבר כיסה את הסיכון האמיתי מאותו יום.
- **2026-08-13 (ערב, סגירת כפילות D1):** `SKILL.md` החזיק 21 רשומות היסטוריה שקיימות גם ב-`CHANGELOG.md`, **וארבע מהן כבר התפצלו לשני טקסטים תחת אותו מספר גרסה** (v7.20 ב-19% דמיון בלבד). `version_guard` התיר את זה במפורש, כלומר השער שנבנה למנוע שתי גרסאות מקבילות אישר בדיוק אותו דפוס. 20 רשומות נמחקו מ-`SKILL.md` אחרי הצלבה שהוכיחה שכל תוכן תפעולי כבר קיים בגוף הקובץ או בקוד (69.7KB → 54.8KB). `version_guard` v1.2 חוסם מעכשיו ב-`CHANGELOG_DUPLICATE` ו-`CHANGELOG_DRIFT`, ושער CI שביעי `test_version_guard` (14 בדיקות) מוודא שהכלי עצמו עובד. **לקח: כלל אכיפה בלי בדיקה משלו הוא הבטחה ולא שער.** הפירוט ב-`tools/CHANGELOG-tools.md`.
- **2026-08-13 (תיקון עובדתי):** `brief_partial` הוא **42KB** ו-`brief_full` 123KB, נמדד בהרצת `preflight --phase plan --site marom`. הרשומה ב-`CHANGELOG.md` נשאה 17KB, מספר שגוי.
- **תיעוד שינויים בכלים חי ב-`tools/CHANGELOG-tools.md`** (מ-2026-08-13). שינוי ב-tools/ אינו מזיז את גרסת content-machine ואינו נוגע ב-SKILL.md.
- **2026-08-13 (שני שערים חדשים):** `DOMINANT_H1_DUPLICATE` ב-postflight v1.5 חוסם H1 שמשכפל שאילתה שעמוד שלנו מחזיק במיקום 1-3 (הרקע: שני מאמרי שארפ במרום על אשכול במיקום 1.0 עם 19,687 חשיפות, שניהם על אפס). `STALE_NOT_YET` ב-ledger_lint מתריע על שורת "טרם צבר" מעל 90 יום. שער CI שישי: `test_ledger_tools`.
- **2026-08-10 (ריצה מוצלחת ראשונה):** מאמר Refresh למרום (`/חלקי-חילוף-למקרר-שארפ/`) עבר את השרשרת המלאה: preflight → finalize → postflight ירוק. שכבת הדדופ תפסה כפילות 100% והפכה מאמר חדש ל-Refresh. נוספו למאמר: דנה (AI channel), `sameAs` לשארפ, וטבלת מחירים במקום "פנו אלינו". **שתי לחיצות "המשך" בלבד** אחרי צמצום ה-brief.
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
- **סבב סיווג NO_GSC_DATA (2026-08-13):** 12 השורות שסומנו "אין נתונים" הוצלבו מול `cats/{site}_page_queries.json` ומול datePublished חי דרך WooCommerce MCP. תוצאה: 1 קיים ב-GSC ומולא בשאילתות בפועל, 8 "טרם צבר" (פורסמו פחות מ-3 חודשים), 3 מועמדי Refresh. עמודת התאריך מולאה מ-datePublished אמיתי בכל 12 השורות. `ledger_lint`: 20 → 8 אזהרות, NO_GSC_DATA = 0.
- **פורמט תא מסווג:** `טרם צבר (YYYY-MM) · שאילתה1; שאילתה2; שאילתה3` או `מועמד Refresh (YYYY-MM) · ...`. הסימון והשאילתות יחד, כדי ששער ה-dedup לא יישאר עיוור בשורה כמו שקרה עם "אין נתונים".

## מבנה URL ונקודות תורפה ידועות
- Brand hub: /brands/[brand]-service/
- Pillar pages (/blomberg-service/) לא ניתנים לקישור ישיר → השתמש ב-/product-category/[brand]/
- MCP permalinks: lowercase percent-encoded verbatim. Exception: Elementor HTML widgets → raw Hebrew URLs (WAF חוסם %XX ארוכים)
- MCP freeze → Cmd+Q מלא ל-Claude Desktop. list_sites = probe מהיר. get_categories על marom = lock גלובלי, להימנע
