# common-core — כללים משותפים לשלושת הסקילים (מקור אמת יחיד)

קובץ זה הוא המקום היחיד שבו כתובים הכללים המשותפים ל-content-machine, brand-hub-machine
ו-product-page-machine. הסקילים מפנים לכאן ולא משכפלים. עדכון כלל משותף = עדכון כאן בלבד
(+ עדכון pal_lint.py אם הכלל נאכף בקוד, + selftest באותה פעולה).

---

## 1. permalink — כלל הברזל המלא

השתמש ב-permalink שחוזר מ-WooCommerce MCP **בדיוק כפי שהוא** (verbatim). ה-MCP מחזיר
percent-encoding ב-lowercase, וזה מה ש-WordPress מקבל.
- **אסור** לקודד מחדש, אסור לשנות case ל-uppercase, אסור לבנות URL מתבנית. uppercase גורם 404.
- **Slug שנראה מקוצר/חתוך** (למשל `מיל` במקום `מילה`) נשאר בדיוק כפי שהוא. וורדפרס חותך
  slugs, ו"תיקון" למילה המלאה גרם 404 בפועל (לקח v7.11, 2.7.2026). חתוך = verbatim.
- **blog posts אינם ב-MCP:** אסור לבנות slug מכותרת. לכל blog post מקושר — `web_fetch`
  של ה-URL וחילוץ שדה `canonical`. ה-canonical הוא ה-permalink.

**חריג יחיד (כל ווידג'ט HTML באלמנטור):** slug עברי percent-encoded מפוענח לעברית raw
לפני ההטמעה ב-href (`/product/%d7%9e...` ← `/product/מסנן.../`) — רצף `%XX` ארוך (10+)
נחסם ב-WAF. **decode בלבד, לעולם לא encode**, זהות ה-slug נשמרת תו-בתו. כל טרנספורמציה
אחרת אסורה. pal-lint אוכף (WAF_ENCODED).

## 2. מרום: get_categories אסור

הרצת `get_categories` על alias=marom גורמת נעילה גלובלית של שרת ה-MCP (audit יוני 2026).
במרום: `search_products` בלבד. קטגוריות ופערי תוכן נגזרים משדה `categories` בתוצאות
המוצרים; קטגוריית האב לקישור נלקחת מ-permalink של קטגוריה שחוזר במוצרים או מקובץ הפרויקט.
`get_categories` מותר ב-csb וב-plrom בלבד.

## 3. Zero Hallucination — מדיניות מקורות

**מותר:** מפרטי/הוראות יצרן, אתר היבואן הרשמי, תקנים ישראליים (ת"י 60335, ת"י 900,
תקנות משרד האנרגיה), גופי אישור בשם (משמרת השבת), נתוני web עם מקור מצוין בשם,
ניסיון שירות שטח **איכותני בלבד** ("רוב המקרים", "תקלה שטכנאים נתקלים בה שוב ושוב").

**אסור:** אחוז/מספר ספציפי בלי מקור נתונים אמיתי — ייחוס ל"לדברי הצוות/הטכנאים" אינו
מקור; "מחקרים מראים" בלי שם המחקר; "מומחים אומרים" בלי שם; מחירים שלא מ-MCP חי;
**jeepolog.com אסור כמקור בכל צורה.** pal-lint אוכף (PERCENT_CLAIM, FORBIDDEN_SOURCE).

## 4. משמעת anchor (קישורים פנימיים)

- עוגן תיאורי בשפת לקוח, מתאר את יעד הקישור ("מסנן מוך מקורי למייבש", לא "המוצר").
- מגוון: לא אותו עוגן מדויק פעמיים לאותו יעד.
- **אסור:** "כאן", "לחץ כאן", "לחצו כאן", "קישור", "למידע נוסף", "קרא עוד" כעוגן.
- עוגן משלב מילת מפתח של היעד, לא של העמוד הנוכחי.
pal-lint אוכף (ANCHOR_FORBIDDEN=ERROR, ANCHOR_DUPLICATE=WARN, v1.3.0).

## 5. pal-lint — תנאי הגשה

אסור להגיש שום פלט בלי דוח ירוק (exit 0) מ-`tools/pal_lint.py` שב-clone של pal-state:
```bash
cd /home/claude/pal-state && python3 tools/pal_lint.py --site [csb|marom|plrom] \
  --type [blog|brandhub|product] [--keyword "מילת מפתח"] /path/to/FILE
```
ERROR = תקן והרץ מחדש. אזהרות = שיפוט ידני לפני הגשה. הדוח מצורף לכל הגשה.
הקובץ חסר ב-clone = חוסם, התרע לגיל. אחרי הלינט: link_audit ידני — `web_fetch` לכל
קישור פנימי מרשימת הלינט (200 חי + canonical זהה), למעט קישורים שאומתו באותה שיחה.

## 6. @id — מוסכמת prefix למניעת התנגשות עם Yoast (מ-v1.4.0, ERROR)

כל @id שאנחנו מגדירים בעצמנו ב-JSON-LD (לא רק מאוזכר) **אסור** שיסתיים בדיוק באחת
הסיומות: `#article`, `#organization`, `#breadcrumb`, `#website`, `#primaryimage`. אלה
סיומות קבועות של ה-@graph האוטומטי של Yoast (פעיל בכל האתרים), והתנגשות @id בין שני
`<script>` ld+json באותו עמוד גורמת ל-Rich Results Test לדווח breadcrumb/schema כלא
תקין (אומת חי ב-Rich Results Test, 2026-07-16). מוסכמה קבועה: content-machine →
`#content-*` (למשל `#content-article`, `#content-organization`, `#content-breadcrumb`),
brand-hub-machine → `#brandhub-*`. pal-lint אוכף (SCHEMA_ID_YOAST_COLLISION).

## 7. content-ledger — שורת רישום

כל פלט מסתיים בטיוטת שורה ל-`pal-state/content-ledger.md`:
```
| YYYY-MM-DD | [אתר] | [URL מתוכנן] | [H1] | [שאילתות יעד; מופרדות] | [blog/brandhub/product] |
```
גיל מאשר אחרי פרסום בפועל, והשורה נדחפת. בלי זה לולאת ה-dedup והמדידה
(ledger-performance.md השבועי ב-pal-gsc) לא נסגרת.
