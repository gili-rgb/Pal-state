# פרויקט מרום — marom-serv.co.il

## מידע בסיסי

- **אתר:** https://marom-serv.co.il
- **CTA (אזור אישי):** https://myarea.marom-serv.co.il/login/

---

## עמודים מובילים GSC (snapshot סטטי — רפרנס מבני בלבד)

> ⚠️ טבלה זו היא צילום מצב היסטורי ומשמשת רק להיכרות עם מבנה העמודים המרכזיים. **אסור לבסס עליה בחירת נושא או נתוני ביצועים** — מקור האמת החי הוא `pal-gsc/cats/gsc_customer_language.md` ו-`ledger-performance.md` (שלב 0).

| URL | קליקים | חשיפות | CTR | מיקום |
|---|---|---|---|---|
| marom-serv.co.il/ | 33353 | 514775 | 6.5% | 14.0 |
| marom-serv.co.il/service-locator/ | 5824 | 309252 | 1.9% | 9.1 |
| marom-serv.co.il/צור-קשר/ | 15437 | 193817 | 8.0% | 7.7 |
| marom-serv.co.il/online-services/ | 1560 | 136914 | 1.1% | 5.0 |
| marom-serv.co.il/services/ | 794 | 127586 | 0.6% | 8.8 |
| marom-serv.co.il/sharp/ | 11337 | 125449 | 9.0% | 6.4 |
| marom-serv.co.il/אודות/ | 853 | 122731 | 0.7% | 5.0 |
| marom-serv.co.il/blomberg-service/ | 6407 | 106654 | 6.0% | 7.6 |
| marom-serv.co.il/beko/ | 5618 | 102794 | 5.5% | 7.1 |
| marom-serv.co.il/magimix/ | 4836 | 98381 | 4.9% | 7.0 |
| marom-serv.co.il/haier-service/ | 4693 | 91067 | 5.2% | 11.5 |
| marom-serv.co.il/all-products/ | 531 | 87965 | 0.6% | 6.8 |
| marom-serv.co.il/sharp-service/ | 2896 | 83388 | 3.5% | 6.3 |
| marom-serv.co.il/delonghi-service/ | 8630 | 76884 | 11.2% | 7.2 |
| marom-serv.co.il/tips-information/ | 287 | 73152 | 0.4% | 10.1 |

---

## מותגים

שארפ (Sharp), בלומברג (Blomberg), דלונגי (De'Longhi), האייר (Haier), קיצ'נאייד (KitchenAid), מג'ימיקס (Magimix), סמוראי (Samourai), טפאל (Tefal)

**אסור לכתוב תוכן למרום על: בקו (Beko) — הוצא לצמיתות.**

## קישורים: רשימות סגורות (הכרעת גיל, 2026-08-16)

> מקור האמת המכני הוא `SITES["marom"]` ב-`tools/pal_lint.py`. הרשימות כאן
> נועדו לקריאה בזמן כתיבה, ואסור לערוך אותן בנפרד מהלינט.
> **רשימה סגורה ולא תבנית:** אין כוונה להוסיף עמודי שותפים חדשים.

**אסור לקשר (16 עמודי שותף):**
`/sharp-service/` `/sharp-parts/` `/blomberg-service/` `/blomberg-parts/`
`/haier-service/` `/haier-parts/` `/delonghi-service/` `/delonghi-parts/`
`/dedietrich-service/` `/dedietrich-parts/` `/bauknecht-service/` `/bauknecht-parts/`
`/amana-service/` `/amana-parts/` `/zanussi-service/` `/zanussi-parts/`

**מותר לקשר, עמודי מותג (17):**
`/brands/` + `sharp-service` `blomberg-service` `haier-service` `delonghi-service`
`zanussi-service` `amana-service` `bauknecht-service` `moulinex-service`
`philips-service` `magimix-service` `kitchenaid-service` `tefal-service`
`grundig-service` `lavamat-service` `indesit-service`
ובנוסף `/kitchenaid-parts/` ו-`/magimix-parts/`, שהם שלנו ולא של השותף.

שים לב להבחנה: `/bauknecht-service/` אסור, `/brands/bauknecht-service/` מותר.
כתיב שגוי בכתובת מותג נחסם ב-`BRAND_LINK_UNKNOWN`.

**עמודי `/product-category/` מותרים לקישור.** 420 עמודים, 308,604 חשיפות,
12,847 קליקים, 73 מהם במיקום 1-3. הכלל `MAROM_PC_LINK` שחסם אותם נמחק
ב-pal-lint v1.12.0 אחרי שהתברר שהנימוק שלו ("כמעט תמיד 301/404") שגוי.
כמו כל קישור פנימי, גם הם מחייבים אימות `check_url` חי לפני הגשה.

**שפות:** עמוד מתורגם הוא אותו עמוד. `/en/brands/amana-service/` זהה
ל-`/brands/amana-service/` בכל הבדיקות.

## CTA

- אזור אישי: https://myarea.marom-serv.co.il/login/
- יצירת קשר: https://marom-serv.co.il/צור-קשר/

## YouTube

אין ערוץ ייעודי לאתר. עדיפות: סרטון מערוץ המותג הרשמי. אמת שהערוץ רשמי לפני הטמעה - לא ערוץ אוהדים ולא מוסך פרטי. אם אין סרטון מאומת: מחק את בלוק הווידאו (.video-container) לגמרי. בלי placeholder, בלי הערה.

**ערוצי מותג רשמיים מאומתים (אנגלית):**

שארפ (Sharp):
- אירופה: youtube.com/channel/UCg8X1NFBPH24E5T92_rqjVw (SHARP Consumer Electronics Europe)
- ארה"ב: youtube.com/channel/UCGaxcBNr7-plZiFqwxDyL8Q (Sharp Home USA)
- קיימים גם ערוצי Sharp באנגלית בתאילנד/מלזיה/הודו, אמת בזמן ריצה.

קיצ'נאייד (KitchenAid):
- גלובלי: youtube.com/kitchenaid
- בריטניה: youtube.com/@kitchenaiduk2003
- אוסטרליה וניו זילנד: youtube.com/@KitchenaidANZ

דלונגי (De'Longhi):
- גלובלי: youtube.com/channel/UCYMkDbjIsC4Wb4j0_kqnAOA
- ארה"ב/צפון אמריקה: youtube.com/delonghiusa
- בריטניה: youtube.com/c/delonghiukofficial
- אוסטרליה: youtube.com/channel/UCfpFVwekdmwy3K8rcBoBlnw
- סינגפור: youtube.com/@delonghisg
- דרום מזרח אסיה: youtube.com/channel/UCsmvuQz86QNwW9rFw1uVS6A
- הדרכות תחזוקה/הפעלה: youtube.com/channel/UC26bZXdoK-DikivN5IYkViw (De'Longhi How-To)

האייר (Haier):
- אירופה: youtube.com/c/HaierEurope
- הודו: youtube.com/c/haierindia
- אוסטרליה: youtube.com/channel/UCgGlf-0QnAbe_en124EDw9A
- אמריקה: youtube.com/channel/UCUliTFMtrGzTamS3gB2tdAg
- בנגלדש: youtube.com/@haierbangladesh

בלומברג (Blomberg): youtube.com/channel/UCBt0NH7l0KVtI6LItfUSf2Q (Blomberg Appliances USA)

מג'ימיקס (Magimix): youtube.com/channel/UC_9meoutRrSIp2WnuOGBmsA (Magimix Australia). קיים גם ערוץ Magimix UK, אמת handle בזמן ריצה.

טפאל (Tefal):
- בינלאומי: youtube.com/tefal
- בריטניה: youtube.com/user/UKTefal
- אוסטרליה: youtube.com/channel/UCblJHM6RmLhKyaEEzMyA5Lg
- הודו: youtube.com/channel/UCaOzgsHrVSWONg-mfpNCEOQ
- מלזיה: youtube.com/channel/UCvq60u9ipXuOYQoDFzU5zng
- מזרח תיכון: youtube.com/channel/UCTYZqLuDlTD3ZOgf3WxJmlA

סמוראי (Samurai): אין ערוץ רשמי גלובלי מאומת באנגלית. חפש בזמן ריצה ואמת, אחרת מחק את בלוק הווידאו לגמרי.

## ארגון

- **חברת שירות:** מרום שירותים ואחזקה בע"מ
- **תיאור:** חברת השירות הרשמית למוצרי חשמל מבית שארפ, בלומברג, האייר, זנוסי, באוקנכט, פיליפס, דלונגי, מג'ימיקס וקיטשן אייד
- **סניף ראשי:** הצורף 3, חולון, 5885631
- **טלפון:** *2620

**בלוק Organization קנוני — העתק verbatim, אל תנסח מחדש (v7.22):**
```json
{
  "@type": "Organization",
  "@id": "https://marom-serv.co.il/#content-organization",
  "name": "מרום שירותים ואחזקה בע\"מ",
  "alternateName": "שירות מרום",
  "url": "https://marom-serv.co.il",
  "telephone": "*2620",
  "description": "[משפטים 1-2 מהנרטיב הקנוני, ראה סעיף נרטיב]",
  "sameAs": [
    "https://www.youtube.com/@user-marom-serv/videos",
    "https://marom-serv.co.il/אודות/"
  ]
}
```
`sameAs` הוא שדה חובה ואינו נתון לשיקול דעת. נאכף כ-ERROR ב-pal-lint (`ORG_SCHEMA_DRIFT`, v1.6.0). הדריפט נצפה ב-2026-08-03: מאמר אחד כלל את ערוץ היוטיוב, מאמר אחר באותו יום השמיט אותו.

**סניפים:**
- ירושלים: המדפיסים 10, אזור תעשייה עטרות, ירושלים
- דרום: הדסה 22, באר שבע
- צפון: דרך המוסכים 24, מפרץ חיפה

לתוכן בעל כוונה מקומית (שירות בעיר מסוימת): אזכר את הסניף הרלוונטי והוסף את העיר ל-areaServed ב-Schema. כתובת ה-LocalBusiness תמיד הסניף הראשי.

## נרטיב מותג (משפטים קנוניים)

מקור אמת יחיד לנרטיב. LLM מרכיב את סיפור המותג מ-5-7 משפטים קנוניים שחוזרים בעקביות בכל הנכסים (Lazarina Stoy, Campixx 2026). **הזרק ל-Direct Answer** (משפט קנוני אחד לפחות) **ול-`description` של Organization schema** (משפטים 1-2, הרחבה של שדה "תיאור" בסעיף ארגון ועקביים איתו). author-bio ו-Person מכוסים ע"י סעיף "מומחה", לא ע"י הנרטיב. עקביות מונעת Data Conflict ומחזקת ביטחון מודל. **טיוטה מבוססת עובדות — גיל מאשר/מדייק את הניסוח הסופי (מסר מותג).**

**5 משפטים קנוניים:**
1. מרום שירותים ואחזקה היא חברת השירות הרשמית למגוון מותגי חשמל בישראל.
2. מרום נותנת שירות למותגי שארפ, בלומברג, האייר, זנוסי, באוקנכט, פיליפס, דלונגי, מג'ימיקס וקיטשן אייד.
3. לכל מותג מרום פועלת כזרוע השירות הרשמית של היבואן.
4. השירות כולל תיקונים, אבחון תקלות וחלקי חילוף מקוריים.
5. מרכז השירות בחולון, עם סניפים בירושלים, באר שבע וחיפה.

**8 תכונות מותג (attributes לחיזוק עקבי):** שירות רב-מותגי רשמי, זרוע שירות של יבואנים, חלקי חילוף מקוריים, פריסה ארצית, אבחון תקלות מקצועי, מעבדות שירות, טכנאי שטח, מומחיות רב-מותגית.

## מומחה (E-E-A-T, Person schema + author-bio)

מקור אמת יחיד לפרטי המומחה. `author-bio` ו-Person schema נשענים על זה verbatim. Tom Winter (Campixx 2026): "Trust זה לא להוסיף ביוגרפיית כותב" — לכן ה-bio חייב הוכחה, לא תיאור. אל תמציא נתונים אישיים. מלא רק מהמאומת למטה. שדות ב[סוגריים] = גיל משלים פעם אחת מנתון אמיתי. עד שגיל ממלא — השתמש רק בעוגן הסמכות הארגוני המאומת, בלי להמציא שנים או הסמכות.

- **שם:** מיכה איתן
- **avatar (ראשי תיבות):** מ
- **תפקיד:** מנהל טכני ויבוא במרום שירותים ואחזקה
- **עוגן סמכות (מאומת):** זרוע השירות הרשמית של יבואני המותגים שמרום מייצגת (שארפ דרך ראלקו, דלונגי מוצרים גדולים דרך ניופאן, ועוד). התאם את היבואן למותג המדובר בעמוד — אל תטען "רשמי" לקטגוריה שיבואן אחר מייבא (ראה שלב 1 ב-brand-hub)
- **התמחות (knowsAbout):** תיקון ותחזוקת מוצרי חשמל ביתיים, אבחון תקלות רב-מותגי, חלקי חילוף מקוריים, ניהול יבוא
- **הוכחת ניסיון:** התפקיד "מנהל טכני ויבוא" משמש עוגן סמכות. [גיל: אם יש נתון שנים/היקף, הוסף]
- **sameAs (הוכחה חיצונית ל-Person schema):** [גיל: אם יש LinkedIn/פרסום רשמי, הוסף URL מלא. הקישור share.google שנמסר חסום לאימות אוטומטי]
