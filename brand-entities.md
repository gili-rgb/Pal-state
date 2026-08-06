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
| Neff | נף | `Q326933` | `https://en.wikipedia.org/wiki/Neff_GmbH` |
| Magimix | מג'ימיקס | `Q3276973` | `https://en.wikipedia.org/wiki/Magimix` |
| KitchenAid | קיטשן אייד | `Q1743850` | `https://en.wikipedia.org/wiki/KitchenAid` |
| Bauknecht | באוקנכט | `Q467116` | `https://en.wikipedia.org/wiki/Bauknecht_(company)` |
| Blomberg | בלומברג | `Q884951` | `https://en.wikipedia.org/wiki/Blomberg_(company)` |
| Gaggenau | גגנאו | — | `https://en.wikipedia.org/wiki/Gaggenau_Hausger%C3%A4te` |
| De'Longhi | דלונגי | — | `https://en.wikipedia.org/wiki/De%27_Longhi` |
| Haier | האייר | — | `https://en.wikipedia.org/wiki/Haier` |
| Zanussi | זנוסי | — | `https://en.wikipedia.org/wiki/Zanussi` |
| Tefal | טפאל | — | `https://en.wikipedia.org/wiki/Tefal` |
| Moulinex | מולינקס | — | `https://en.wikipedia.org/wiki/Moulinex` |
| Breville | ברוויל | — | `https://en.wikipedia.org/wiki/Breville_Group` |

**בוש וסימנס (מוצרי חשמל):** אין ישות מותג נפרדת. `sameAs` מפנה ל-BSH (`Q614920`) כיצרן. **אסור לקשר ל-`Robert Bosch GmbH` או ל-`Siemens AG`.**

**Neff וקונסטרוקטה חולקים QID** (`Q326933`, Constructa-Neff Vertriebs-GmbH) כי הם אותה חברה. זה נכון עובדתית. ה-URI של ויקיפדיה שונה לכל אחד.

**Breville — סייג:** בבריטניה ובאירופה המותג "Breville" שייך ל-Newell Brands, ישות אחרת לגמרי, ושם החברה האוסטרלית משווקת כ-Sage. הישות הרשומה כאן היא Breville Group האוסטרלית, שהיא הרלוונטית לישראל.

---

## ממתין — ושתי מלכודות שזוהו

**ליבהר.** `Liebherr Group` הוא תאגיד מנופים וציוד כבד. מוצרי הקירור הם `Liebherr-Hausgeräte`. **אותה מלכודת בדיוק כמו בוש.** דורש אימות פרטני לפני שנכנס.

**פיליפס.** `Koninklijke Philips` הוא היום תאגיד טכנולוגיה רפואית. **מחלקת מוצרי החשמל הביתיים נמכרה ב-2021 והפכה ל-Versuni**, שממשיכה להשתמש בשם פיליפס ברישיון. הישות הנכונה למאמר על מכשיר ביתי אינה ברורה, ודורשת הכרעה.

**סאוטר.** קיימות Sauter שוויצרית לבקרת בניינים, Sauter צרפתית לחימום, ומשפחות ומקומות. **סביר שיישאר בחוץ לצמיתות.**

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
