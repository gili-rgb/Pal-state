# PAL STATE
עודכן: 2026-07-05

> כללי ברזל (NAP, קישורים אסורים, טרמינולוגיה, פרוטוקול SKILL, Yoast) חיים בזיכרון המובנה. לא משוכפלים כאן.

---

## סקילים — גרסה + סטטוס

| סקיל | גרסה | סטטוס | פתוח |
|------|------|-------|------|
| content-machine | v7.13 | יציב, ממתין להתקנת ZIP | בירור: האם v7.10-v7.11 קיימות כ-ZIP מחוץ למותקן (הבסיס ל-v7.12 הוא v7.9 המותקנת) |
| brand-hub-machine | v1.15 | יציב, ממתין להתקנת ZIP | 3 עמודים צריכים תיקון Product schema רטרו |
| product-page-machine | v7.0 | יציב | — |
| ai-visibility-audit | v1.0 | פעיל | — |
| global-notes | — | פעיל | NOTES.md לא persists בין שיחות — לא מקור אמת |

### לקחי גרסה אחרונים (תקציר — הפירוט בזיכרון ובראש כל SKILL)
- content-machine v7.13: בלוק ה-VALIDATE Elementor המוטמע נמחק — pal-lint v1.1.0 (בריפו זה) הוא המקור היחיד; CONTENT/YOAST/LINKS/DEEP מוטמעים עד pal-lint v1.2.
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
- Sharp ✓ (עודכן ל-v1.12: offers block, hex, מומחה מיכה איתן, bh-pref-mini)
- Haier ✓
- Blomberg ✓ (×2 sessions)
- DeLonghi ✓

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
