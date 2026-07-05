# PAL STATE
עודכן: 2026-07-03

> כללי ברזל (NAP, קישורים אסורים, טרמינולוגיה, פרוטוקול SKILL, Yoast) חיים בזיכרון המובנה. לא משוכפלים כאן.

---

## סקילים — גרסה + סטטוס

| סקיל | גרסה | סטטוס | פתוח |
|------|------|-------|------|
| content-machine | v7.7 | יציב | — |
| brand-hub-machine | v1.12 | יציב | 3 עמודים צריכים תיקון Product schema רטרו |
| product-page-machine | v7.0 | יציב | — |
| global-notes | — | פעיל | NOTES.md לא persists בין שיחות — לא מקור אמת |
| pal-lint | v1.0.0 | פעיל | tools/pal_lint.py — gate חוסם לפני כל הגשה, selftest מלא |

### לקחי גרסה אחרונים (תקציר — הפירוט בזיכרון)
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
- Sharp ✓ (עודכן ל-v1.12: offers block, hex, מומחה מיכה לוי, bh-pref-mini)
- Haier ✓
- Blomberg ✓ (×2 sessions)
- DeLonghi ✓

---

## מבנה URL ונקודות תורפה ידועות
- Brand hub: /brands/[brand]-service/
- Pillar pages (/blomberg-service/) לא ניתנים לקישור ישיר → השתמש ב-/product-category/[brand]/
- MCP permalinks: lowercase percent-encoded verbatim. Exception: Elementor HTML widgets → raw Hebrew URLs (WAF חוסם %XX ארוכים)
- MCP freeze → Cmd+Q מלא ל-Claude Desktop. list_sites = probe מהיר. get_categories על marom = lock גלובלי, להימנע
