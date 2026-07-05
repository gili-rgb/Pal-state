# pal-lint v1.0.0
שכבת אכיפה דטרמיניסטית לכל פלט HTML (content-machine / brand-hub-machine / PPM).
stdlib בלבד, אפס תלויות.

## הרצה
python3 tools/pal_lint.py FILE.html [--site csb|marom|plrom] [--type blog|brandhub|product] [--json]

exit 0 = ירוק, מותר להגיש. exit 1 = ERROR, אסור להגיש.
site/type מזוהים אוטומטית אם לא סופקו.

## מה נבדק (ERROR חוסם)
קו מפריד ארוך | var()/custom-props/comments/rem ב-CSS | backslash ב-HTML גלוי |
percent-encoding באותיות גדולות | URL מקודד ב-brand-hub widget | קישורים אסורים per-site |
product-category בפלרום | sitemap XML | jeepolog | טרמינולוגיה אסורה | מומחה שגוי per-site |
טלפון אסור | Beko במרום / אלקטרה בפלרום | "שירות רשמי" למכונות קפה דלונגי |
JSON-LD לא נפרס | Product בלי offers | priceCurrency לא ILS | NAP שגוי ב-LocalBusiness |
video-container ריק / placeholder | קידוד שבור.

WARN (שיקול דעת): en dash, מונחים תלויי הקשר, קישור cross-site, אורך משפטים Yoast, תווי BiDi.

## עדכון כללים
מקור האמת לכללים = הזיכרון המובנה של Claude. כל כלל חדש/משתנה מתעדכן
בשני מקומות באותה פעולה: זיכרון + הטבלאות בראש pal_lint.py, ואז מריצים selftest:
python3 tools/tests/selftest.py

## אינטגרציה
צעד חובה בכל SKILL לפני הגשה. Claude מריץ אוטונומית בכל session
(clone של pal-state ממילא קורה בפתיחת משימה). דוח ירוק מצורף לכל הגשה.
