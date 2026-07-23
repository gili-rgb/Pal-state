#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""בדיקה עצמית של pal-lint: מאמת שכל כלל נתפס ושתוכן תקין עובר ירוק."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pal_lint import run, detect_type

FIX = Path(__file__).parent / "fixtures"
FAILED = []

def expect(name, path, site, must_have_errors=(), must_pass=False, doc_type=None,
           expect_type=None):
    rep, s, d = run(path, site, doc_type)
    got = {e["rule"] for e in rep.errors}
    if expect_type and d != expect_type:
        FAILED.append(f"{name}: detect_type החזיר {d}, מצופה {expect_type}")
    if must_pass:
        if rep.errors:
            FAILED.append(f"{name}: אמור לעבור ירוק אבל יש {sorted(got)}")
        else:
            print(f"✅ {name}: ירוק כמצופה")
        return
    missing = set(must_have_errors) - got
    if missing:
        FAILED.append(f"{name}: כללים שלא נתפסו: {sorted(missing)} | נתפסו: {sorted(got)}")
    else:
        print(f"✅ {name}: כל {len(must_have_errors)} הכללים נתפסו ({len(rep.errors)} שגיאות סה\"כ)")

expect("marom_bad", FIX / "marom_bad.html", "marom", must_have_errors=[
    "CSS_COMMENT", "CSS_VAR", "CSS_REM", "CSS_CUSTOM_PROP",
    "BACKSLASH", "PCT_UPPER", "TERM", "EXPERT", "PHONE",
    "BRAND_BEKO", "DELONGHI_COFFEE", "FORBIDDEN_SOURCE",
    "FORBIDDEN_LINK", "XML_SITEMAP", "VIDEO_PLACEHOLDER",
    "SCHEMA_PRODUCT_BLOG", "NAP_ADDR", "NAP_PHONE", "MAROM_PC_LINK",
])

expect("marom_good", FIX / "marom_good.html", "marom", must_pass=True,
       expect_type="blog")

expect("blog_good", FIX / "blog_good.html", "csb", must_pass=True,
       expect_type="blog")  # bh-pref-mini אינו סמן brandhub

expect("anchor_bad", FIX / "anchor_bad.html", "csb", doc_type="blog",
       must_have_errors=["ANCHOR_FORBIDDEN"])  # v1.3.0; ANCHOR_DUPLICATE/LINK_BUDGET/SPEAKABLE = WARN

expect("blog_product_schema", FIX / "blog_product_schema.html", "csb",
       must_have_errors=["SCHEMA_PRODUCT_BLOG"])

expect("schema_id_collision_bad", FIX / "schema_id_collision_bad.html", "csb",
       must_have_errors=["SCHEMA_ID_YOAST_COLLISION"])  # v1.4.0; #article/#breadcrumb מתנגשים עם @graph של Yoast

expect("brandhub_good", FIX / "brandhub_good.html", "marom", must_pass=True,
       expect_type="brandhub")  # כולל /brands/haier-service/ — לא קישור אסור

expect("brandhub_bad_responsive", FIX / "brandhub_bad_responsive.html", "marom",
       must_have_errors=["RESPONSIVE_GRID", "RESPONSIVE_STICKY",
                         "RESPONSIVE_MEDIA", "PHONE_ENTITY", "CTA_LOGIN"])

expect("elementor_bad", FIX / "elementor_bad.html", "marom", must_have_errors=[
    "UNICODE_BIDI", "SVG_INLINE", "GA_EVENT", "TARGET_BLANK",
    "CHAR_BLOCKER", "CSS_UNBALANCED", "MEDIA_NESTED", "HREF_EMPTY",
])

expect("csb_bad", FIX / "csb_bad.html", "csb", must_have_errors=[
    "EMDASH", "FORBIDDEN_LINK", "EXPERT",
])

expect("plrom_bad", FIX / "plrom_bad.html", "plrom", must_have_errors=[
    "FORBIDDEN_PC", "FORBIDDEN_LINK", "BRAND_ELECTRA", "EXPERT",
])

expect("brandhub_encoded", FIX / "brandhub_encoded.html", "marom",
       must_have_errors=["WAF_ENCODED"], doc_type="brandhub")

expect("waf_blog", FIX / "waf_blog.html", "marom",
       must_have_errors=["WAF_ENCODED"], expect_type="blog")

expect("product_bad", FIX / "product_bad.md", "csb",
       must_have_errors=["TERM_IMITATION", "EXPERT"], expect_type="product")

print()
if FAILED:
    print("🔴 selftest נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print("✅ selftest עבר במלואו — pal-lint מאומת")
