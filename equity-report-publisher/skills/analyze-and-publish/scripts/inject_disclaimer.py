#!/usr/bin/env python3
"""
inject_disclaimer.py -- add the sticky red "educational purpose only" banner (top) and a
matching block (bottom) to any HTML file that does not already carry it.

  python inject_disclaimer.py FILE.html [FILE2.html ...]

Idempotent: files already containing the banner (built by this plugin's build_report.py,
or injected earlier) are skipped. Works on standalone reports, index.html and Jekyll
layouts (_layouts/report.html), so markdown pages rendered by Pages get it too.
"""
import re, sys

MARK = "edu-disclaimer"
TEXT = ("<b>&#9888; EDUCATIONAL PURPOSE ONLY &mdash; THIS IS NOT A BUY OR SELL RECOMMENDATION.</b> "
        "AI-generated research that may contain errors. If you act on it without doing your own "
        "research, you are guaranteed to lose your money.")
TOP = ('<!-- %s -->\n<div class="%s" role="alert" style="position:sticky;top:0;z-index:2147483000;'
       'background:#fee2e2;border-bottom:3px solid #dc2626;color:#b91c1c;font-weight:800;'
       'text-align:center;padding:9px 14px;font-size:14px;line-height:1.4;'
       'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;'
       'box-shadow:0 2px 6px rgba(0,0,0,.08)">%s</div>\n') % (MARK, MARK, TEXT)
BOTTOM = ('<div class="%s-foot" style="max-width:1100px;margin:28px auto;border:3px solid #dc2626;'
          'background:#fee2e2;color:#b91c1c;font-weight:800;font-size:15px;padding:14px 18px;'
          'border-radius:6px;text-align:center;'
          'font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif">%s</div>\n'
          ) % (MARK, TEXT)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for p in sys.argv[1:]:
        s = open(p, encoding="utf-8").read()
        if MARK in s or 'class="disc"' in s:
            print("skip (already has banner): %s" % p)
            continue
        m = re.search(r"<body[^>]*>", s, re.I)
        e = s.lower().rfind("</body>")
        if not m or e < 0:
            print("skip (no <body>): %s" % p)
            continue
        s = s[:m.end()] + "\n" + TOP + s[m.end():e] + BOTTOM + s[e:]
        open(p, "w", encoding="utf-8").write(s)
        print("added banner: %s" % p)


if __name__ == "__main__":
    main()
