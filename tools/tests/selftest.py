#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""בדיקה עצמית של pal-lint: מאמת שכל כלל נתפס ושתוכן תקין עובר ירוק."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pal_lint import run

FIX = Path(__file__).parent / "fixtures"
FAILED = []

def expect(name, path, site, must_have_errors=(), must_pass=False, doc_type=None):
    rep, s, d = run(path, site, doc_type)
    got = {e["rule"] for e in rep.errors}
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
    "SCHEMA_OFFERS", "NAP_ADDR", "NAP_PHONE",
])

expect("marom_good", FIX / "marom_good.html", "marom", must_pass=True)

expect("csb_bad", FIX / "csb_bad.html", "csb", must_have_errors=[
    "EMDASH", "FORBIDDEN_LINK", "EXPERT",
])

expect("plrom_bad", FIX / "plrom_bad.html", "plrom", must_have_errors=[
    "FORBIDDEN_PC", "FORBIDDEN_LINK", "BRAND_ELECTRA", "EXPERT",
])

expect("brandhub_encoded", FIX / "brandhub_encoded.html", "marom",
       must_have_errors=["BRANDHUB_ENCODED"], doc_type="brandhub")

print()
if FAILED:
    print("🔴 selftest נכשל:")
    for f in FAILED:
        print("   " + f)
    sys.exit(1)
print("✅ selftest עבר במלואו — pal-lint מאומת")
