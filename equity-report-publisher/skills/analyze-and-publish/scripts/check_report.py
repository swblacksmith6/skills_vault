#!/usr/bin/env python3
"""
check_report.py -- render a built report headlessly and assert it is sound.

  python check_report.py TICKER_report_YYYYMMDD.html [--shot out.png]

Fails loudly on: JS console errors, charts that did not draw (canvas left at the
303x150 default), and empty collapsible sections. A report whose charts silently
fail is worse than one with no charts.
"""
import argparse, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--shot", help="also save a screenshot here")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed:  pip install playwright --break-system-packages")

    import os
    url = "file://" + os.path.abspath(a.html)
    errs = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1180, "height": 1000})
        pg.on("console", lambda m: errs.append(("console", m.text)) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(("pageerror", str(e))))
        pg.goto(url)
        pg.wait_for_timeout(3500)
        info = pg.evaluate("""() => ({
            chart: typeof Chart,
            canvases: Array.from(document.querySelectorAll('canvas')).map(c => [c.id, c.width, c.height]),
            details: Array.from(document.querySelectorAll('details pre')).map(p => p.textContent.length),
            tables: document.querySelectorAll('table').length,
            height: document.body.scrollHeight
        })""")
        if a.shot:
            pg.screenshot(path=a.shot, full_page=False)
        b.close()

    print("Chart.js:      %s" % info["chart"])
    print("tables:        %d" % info["tables"])
    print("page height:   %dpx" % info["height"])
    print("canvases:      %s" % info["canvases"])
    print("raw sections:  %s chars" % info["details"])

    problems = []
    if errs:
        problems.append("console errors: %s" % errs)
    if info["canvases"] and info["chart"] == "undefined":
        problems.append("charts present but Chart.js did not load")
    for cid, w, h in info["canvases"]:
        if w <= 310 and h <= 160:
            problems.append("canvas %r never sized - chart did not draw" % cid)
    for i, n in enumerate(info["details"]):
        if n == 0:
            problems.append("collapsible raw section %d is empty" % i)

    if problems:
        print("\nFAIL")
        for p_ in problems:
            print("  ! " + p_)
        sys.exit(1)
    print("\nOK")

if __name__ == "__main__":
    main()
