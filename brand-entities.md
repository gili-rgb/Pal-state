# רישום ישויות מותג — Entity Disambiguation

**מטרה:** לקשר מותג במאמר לגרף הידע העולמי דרך `sameAs`, כדי שמנוע AI יזהה את הישות בוודאות ולא ינחש.

**כלל ברזל:** שורה נכנסת לכאן **רק אחרי אימות מול המקור**. מותג שלא אומת אינו ברישום, ואז אין `sameAs` — וזה תקין. QID שגוי גרוע מ-QID חסר, כי הוא מקשר אותנו לישות הלא נכונה.

**מלכודות שנתפסו באימות (2026-08-06):**
- `Q48757454` הוא "Sharp — יצרן רובי אוויר לשעבר ביפן". הנכון הוא `Q53227`.
- ל**בוש ולסימנס כמותגי מוצרי חשמל אין ישות נפרדת**. `Robert Bosch GmbH` ו-`Siemens AG` הם תאגידים בתחומי בלמים, אנרגיה ורפואה. הישות הנכונה למוצרי חשמל היא `BSH Hausgeräte`.
- Constructa מופיעה כשני ערכים: `Constructa-Neff` (החברה) ו-`Constructa (company)` (המותג).

**מדיניות `sameAs`:** ויקיפדיה תמיד (קריא ובר-אימות בעין), ויקידאטה כשאומת, ואתר המותג הרשמי כעוגן שלישי.

---

## מאומת

| מותג | עברית | Wikidata | Wikipedia |
|------|-------|----------|-----------|
| Sharp | שארפ | `Q53227` | `https://en.wikipedia.org/wiki/Sharp_Corporation` |
| Miele | מילה | `Q695230` | `https://en.wikipedia.org/wiki/Miele` |
| BSH | — | `Q614920` | `https://en.wikipedia.org/wiki/BSH_Hausger%C3%A4te` |
| Constructa | קונסטרוקטה | `Q326933` | `https://en.wikipedia.org/wiki/Constructa-Neff` |
| Magimix | מג'ימיקס | `Q3276973` | `https://en.wikipedia.org/wiki/Magimix` |
| Gaggenau | גגנאו | — | `https://en.wikipedia.org/wiki/Gaggenau_Hausger%C3%A4te` |
| De'Longhi | דלונגי | — | `https://en.wikipedia.org/wiki/De%27_Longhi` |
| Haier | האייר | — | `https://en.wikipedia.org/wiki/Haier` |
| Zanussi | זנוסי | — | `https://en.wikipedia.org/wiki/Zanussi` |

**בוש וסימנס (מוצרי חשמל):** אין ישות מותג נפרדת. `sameAs` מפנה ל-BSH (`Q614920`) כיצרן, ולאתר המותג הרשמי. **אסור לקשר ל-`Robert Bosch GmbH` או ל-`Siemens AG`.**

---

## ממתין לאימות

בלומברג, קיטשן אייד, ברוויל, טפאל, מולינקס, פיליפס, ליבהר, נף, באוקנכט.

**סאוטר** — סביר שיישאר בחוץ. קיימות Sauter שוויצרית לבקרת בניינים, Sauter צרפתית לחימום, ומשפחות ומקומות באותו שם. בלי הכרעה חד-משמעית, אין קישור.

---

## שימוש בסכמה

```json
"mentions": [
  {
    "@type": "Brand",
    "name": "שארפ",
    "sameAs": [
      "https://www.wikidata.org/wiki/Q53227",
      "https://en.wikipedia.org/wiki/Sharp_Corporation"
    ]
  }
]
```

נאכף ב-`BRAND_SAMEAS_MISSING` (pal-lint): נורה רק כשהמותג ברישום ו-`sameAs` חסר.
