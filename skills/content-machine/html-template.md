# תבנית HTML v7.11 — מוכנה להטמעה בווידג'ט HTML של Elementor

> **v7.9 (2026-08-03):** **ישות `Product` הוסרה מה-@graph.** התבנית עדיין הציגה "6 entities, או 7 עם כרטיס מוצר" וכללה בלוק Product מלא — סתירה מול SKILL v7.15+ שקובע 6 ישויות תמיד, ומול pal-lint שאוכף `SCHEMA_PRODUCT_BLOG` כ-ERROR. דריפט בן שלוש גרסאות שנתפס באודיט v7.18. `mentions` מצביע על Brand בלבד.

> **v7.8 (2026-07-23):** תיקון WCAG_HEADING_SKIP — ה-TOC (מיד אחרי H1, לפני ה-H2 הראשון) עבר מ-`<h3>תוכן עניינים</h3>` ל-`<p class="toc-title">`. תבנית קודמת יצרה דילוג היררכיה (h1→h3) שנתפס כ-ERROR ב-pal-lint. לוגו/עיצוב זהים, רק תגית שונה.

## כללי ברזל

- **ללא** `<html>`, `<body>`, `<head>` — תגיות סמנטיות בלבד
- הקוד מיועד לווידג'ט HTML בתוך אלמנטור
- **אפס JS** — CSS בלבד
- **system fonts בלבד** — אפס טעינת פונטים חיצוניים (`font-family: inherit`, בלי `@import` של Google Fonts בתוך הווידג'ט)
- **dir="rtl"** ו-**lang="he"** על article root
- **CSS עם צבעי hex קשיחים (חובה, v7.7 — תיקון Elementor קריטי):** ה-CSS חייב להיות **hex קשיח בלבד**. **אסור `var()` ואסור בלוק tokens `.blog-article{--bh-*}`** — הם מפילים את שמירת הווידג'ט ב-Elementor ("משהו לא תקין"/"החיבור אבד"). הוכח בניסוי צלב (יוני 2026): אותו עמוד עם בלוק tokens נכשל, עם hex קשיח נשמר ופורסם. ה-CSS בתבנית מקודד לערכי **CSB** (כתום). **לאתר אחר — החלף את ערכי הצבע לפי טבלת הצבעים למטה, לפי תפקיד** (לא find-replace עיוור: חלק מצבעי CSB חוזרים בכמה תפקידים שמתפצלים ב-Marom/Plrom, למשל `#B55304` = action+badge+link ב-CSB אך שלושה צבעים שונים ב-Marom). מבנה ה-CSS זהה בכל האתרים, רק ערכי ה-hex משתנים. **אסור גם הערות `/* */` בתוך ה-`<style>`** — שמור על CSS נקי כמו הקבצים שמתפרסמים תקין.

## חוסמי Elementor (אסורים בהחלט — כל אחד מפיל שמירה עם "החיבור אבד")

נבדקים אוטומטית בשלב 13 (VALIDATE). אל תכניס אף אחד מהם:

1. `unicode-bidi` בכל וריאציה (isolate/embed/plaintext) — בכל מקום. ערך טכני LTR (מק"ט, קוד תקלה, דגם) = טקסט רגיל בתוך `<td>`/`<span>`, בלי class ובלי style מיוחד.
2. `<svg>` inline — אסור. לאייקון: תו HTML entity (כוכב `&#9733;`, טלפון `&#9742;`).
3. `data-ga-event`, `target="_blank"` — אסורים כ-attributes.
4. תווי רוח: U+2011 (non-breaking hyphen), U+00AD (soft hyphen), U+200B (zero-width). מקף = `-` רגיל בלבד.
5. CSS מאוזן (`{` = `}`), בלי `@media` מקונן. אחרי כל עריכת CSS — ספור סוגריים.
6. קישורי מוצר: אם ה-permalink מכיל רצף ארוך של `%XX` (10+) — השתמש ב-**URL עברית raw לא מקודד** (`/product/שם-בעברית/`). רצף percent-encoding ארוך עלול להיחסם ב-WAF. וורדפרס מקבל את הצורה העברית. אחרת, permalink verbatim מ-MCP כפי שהוא.
7. **בלוק tokens `.blog-article{--bh-*}` ו-`var(--bh-*)`** — אסורים בהחלט. הוכח כגורם החד-משמעי לכשל השמירה בבלוגים (יוני 2026). כל הצבעים = **hex קשיח**. ראה טבלת צבעים לפי אתר למטה.
8. **יחידות `rem` ב-CSS** — אסורות, px מפורש בלבד (נאכף ב-pal-lint, CSS_REM). גדלים ומרווחים נכתבים ב-px.
8. **הערות CSS `/* */` בתוך `<style>`** — הימנע. הקבצים שמתפרסמים תקין נקיים מהן.

## כללי נגישות (WCAG 2.2 AA) - חובה

- כל `<img>` עם `alt` תיאורי וקצר. תמונה דקורטיבית בלבד: `alt=""`
- כל `<iframe>` עם `title` תיאורי (לא "וידאו" גנרי)
- טקסט סמנטי בקופסאות (אזהרת בטיחות / המלצת מומחה / תובנה מרכזית) חי ב-HTML אמיתי (`.warning-box-title` וכו'), **לא** ב-`::before content`. קוראי מסך לא מקריאים pseudo-element content באופן אמין. ה-emoji בלבד נשאר ב-`::before` כדקורציה
- כל טבלה עטופה ב-`<div class="table-wrap">`. כל `<th>` עם `scope="col"` או `scope="row"`
- היררכיית כותרות רציפה: H1 אחד, ואז H2/H3 בלי דילוג
- קישורים בגוף הטקסט נשארים עם קו תחתון (לא צבע בלבד)
- אל תסיר את מצב ה-focus (outline). הוא נדרש לניווט במקלדת
- ניגודיות טקסט מול רקע: לפחות 4.5:1 (טקסט רגיל), 3:1 (טקסט גדול)

---

## טבלת צבעים לפי אתר (להחלפה לפי תפקיד)

ה-CSS למטה מקודד לערכי **CSB**. לבניית בלוג ל-Marom/Plrom, החלף כל ערך לפי התפקיד שלו בטבלה. **חשוב:** החלף לפי תפקיד, לא לפי hex עיוור — `#B55304` ב-CSB משמש 3 תפקידים שמתפצלים ב-Marom (action=אדום, badge=navy, link=אדום).

| תפקיד | היכן ב-CSS | CSB (כתום) | Marom (navy+אדום) | Plrom (כתום Electra) |
|---|---|---|---|---|
| action | cta-primary bg, author-avatar bg, גבול pref | `#B55304` | `#D01F26` | `#B85700` |
| action-hover | cta-primary:hover | `#974503` | `#B81A21` | `#913F00` |
| structure | גבולות h1/h2/direct-answer, toc badge accent | `#FB7305` | `#140C3C` | `#F07800` |
| badge | toc/step מספור bg | `#B55304` | `#140C3C` | `#B85700` |
| link | קישורים, cta, pref | `#B55304` | `#B81A21` | `#B85700` |
| link-hover | קישור:hover | `#974503` | `#9C151B` | `#913F00` |
| ink | כותרות/טקסט כהה | `#16232e` | `#140C3C` | `#181818` |
| text | טקסט גוף | `#34414a` | `#2E2D38` | `#2B2B2B` |
| text-2 | טקסט משני | `#4b5860` | `#44434F` | `#4A4A4A` |
| muted | eyebrow, עמום | `#687680` | `#5E5C6B` | `#6E6E6E` |
| tint | direct-answer bg | `#FFF1E6` | `#F4F3FC` | `#FFF4E8` |
| surface | toc/sources/author bg | `#f6f8f9` | `#F8F8FB` | `#F8F8F8` |
| surface-2 | th bg | `#eceff1` | `#F1F0F4` | `#F3F3F3` |
| border | גבולות טבלה/כרטיס | `#dde3e7` | `#E4E3E9` | `#E3E3E3` |
| border-strong | inline-faq dashed | `#c4ccd2` | `#CBCAD2` | `#C9C9C9` |
| dark | cta-box bg | `#16232e` | `#140C3C` | `#181818` |
| dark-text | cta-box טקסט | `#c4ccd2` | `#CFC9F0` | `#C9C9C9` |
| success | key-takeaway accent | `#1f9d57` | `#1F9D57` | `#1E9E57` |
| success-text | key-takeaway/stock טקסט | `#167a43` | `#197E46` | `#0F6B38` |
| success-tint | key-takeaway/stock bg | `#dff3e4` | `#E3F6EC` | `#E9F7EF` |
| danger | warning-box accent | `#d6361f` | `#D01F26` | `#D83A36` |
| danger-text | warning-box טקסט | `#ad2716` | `#D01F26` | `#B82C29` |
| danger-tint | warning-box bg | `#fbe3df` | `#FCE4E5` | `#FDECEC` |
| warning | expert-tip accent | `#ef9f0a` | `#E08A00` | `#E6A100` |
| warning-text | expert-tip טקסט | `#16232e` | `#140C3C` | `#181818` |
| warning-tint | expert-tip bg | `#fdf0d6` | `#FBEFD6` | `#FFF7E6` |
| cite | citation accent | `#1f72c4` | `#2A6FDB` | `#2A6DB5` |
| cite-tint | citation bg | `#e0edfb` | `#E4EEFB` | `#EAF2FB` |

מקור אמת לערכים: `../brand-hub-machine/tokens-[site].css` (Design System, WCAG 2.2 AA).

---

## CSS בסיסי

```html
<style>

.blog-article, .blog-article * { box-sizing: border-box !important; max-width: 100% !important; }
.blog-article { font-family: inherit; font-size: 17px; line-height: 1.75; color: inherit; direction: rtl; }
.blog-article a { color: #B55304; text-decoration: underline; text-underline-offset: 2px; transition: color 0.2s; }
.blog-article a:hover { color: #974503; }
.blog-article a:focus-visible, .blog-article button:focus-visible { outline: 3px solid #B55304; outline-offset: 2px; border-radius: 2px; }
.blog-article h1 { font-size: 28px; text-align: right; border-bottom: 2px solid #FB7305; padding-bottom: 15px; margin-bottom: 25px; }
.blog-article h2 { font-size: 22px; border-right: 4px solid #FB7305; padding-right: 12px; margin-top: 2em; }
.blog-article h3 { font-size: 19px; margin-top: 1.5em; }
.blog-article table { width: 100%; border-collapse: collapse; margin: 1.5em 0; }
.table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 1.5em 0; }
.table-wrap table { margin: 0; }
.blog-article th { background: #eceff1; padding: 10px; text-align: right; border: 1px solid #dde3e7; }
.blog-article td { padding: 10px; border: 1px solid #dde3e7; vertical-align: top; }
.blog-article img { max-width: 100%; height: auto; }

.last-updated { text-align: right; color: #4b5860; font-size: 14px; margin-bottom: 20px; }

.direct-answer { background: #FFF1E6; border-right: 4px solid #FB7305; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }

.toc { background: #f6f8f9; border: 1px solid #dde3e7; border-radius: 8px; padding: 20px; margin: 25px 0; }
.toc-title { margin: 0 0 10px; font-size: 18px; font-weight: 700; color: inherit; }
.toc ol { list-style: none; padding: 0; counter-reset: toc-counter; }
.toc li { counter-increment: toc-counter; margin: 8px 0; }
.toc li::before { content: counter(toc-counter); background: #B55304; color: #fff; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 13px; margin-left: 10px; }
.toc a { color: #34414a; font-weight: 500; text-decoration: none; }
.toc a:hover, .toc a:focus-visible { color: #B55304; text-decoration: underline; }

.expert-tip { background: #fdf0d6; border: 1px solid #ef9f0a; border-radius: 8px; padding: 15px 20px; margin: 20px 0; }
.expert-tip-title { font-weight: 700; margin-bottom: 8px; color: #16232e; }
.expert-tip-title::before { content: "💡 "; }

.product-rec { margin: 25px 0 8px; }
.product-card { display: flex; gap: 15px; align-items: stretch; background: #fff; border: 1px solid #dde3e7; border-radius: 12px; padding: 14px; margin: 8px 0 25px; text-decoration: none !important; transition: border-color 0.2s, box-shadow 0.2s; }
.product-card:hover { border-color: #FB7305; box-shadow: 0 2px 12px rgba(0,0,0,0.10); border-bottom: 1px solid #FB7305 !important; }
.product-card:focus-visible { outline: 3px solid #B55304; outline-offset: 2px; }
.product-card-img { flex: 0 0 110px; width: 110px; height: 110px; border-radius: 8px; object-fit: contain; background: #f6f8f9; border: 1px solid #dde3e7; }
.product-card-body { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 6px; }
.product-card-eyebrow { font-size: 13px; color: #687680; }
.product-card-title { font-size: 17px; font-weight: 700; color: #16232e; line-height: 1.45; }
.product-card-meta { display: flex; align-items: center; gap: 12px; margin-top: 4px; flex-wrap: wrap; }
.product-card-price { font-size: 18px; font-weight: 700; color: #16232e; }
.product-card-stock { font-size: 13px; font-weight: 600; color: #167a43; background: #dff3e4; padding: 2px 10px; border-radius: 6px; }
.product-card-cta { margin-inline-start: auto; font-size: 14px; font-weight: 700; color: #B55304; }

.warning-box { background: #fbe3df; border: 1px solid #d6361f; border-radius: 8px; padding: 15px 20px; margin: 20px 0; }
.warning-box-title { font-weight: 700; margin-bottom: 8px; color: #ad2716; }
.warning-box-title::before { content: "⚠️ "; }

.step-guide { margin: 20px 0; }
.step { display: flex; gap: 15px; margin: 15px 0; align-items: flex-start; }
.step-number { background: #B55304; color: #fff; min-width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.step-content { flex: 1; }

.citation { background: #e0edfb; border-right: 3px solid #1f72c4; padding: 12px 18px; margin: 15px 0; border-radius: 0 6px 6px 0; font-size: 15px; }
.citation cite { display: block; color: #4b5860; font-size: 13px; margin-top: 5px; font-style: normal; }

.inline-faq { background: #f6f8f9; border: 1px dashed #c4ccd2; border-radius: 6px; padding: 12px 18px; margin: 15px 0; }
.inline-faq strong { color: #34414a; }

.key-takeaway { background: #dff3e4; border-right: 3px solid #1f9d57; padding: 12px 18px; margin: 15px 0; border-radius: 0 6px 6px 0; }
.key-takeaway-title { font-weight: 700; margin-bottom: 5px; color: #167a43; }
.key-takeaway-title::before { content: "✅ "; }

.cta-box { background: #16232e; color: #fff; border-radius: 12px; padding: 30px; margin: 30px 0; text-align: center; }
.cta-box h2 { color: #fff; border: none; text-align: center; padding: 0; }
.cta-box p { color: #c4ccd2; }
.cta-buttons { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; margin-top: 15px; }
.cta-primary { background: #B55304; color: #fff !important; padding: 12px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; border: none; display: inline-block; }
.cta-ai { background: #fff; color: #140C3C !important; padding: 12px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; border: 2px solid #fff; display: inline-block; }
.call-strip { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; background: #F4F3FC; border-right: 4px solid #140C3C; border-radius: 0 8px 8px 0; padding: 14px 18px; margin: 20px 0; }
.call-strip-txt { flex: 1; min-width: 170px; font-size: 15px; }
.call-strip a.tel { display: inline-flex; align-items: center; gap: 7px; background: #140C3C; color: #fff !important; font-weight: 700; font-size: 16px; padding: 10px 20px; border-radius: 8px; text-decoration: none !important; white-space: nowrap; border-bottom: none !important; }
.call-strip a.tel:hover { background: #2E2D38; color: #fff !important; }
.call-strip a.tel:focus-visible { outline: 3px solid #D01F26; outline-offset: 2px; }
.cta-primary:hover { background: #974503; color: #fff !important; border-bottom: none !important; }
.cta-secondary { background: transparent; color: #fff !important; padding: 12px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; border: 2px solid #fff; display: inline-block; }
.cta-secondary:hover { background: rgba(255,255,255,0.1); color: #fff !important; border-bottom: none !important; }
.cta-box a:focus-visible { outline: 3px solid #fff; outline-offset: 3px; }

.sources-list { background: #f6f8f9; border: 1px solid #dde3e7; border-radius: 8px; padding: 15px 20px; margin: 25px 0; font-size: 14px; }
.sources-list h3 { margin-top: 0; font-size: 16px; color: #4b5860; }
.sources-list ul { padding-right: 20px; }
.sources-list li { margin: 5px 0; color: #4b5860; }

.author-bio { display: flex; gap: 15px; align-items: center; background: #f6f8f9; border-radius: 8px; padding: 20px; margin-top: 30px; }
.author-avatar { width: 50px; height: 50px; background: #B55304; color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; flex-shrink: 0; }
.author-bio p { margin: 0; font-size: 14px; color: #4b5860; }
.author-bio strong { color: #16232e; font-size: 16px; }

.video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 25px 0; border-radius: 8px; }
.video-container iframe { position: absolute; top: 0; right: 0; width: 100%; height: 100%; border: none; }

.bh-pref-mini { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 14px; color: #4b5860; margin: 20px 0 0; padding-top: 14px; border-top: 1px solid #dde3e7; }
.bh-pref-mini .star { color: #ef9f0a; flex-shrink: 0; font-size: 18px; }
.bh-pref-mini-txt { flex: 1; min-width: 160px; }
.bh-pref-mini a.add { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; font-size: 14px; color: #B55304 !important; text-decoration: none !important; border: 1.5px solid #B55304; border-radius: 7px; padding: 7px 14px; white-space: nowrap; transition: background 0.2s, color 0.2s; border-bottom: 1.5px solid #B55304 !important; }
.bh-pref-mini a.add:hover { background: #B55304; color: #fff !important; }
.bh-pref-mini a.add:focus-visible { outline: 3px solid #B55304; outline-offset: 2px; }

@media (max-width: 600px) {
  .blog-article h1 { font-size: 24px; }
  .blog-article h2 { font-size: 20px; }
  .blog-article table { font-size: 14px; }
  .blog-article th, .blog-article td { padding: 6px 8px; }
  .cta-box { padding: 20px 15px; }
  .cta-buttons { flex-direction: column; align-items: stretch; }
  .cta-primary, .cta-secondary { width: 100%; text-align: center; }
  .author-bio { flex-direction: column; text-align: center; }
  .step { flex-direction: column; }
  .direct-answer { padding: 12px 15px; }
  .toc { padding: 15px; }
  .product-card-img { flex-basis: 90px; width: 90px; height: 90px; }
  .product-card-title { font-size: 15px; }
  .product-card-meta { gap: 8px; }
  .bh-pref-mini a.add { width: 100%; justify-content: center; }
}

@media (prefers-reduced-motion: reduce) {
  .blog-article *, .blog-article *::before, .blog-article *::after { transition: none !important; animation: none !important; }
}
</style>
```

---

## HTML שלד

```html
<!-- Schema JSON-LD — ראה שלב 12 ב-SKILL.md -->
<script type="application/ld+json">
{ "@context": "https://schema.org", "@graph": [ ... ] }
</script>

<article class="blog-article" dir="rtl" lang="he">

  <h1>[H1 משלב 5]</h1>
  <p class="last-updated">עודכן: [חודש שנה]</p>

  <div class="direct-answer">
    <p><strong>בקצרה:</strong> [תשובה ישירה ב-2-3 משפטים]</p>
  </div>

  <nav class="toc">
    <p class="toc-title">תוכן עניינים</p>
    <ol>
      <li><a href="#section-1">[כותרת H2]</a></li>
      <li><a href="#section-2">[כותרת H2]</a></li>
      <!-- ... -->
    </ol>
  </nav>

  <!-- === סקשנים === -->
  <h2 id="section-1">[שאלה Answer-First]</h2>
  <p>[תשובה ישירה במשפט ראשון]. [הרחבה...]</p>

  <!-- === Hero Product — כרטיס מוצר אחרי הסקשן שמבסס את הצורך === -->
  <!-- מיקום: מיד אחרי שהמאמר ביסס את הבעיה/סימפטום והציב את החלק כפתרון (commerce קונטקסטואלי) -->
  <!-- כל הערכים מ-get_product_by_sku, verbatim: permalink, images[0], מחיר. alt = שם המוצר -->
  <!-- href: permalink מ-MCP verbatim. אם יש רצף %XX ארוך (10+) — URL עברית raw לא מקודד -->
  <p class="product-rec"><strong>[שם הטכנאי של האתר] ממליץ:</strong> [משפט קצר שמקשר את הצורך לחלק]. הפתרון הוא [שם המוצר].</p>
  <a class="product-card" href="[permalink מ-MCP — verbatim, lowercase]">
    <img class="product-card-img" src="[images[0] מ-MCP]" alt="[שם המוצר המלא]" loading="lazy">
    <span class="product-card-body">
      <span class="product-card-eyebrow">[domain] · חלק מקורי</span>
      <span class="product-card-title">[שם המוצר]</span>
      <span class="product-card-meta">
        <span class="product-card-price">[מחיר] ₪</span>
        <span class="product-card-stock">במלאי</span>
        <span class="product-card-cta">לפרטים והזמנה ←</span>
      </span>
    </span>
  </a>

  <div class="citation">
    <p>[ניסוח עם מקור]<cite>מקור: [שם המקור]</cite></p>
  </div>

  <div class="inline-faq">
    <p><strong>שאלה נפוצה:</strong> [שאלת המשך]</p>
    <p>[תשובה קצרה]</p>
  </div>

  <div class="expert-tip">
    <p class="expert-tip-title">המלצת מומחה</p>
    <p>[טיפ מהטכנאי — אם רלוונטי]</p>
  </div>

  <div class="warning-box">
    <p class="warning-box-title">אזהרת בטיחות</p>
    <p>[אזהרת בטיחות — אם רלוונטי]</p>
  </div>

  <div class="step-guide">
    <div class="step">
      <div class="step-number">1</div>
      <div class="step-content"><p>[הוראה]</p></div>
    </div>
    <div class="step">
      <div class="step-number">2</div>
      <div class="step-content"><p>[הוראה]</p></div>
    </div>
  </div>

  <div class="key-takeaway">
    <p class="key-takeaway-title">תובנה מרכזית</p>
    <p>[תובנה מרכזית לסיכום הסקשן]</p>
  </div>

  <!-- === טבלה: תמיד עטופה ב-table-wrap, כל th עם scope === -->
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th scope="col">[כותרת עמודה]</th>
          <th scope="col">[כותרת עמודה]</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">[כותרת שורה]</th>
          <td>[ערך]</td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- === Cluster Links === -->
  <h2>מאמרים קשורים</h2>
  <ul>
    <li><a href="[pillar URL]">[שם מאמר pillar]</a></li>
    <li><a href="[sibling URL]">[שם מאמר אח]</a></li>
  </ul>

  <!-- === YouTube === -->
  <div class="video-container">
    <iframe src="https://www.youtube.com/embed/[VIDEO_ID]" allowfullscreen loading="lazy" title="[תיאור]"></iframe>
  </div>

  <!-- === FAQ === -->
  <h2 id="faq">שאלות נפוצות</h2>

  <h3>[שאלה Hyper Specific — 2+ עוגנים]</h3>
  <p>[תשובה]</p>

  <h3>[שאלה עם כוונה מקומית]</h3>
  <p>[תשובה]</p>

  <!-- === CTA === -->
  <div class="cta-box">
    <h2>[כותרת CTA]</h2>
    <p>[טקסט CTA]</p>
    <div class="cta-buttons">
      <a href="[myarea link]" class="cta-primary">[כפתור ראשי]</a>
      <a href="[product/category link]" class="cta-secondary">[כפתור משני]</a>
    </div>
  </div>

  <!-- === מקורות === -->
  <div class="sources-list">
    <h3>מקורות</h3>
    <ul>
      <li>[מקור 1]</li>
      <li>[מקור 2]</li>
    </ul>
  </div>

  <!-- === Author Bio (E-E-A-T מבוסס הוכחה — נשען על סעיף "מומחה" בקובץ הפרויקט) === -->
  <!-- הוכחה, לא תיאור (Tom Winter, Campixx 2026). מבנה: עוגן סמכות מאומת + הוכחת ניסיון + התמחות. -->
  <!-- אל תמציא שנים/הסמכות. אם שדה הוכחת הניסיון בקובץ הפרויקט עדיין [placeholder] — השמט אותו, אל תמלא באוויר. -->
  <div class="author-bio">
    <div class="author-avatar">[ראשי תיבות]</div>
    <div>
      <strong>[שם המומחה]</strong>
      <p>[תפקיד] ב[חברה], [עוגן סמכות מאומת]. [הוכחת ניסיון]. מתמחה ב[התמחות].</p>
    </div>
  </div>

  <!-- === מקור מועדף בגוגל — בלוק אחרון בזרימה, אחרי author-bio. אל תמקם לפני cta-box === -->
  <!-- [שם-אתר]: CSB / שירות מרום / פלרום (מקובץ הפרויקט). [DOMAIN]: csb.co.il / marom-serv.co.il / plrom.co.il -->
  <div class="bh-pref-mini">
    <span class="star" aria-hidden="true">&#9733;</span>
    <span class="bh-pref-mini-txt">מצאתם את המידע מועיל? בחרו ב[שם-אתר] כמקור מועדף בגוגל.</span>
    <a class="add" href="https://www.google.com/preferences/source?q=[DOMAIN]" rel="noopener" aria-label="הוספת [שם-אתר] כמקור מועדף בגוגל">הוספה כמקור מועדף</a>
  </div>

</article>
```

---

### רצועת חיוג ותיאום (v7.11) — חובה כשהמאמר מזכיר תיאום או יצירת קשר

72-76% מהתנועה מובייל. מספר שאינו בר-לחיצה מאבד שיחות, ולכן `href="tel:"` חובה.
**סדר ההצגה: נציגת ה-AI ראשונה, המוקד חלופה** — המטרה להסיט עומס מהמוקד האנושי.

```html
<div class="call-strip">
  <span class="call-strip-txt">
    לתיאום התקנה בלי המתנה לנציג, [שם הנציגה] זמינה 24/7 כל השנה, בשיחה ובצ'אט.
  </span>
  <a class="tel" href="tel:[טלפון מ-brief.ai_agent]">&#9742; [טלפון הנציגה]</a>
</div>
```

בתוך `.cta-box`, כשיש נציגה, הכפתור הראשון מוביל אליה:

```html
<a href="[brief.ai_agent.url]" class="cta-primary">תיאום מיידי עם [שם הנציגה]</a>
<a href="[עמוד יצירת קשר]" class="cta-ai">למוקד השירות</a>
```

**לפלרום אין נציגת AI** — `brief.ai_agent` יחזיר `null`, ואז מוצג המוקד בלבד. הצבעים כאן הם של מרום; החלף לפי טבלת הצבעים של האתר.

## Schema @graph — שלד (6 entities תמיד)

> **אין ישות `Product` בבלוג. לעולם.** גם כשיש כרטיס מוצר. גוגל דורש בכל Product לפחות אחד מ-`offers`/`review`/`aggregateRating`, ומחיר סטטי בבלוג יוצר mismatch — לכן דף המוצר הוא היחיד שמחזיק Product עם offer חי. הכרטיס הוויזואלי (`.product-card`) הוא **תוכן בלבד**, והמחיר בתוכו אינו schema. `mentions` מצביע על Brand בלבד. pal-lint אוכף (`SCHEMA_PRODUCT_BLOG`, ERROR).
>
> **Speakable (v7.4):** ישות ה-Article כוללת `speakable` שמצביע על `.direct-answer` — בלוק ה"בקצרה" ה-extractable. זה ה-selector שעוזרי קול ומנועי AI מצביעים אליו לציטוט.

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Article",
      "@id": "https://[domain]/[slug]/#content-article",
      "headline": "[H1]",
      "description": "[Meta Description]",
      "datePublished": "[YYYY-MM-DD]",
      "dateModified": "[YYYY-MM-DD]",
      "author": { "@id": "https://[domain]/#content-author" },
      "publisher": { "@id": "https://[domain]/#content-organization" },
      "mainEntityOfPage": "https://[domain]/[slug]/",
      "speakable": {
        "@type": "SpeakableSpecification",
        "cssSelector": [".direct-answer"]
      },
      "about": [
        { "@type": "Thing", "name": "[נושא 1]" },
        { "@type": "Thing", "name": "[נושא 2]" }
      ],
      "mentions": [
        {
          "@type": "Brand",
          "name": "[מותג]",
          "sameAs": ["[URI מ-brand-entities.md — ויקידאטה + ויקיפדיה]"]
        }
      ]
    },
    {
      "@type": "Person",
      "@id": "https://[domain]/#content-author",
      "name": "[שם המומחה מקובץ הפרויקט]",
      "jobTitle": "[תפקיד מקובץ הפרויקט]",
      "worksFor": { "@id": "https://[domain]/#content-organization" },
      "knowsAbout": ["[התמחות 1]", "[התמחות 2]", "[התמחות 3]"],
      "description": "[עוגן סמכות מאומת + הוכחת ניסיון — לא ביו גנרי. מסעיף 'מומחה' בקובץ הפרויקט]",
      "sameAs": ["[הוכחת author חיצונית מסעיף 'מומחה': עמוד כותב/LinkedIn. אם אין הוכחה חיצונית — השמט את כל שדה sameAs]"]
    },
    {
      "@type": "Organization",
      "@id": "https://[domain]/#content-organization",
      "name": "[שם חברה]",
      "alternateName": "[שם חלופי]",
      "url": "https://[domain]",
      "telephone": "[טלפון]",
      "description": "[מהנרטיב הקנוני: משפטים 1-2, סעיף 'נרטיב מותג' בקובץ הפרויקט]",
      "sameAs": ["[YouTube URL]", "[About page URL]"]
    },
    {
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "[שאלה — זהה לטקסט]",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "[תשובה — זהה לטקסט]"
          }
        }
      ]
    },
    {
      "@type": "LocalBusiness",
      "@id": "https://[domain]/#content-localbusiness",
      "name": "[שם]",
      "telephone": "[טלפון]",
      "url": "https://[domain]",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "[רחוב ומספר מקובץ הפרויקט]",
        "addressLocality": "[עיר: לוד ל-CSB/פלרום, חולון למרום]",
        "postalCode": "[מיקוד]",
        "addressCountry": "IL"
      },
      "areaServed": {
        "@type": "Place",
        "name": "ישראל"
      },
      "parentOrganization": { "@id": "https://[domain]/#content-organization" }
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://[domain]/[slug]/#content-breadcrumb",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "דף הבית", "item": "https://[domain]/" },
        { "@type": "ListItem", "position": 2, "name": "בלוג", "item": "https://[domain]/blog/" },
        { "@type": "ListItem", "position": 3, "name": "[כותרת]" }
      ]
    }
  ]

}
```
