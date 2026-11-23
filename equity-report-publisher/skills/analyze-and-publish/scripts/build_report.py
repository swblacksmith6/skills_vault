#!/usr/bin/env python3
"""
build_report.py -- (equity-report-publisher copy of equity-deep-dive's builder; adds a
non-removable educational disclaimer banner and an "Earlier analyses" strip.)
Fuse a report.json into one self-contained offline HTML report.

  python build_report.py report.json --out TICKER_report_YYYYMMDD.html

Reads assets/report_template.html and inlines assets/chart.umd.js, so the output
needs no network, no CDN and no server. See references/13-report-schema.md for the
full input contract; run with --example to print a minimal working report.json.

Design note: everything except charts is rendered to static HTML here in Python,
so tables, callouts and the raw-markdown sections still work with JS disabled.
Only the <canvas> charts need Chart.js.
"""
import argparse, html, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATE = os.path.join(ROOT, "assets", "report_template.html")

# Hard-coded on purpose: report.json cannot remove or soften this.
DISCLAIMER_HTML = ("<b>&#9888; Educational purpose only &mdash; this is NOT a buy or sell recommendation.</b> "
                   "AI-generated research that may contain errors. If you act on it without doing your own "
                   "research, you are guaranteed to lose your money.")
CHARTJS = os.path.join(ROOT, "assets", "chart.umd.js")

TONE_CLASS = {"green": "g", "amber": "a", "red": "r", "grey": "n",
              "g": "g", "a": "a", "r": "r", "n": "n"}
TONE_VAR = {"green": "var(--green)", "amber": "var(--amber)",
            "red": "var(--red)", "grey": "var(--grey)", "blue": "var(--blue)"}
TAG_CLASS = {"green": "t-g", "amber": "t-a", "red": "t-r", "grey": "t-n"}


def esc(s):
    return html.escape(str(s), quote=False)


def cell_html(cell, col_num=False, tag="td"):
    """cell may be a plain scalar or {v, tone, num, bold, escape, tag, cite}.

    Text is treated as raw HTML by default -- consistent with every other text
    field in the schema, and table evidence almost always wants <b>/<i>. Pass
    {"escape": true} for the rare cell containing literal angle brackets."""
    if not isinstance(cell, dict):
        v, tone, num, bold, escape, tagtxt, cite = cell, None, col_num, False, False, None, None
    else:
        v = cell.get("v", "")
        tone = cell.get("tone")
        num = cell.get("num", col_num)
        bold = cell.get("bold", False)
        escape = cell.get("escape", False)
        tagtxt = cell.get("tag")
        cite = cell.get("cite")
    body = esc(v) if escape else str(v)
    if bold:
        body = "<b>%s</b>" % body
    if tagtxt:
        t = TAG_CLASS.get(str(tagtxt).lower(), "t-n")
        body = ('<span class="tag %s">%s</span>' % (t, esc(str(tagtxt).upper()))) + (" " + body if v not in ("", None) else "")
    if cite:
        body += '<span class="cite">%s</span>' % cite
    classes = []
    if num:
        classes.append("num")
    if tone:
        c = TONE_CLASS.get(str(tone).lower())
        if c:
            classes.append(c)
    cls = ' class="%s"' % " ".join(classes) if classes else ""
    return "<%s%s>%s</%s>" % (tag, cls, body, tag)


def render_table(b):
    cols = b.get("columns", [])
    specs = []
    for c in cols:
        if isinstance(c, dict):
            specs.append({"label": c.get("label", ""), "num": c.get("num", False), "width": c.get("width")})
        else:
            specs.append({"label": c, "num": False, "width": None})
    out = []
    if b.get("title"):
        out.append("<h3>%s</h3>" % esc(b["title"]))
    out.append("<table>")
    if specs:
        head = []
        for s in specs:
            style = ' style="width:%s"' % s["width"] if s["width"] else ""
            cls = ' class="num"' if s["num"] else ""
            head.append("<th%s%s>%s</th>" % (cls, style, esc(s["label"])))
        out.append("<thead><tr>%s</tr></thead>" % "".join(head))
    out.append("<tbody>")
    for row in b.get("rows", []):
        cells = []
        for i, cell in enumerate(row):
            col_num = specs[i]["num"] if i < len(specs) else False
            cells.append(cell_html(cell, col_num))
        out.append("<tr>%s</tr>" % "".join(cells))
    out.append("</tbody></table>")
    if b.get("note"):
        out.append('<p class="small">%s</p>' % b["note"])
    if b.get("cite"):
        out.append('<p class="cite">%s</p>' % b["cite"])
    return "\n".join(out)


def render_callout(b):
    tone = b.get("tone", "red")
    out = ['<div class="callout %s">' % ("" if tone == "red" else esc(tone))]
    if b.get("title"):
        out.append("<h4>%s</h4>" % esc(b["title"]))
    if b.get("html"):
        out.append(b["html"])
    if b.get("items"):
        tag = "ol" if b.get("ordered", True) else "ul"
        out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % i for i in b["items"]), tag))
    out.append("</div>")
    return "\n".join(out)


def render_stats(items):
    out = ['<div class="grid">']
    for s in items:
        colour = TONE_VAR.get(str(s.get("tone", "")).lower())
        style = ' style="color:%s"' % colour if colour else ""
        out.append('<div class="stat">')
        out.append('<div class="lbl">%s</div>' % esc(s.get("label", "")))
        out.append('<div class="val"%s>%s</div>' % (style, s.get("value", "")))
        if s.get("bar") is not None:
            pct = max(0.0, min(100.0, float(s["bar"])))
            out.append('<div class="bar"><i style="width:%.1f%%;background:%s"></i></div>'
                       % (pct, colour or "var(--grey)"))
        if s.get("note"):
            out.append('<div class="note">%s</div>' % s["note"])
        out.append("</div>")
    out.append("</div>")
    return "\n".join(out)


def render_chart(b, charts, idx):
    cid = b.get("id") or "chart%d" % idx[0]
    idx[0] += 1
    charts[cid] = b["chart"]
    h = b.get("height", 300)
    out = ['<div class="chartbox">']
    if b.get("title"):
        out.append("<h4>%s</h4>" % esc(b["title"]))
    if b.get("note"):
        out.append("<p>%s</p>" % b["note"])
    out.append('<div class="cw" style="height:%dpx"><canvas id="%s"></canvas></div>' % (h, cid))
    out.append("</div>")
    return "\n".join(out)


def render_blocks(blocks, charts, idx):
    out = []
    for b in blocks or []:
        t = b.get("type", "html")
        if t == "html":
            out.append(b.get("html", ""))
        elif t == "h3":
            out.append("<h3>%s</h3>" % esc(b.get("text", "")))
        elif t == "card":
            out.append('<div class="card">%s</div>' % render_blocks(b.get("blocks", []), charts, idx))
        elif t == "table":
            out.append(render_table(b))
        elif t == "callout":
            out.append(render_callout(b))
        elif t == "stats":
            out.append(render_stats(b.get("items", [])))
        elif t == "chart":
            out.append(render_chart(b, charts, idx))
        elif t == "charts2":
            inner = "".join(render_chart(c, charts, idx) for c in b.get("charts", []))
            out.append('<div class="two">%s</div>' % inner)
        elif t == "columns2":
            left = render_blocks(b.get("left", []), charts, idx)
            right = render_blocks(b.get("right", []), charts, idx)
            out.append('<div class="two"><div>%s</div><div>%s</div></div>' % (left, right))
        else:
            raise SystemExit("build_report.py: unknown block type %r" % t)
    return "\n".join(out)


def build(data):
    charts, idx = {}, [1]
    meta = data.get("meta", {})
    verdict = data.get("verdict", {})

    head = ['<header><div class="wrap">']
    head.append("<h1>%s</h1>" % esc(meta.get("company", "")))
    subbits = [x for x in (meta.get("exchange"), meta.get("sector"),
                           "Report date: " + meta["date"] if meta.get("date") else None) if x]
    if subbits:
        head.append('<div class="sub">%s</div>' % " &nbsp;|&nbsp; ".join(esc(s) for s in subbits))
    head.append('<div class="strip">')
    if verdict.get("label"):
        head.append('<span class="badge b-%s">%s</span>'
                    % (esc(verdict.get("tone", "grey")), esc(verdict["label"])))
    for kv in meta.get("kv", []):
        head.append('<span class="kv"><span>%s</span><b>%s</b></span>'
                    % (esc(kv.get("label", "")), esc(kv.get("value", ""))))
    head.append("</div>")
    if meta.get("price_note"):
        head.append('<div class="cite">%s</div>' % esc(meta["price_note"]))
    prev = meta.get("previous") or []
    if prev:
        links = " ".join('<a href="%s">%s</a>' % (esc(p.get("href", "#")), esc(p.get("label", p.get("date", ""))))
                         for p in prev)
        head.append('<div class="hist"><b>Earlier analyses:</b> %s</div>' % links)
    head.append("</div></header>")

    body = ['<div class="wrap">']
    if data.get("exec_summary"):
        body.append("<h2>Executive summary</h2>")
        body.append(render_blocks(data["exec_summary"], charts, idx))
    if data.get("stats"):
        body.append(render_stats(data["stats"]))
    for sec in data.get("sections", []):
        if sec.get("title"):
            body.append("<h2>%s</h2>" % esc(sec["title"]))
        body.append(render_blocks(sec.get("blocks", []), charts, idx))

    raw = data.get("raw", [])
    if raw:
        body.append("<h2>%s</h2>" % esc(data.get("raw_title", "Full source analyses")))
        for r in raw:
            text = r.get("text", "")
            if r.get("file"):
                with open(r["file"], encoding="utf-8") as fh:
                    text = fh.read()
            body.append("<details><summary>&#9656; %s</summary><pre>%s</pre></details>"
                        % (esc(r.get("label", "Detail")), esc(text)))

    body.append('<div class="disc-foot">%s</div>' % DISCLAIMER_HTML)
    f = data.get("footer", {})
    if f:
        body.append("<footer>")
        for key in ("generated", "sources", "method", "disclaimer"):
            if f.get(key):
                body.append("<p>%s</p>" % f[key])
        body.append("</footer>")
    body.append("</div>")

    with open(TEMPLATE, encoding="utf-8") as fh:
        tpl = fh.read()
    chartjs = ""
    if charts:
        if not os.path.exists(CHARTJS):
            raise SystemExit("build_report.py: charts requested but assets/chart.umd.js is missing")
        with open(CHARTJS, encoding="utf-8") as fh:
            chartjs = "/* Chart.js v4 (MIT) - inlined for offline use */\n" + fh.read()
    for blob in (chartjs, json.dumps(charts)):
        if "</script>" in blob.lower():
            raise SystemExit("build_report.py: refusing to emit content containing </script>")

    title = "%s - Investment Report" % meta.get("company", "Investment Report")
    if meta.get("date"):
        title += " | " + meta["date"]
    out = tpl.replace("__TITLE__", esc(title))
    out = out.replace("__DISCLAIMER_TOP__", '<div class="disc" role="alert">%s</div>' % DISCLAIMER_HTML)
    out = out.replace("__BODY__", "\n".join(head + body))
    out = out.replace("__CHARTJS__", chartjs)
    out = out.replace("__CHARTS__", json.dumps(charts))
    return out


EXAMPLE = {
    "meta": {
        "company": "Example Ltd", "exchange": "NSE: EXMP", "sector": "Capital Goods",
        "date": "18 August 2026", "price_note": "Price data: source, as of 17-Aug-2026.",
        "kv": [{"label": "CMP", "value": "₹136"}, {"label": "Mcap", "value": "₹803 cr"}],
    },
    "verdict": {"label": "WATCH — revisit on trigger", "tone": "amber"},
    "exec_summary": [{"type": "card", "blocks": [
        {"type": "html", "html": "<p><b>Verdict: WATCH.</b> One-paragraph summary.</p>"}]}],
    "stats": [{"label": "Piotroski F-Score", "value": "3 <span style='font-size:15px;color:var(--grey)'>/ 9</span>",
               "tone": "red", "bar": 33.3, "note": "Financially weak band."}],
    "sections": [{"title": "1 · Quick scan", "blocks": [
        {"type": "table",
         "columns": ["Metric", {"label": "FY25", "num": True}, {"label": "FY26", "num": True}],
         "rows": [["Revenue", 345.89, 377.88],
                  ["CFO", {"v": -3.43, "tone": "red", "bold": True}, {"v": -48.85, "tone": "red", "bold": True}]],
         "cite": "Annual Report FY26"},
        {"type": "callout", "tone": "red", "title": "Bear case",
         "items": ["Three straight years of negative operating cash flow."]},
        {"type": "chart", "title": "PAT vs operating cash flow (₹ cr)",
         "chart": {"type": "bar",
                   "data": {"labels": ["FY24", "FY25", "FY26"], "datasets": [
                       {"label": "PAT", "data": [23.96, 30.51, 34.74], "backgroundColor": "#16a34a"},
                       {"label": "CFO", "data": [-8.39, -3.43, -48.85], "backgroundColor": "#dc2626"}]},
                   "options": {"plugins": {"legend": {"position": "bottom"}}}}}]}],
    "raw": [{"label": "Full Quick Scan markdown", "text": "# Quick scan\n..."}],
    "footer": {"generated": "<b>Generated:</b> 18 August 2026.",
               "sources": "<b>Sources:</b> ...",
               "disclaimer": "<b>Research only. Not investment advice.</b>"},
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", nargs="?", help="report.json")
    ap.add_argument("--out", "-o", help="output .html path")
    ap.add_argument("--example", action="store_true", help="print a minimal report.json and exit")
    a = ap.parse_args()
    if a.example:
        print(json.dumps(EXAMPLE, indent=2, ensure_ascii=False))
        return
    if not a.input:
        ap.error("input report.json required (or --example)")
    with open(a.input, encoding="utf-8") as fh:
        data = json.load(fh)
    out = build(data)
    dest = a.out or os.path.splitext(a.input)[0] + ".html"
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("wrote %s  (%.0f KB, %d charts)" % (dest, len(out) / 1024, out.count("<canvas")))


if __name__ == "__main__":
    main()
