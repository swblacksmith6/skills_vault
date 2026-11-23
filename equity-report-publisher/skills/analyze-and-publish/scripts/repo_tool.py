#!/usr/bin/env python3
"""
repo_tool.py -- GitHub Pages repo helper for equity-report-publisher.

Subcommands
  find-prior  --repo R --company "Name" [--ticker T]
      Locate the company's folder (via index.html entry, folder name, or ticker-prefixed
      files) and list earlier dated analyses. Prints JSON.

  publish     --repo R --folder "Folder" --company "Display Name" --date YYYYMMDD
              --files f1 f2 ... [--commit] [--message "..."]
      Copy the analysis files into <repo>/<folder>/, add Jekyll front matter to markdown
      that lacks it, insert or replace the company's entry in index.html (alphabetical,
      newest report as the main link, older reports as "Earlier" links), make sure
      .gitignore excludes temp/ and .DS_Store, and optionally `git add` exactly those
      paths and commit. Never runs `git add .` and never pushes.

  gitignore   --repo R
      Only ensure the .gitignore lines.
"""
import argparse, html, json, os, re, shutil, subprocess, sys
from urllib.parse import quote, unquote

LABELS = [  # (filename fragment, link label) -- order = display order
    ("storyline", "What changed"),
    ("quick_scan", "Quick scan"),
    ("walk_the_talk", "Walk the talk"),
    ("concall", "Concall analysis"),
    ("growth_triggers", "Growth triggers"),
    ("sector_valuation", "Sector valuation"),
    ("valuation", "Valuation"),
]
GITIGNORE_LINES = ["temp/", ".DS_Store"]
DATE_RE = re.compile(r"_(\d{8})\.(md|html)$")


def norm(s):
    s = re.sub(r"\b(ltd|limited|india|pvt|private|the)\b", "", s.lower())
    return re.sub(r"[^a-z0-9]", "", s)


def label_for(fname):
    for frag, lab in LABELS:
        if frag in fname:
            return lab
    return None


def href(folder, fname):
    return quote(folder) + "/" + quote(fname)


# ---------------------------------------------------------------- index.html
LI_RE = re.compile(r"[ \t]*<li>\s*<div class=\"company-row\">.*?</li>\n?", re.S)
NAME_RE = re.compile(r'<a class="company-name" href="([^"]+)">([^<]+)</a>')


def index_entries(index_html):
    out = []
    for m in LI_RE.finditer(index_html):
        n = NAME_RE.search(m.group(0))
        if n:
            folder = unquote(n.group(1).split("/")[0])
            out.append({"start": m.start(), "end": m.end(), "name": html.unescape(n.group(2)),
                        "folder": folder, "text": m.group(0)})
    return out


def render_li(folder, company, report, docs, earlier):
    c = html.escape(company)
    lines = ["        <li>", '          <div class="company-row">',
             '            <a class="company-name" href="%s">%s</a>' % (href(folder, report), c),
             '            <span class="company-links" aria-label="%s documents">' % c]
    for lab, fn in docs:
        lines.append('              <a href="%s">%s</a>' % (href(folder, fn), lab))
    for d, fn in earlier:
        lines.append('              <a href="%s">Earlier: %s</a>' % (href(folder, fn), d))
    lines += ["            </span>", "          </div>", "        </li>", ""]
    return "\n".join(lines)


def update_index(repo, folder, company, date, files):
    p = os.path.join(repo, "index.html")
    src = open(p, encoding="utf-8").read()
    report = next((f for f in files if f.endswith(".html")), None)
    if not report:
        sys.exit("publish: no .html report among --files")
    docs = []
    for frag, lab in LABELS:
        for f in files:
            if f.endswith(".md") and frag in f and lab not in [d[0] for d in docs] \
                    and f not in [d[1] for d in docs]:
                docs.append((lab, f))
                break
    # earlier reports already in the folder
    earlier = []
    fdir = os.path.join(repo, folder)
    for fn in sorted(os.listdir(fdir), reverse=True):
        m = DATE_RE.search(fn)
        if fn.endswith(".html") and fn != report and m and m.group(1) < date:
            d = m.group(1)
            earlier.append(("%s-%s-%s" % (d[6:], d[4:6], d[:4]), fn))
    li = render_li(folder, company, report, docs, earlier)

    entries = index_entries(src)
    match = [e for e in entries if e["folder"] == folder or norm(e["name"]) == norm(company)]
    if match:
        e = match[0]
        new = src[:e["start"]] + li + src[e["end"]:]
    else:
        after = [e for e in entries if e["name"].lower() > company.lower()]
        if after:
            pos = after[0]["start"]
            new = src[:pos] + li + "\n" + src[pos:]
        elif entries:
            pos = entries[-1]["end"]
            new = src[:pos] + "\n" + li + src[pos:]
        else:
            m = re.search(r'<ul class="company-list">\n', src)
            if not m:
                sys.exit("publish: could not find <ul class=\"company-list\"> in index.html")
            new = src[:m.end()] + li + src[m.end():]
    new = re.sub(r"\n{3,}(\s*<li>)", r"\n\n\1", new)
    open(p, "w", encoding="utf-8").write(new)
    return "updated" if match else "added"


# ---------------------------------------------------------------- helpers
def ensure_gitignore(repo):
    p = os.path.join(repo, ".gitignore")
    cur = open(p, encoding="utf-8").read().splitlines() if os.path.exists(p) else []
    add = [l for l in GITIGNORE_LINES if l not in cur]
    if add:
        with open(p, "a", encoding="utf-8") as fh:
            if cur and cur[-1] != "":
                fh.write("\n")
            fh.write("\n".join(add) + "\n")
    return add


def ensure_front_matter(path, company):
    txt = open(path, encoding="utf-8").read()
    if txt.startswith("---\n"):
        return False
    m = re.search(r"^#\s+(.+)$", txt, re.M)
    title = (m.group(1).strip() if m else os.path.basename(path)).replace('"', "'")
    fm = '---\ntitle: "%s"\ncompany: "%s"\n---\n\n' % (title, company.replace('"', "'"))
    open(path, "w", encoding="utf-8").write(fm + txt)
    return True


def find_prior(repo, company, ticker=None):
    folder = None
    try:
        src = open(os.path.join(repo, "index.html"), encoding="utf-8").read()
        for e in index_entries(src):
            if norm(e["name"]) == norm(company) or norm(company) in norm(e["name"]):
                folder = e["folder"]
                break
    except FileNotFoundError:
        pass
    dirs = [d for d in os.listdir(repo) if os.path.isdir(os.path.join(repo, d))
            and not d.startswith((".", "_")) and d != "temp"]
    if not folder:
        for d in dirs:
            if norm(d) and (norm(d) in norm(company) or norm(company) in norm(d)):
                folder = d
                break
    if not folder and ticker:
        for d in dirs:
            if any(f.upper().startswith(ticker.upper() + "_") for f in os.listdir(os.path.join(repo, d))):
                folder = d
                break
    if not folder:
        return {"found": False, "folder": None}
    by_date = {}
    undated = []
    for fn in sorted(os.listdir(os.path.join(repo, folder))):
        if not fn.endswith((".md", ".html")):
            continue
        m = DATE_RE.search(fn)
        rel = os.path.join(folder, fn)
        if m:
            by_date.setdefault(m.group(1), []).append(rel)
        else:
            undated.append(rel)
    dates = sorted(by_date, reverse=True)
    return {"found": True, "folder": folder, "ticker_prefix": next((os.path.basename(f).split("_")[0] for d in dates for f in by_date[d]
                                   if f.endswith(".html")), None),
            "latest_date": dates[0] if dates else None, "dates": dates,
            "files_by_date": by_date, "undated_files": undated}


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True, text=True)
    if r.returncode:
        sys.exit("git %s failed:\n%s%s" % (" ".join(args), r.stdout, r.stderr))
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("find-prior"); a1.add_argument("--repo", required=True)
    a1.add_argument("--company", required=True); a1.add_argument("--ticker")
    a2 = sub.add_parser("publish"); a2.add_argument("--repo", required=True)
    a2.add_argument("--folder", required=True); a2.add_argument("--company", required=True)
    a2.add_argument("--date", required=True); a2.add_argument("--files", nargs="+", required=True)
    a2.add_argument("--commit", action="store_true"); a2.add_argument("--message")
    a3 = sub.add_parser("gitignore"); a3.add_argument("--repo", required=True)
    a = ap.parse_args()

    if a.cmd == "find-prior":
        print(json.dumps(find_prior(a.repo, a.company, a.ticker), indent=2))
        return
    if a.cmd == "gitignore":
        print("added: %s" % ensure_gitignore(a.repo))
        return

    if not re.fullmatch(r"\d{8}", a.date):
        sys.exit("--date must be YYYYMMDD")
    dest = os.path.join(a.repo, a.folder)
    os.makedirs(dest, exist_ok=True)
    names = []
    for f in a.files:
        fn = os.path.basename(f)
        target = os.path.join(dest, fn)
        if os.path.abspath(f) != os.path.abspath(target):
            shutil.copyfile(f, target)
        if fn.endswith(".md"):
            ensure_front_matter(target, a.company)
        names.append(fn)
    action = update_index(a.repo, a.folder, a.company, a.date, names)
    gi = ensure_gitignore(a.repo)
    paths = [os.path.join(a.folder, n) for n in names] + ["index.html", ".gitignore"]
    print("copied %d files to %s/; index entry %s; .gitignore added %s" % (len(names), a.folder, action, gi))
    if a.commit:
        git(a.repo, "add", "--", *paths)
        msg = a.message or "Add %s analysis (%s)" % (a.company, a.date)
        staged = git(a.repo, "diff", "--cached", "--name-only")
        if not staged.strip():
            print("nothing to commit")
            return
        ident = []
        r = subprocess.run(["git", "-C", a.repo, "config", "user.name"], capture_output=True, text=True)
        if not r.stdout.strip():  # sandboxed shells often lack an identity: reuse the last author
            name, email = git(a.repo, "log", "-1", "--format=%an|%ae").strip().split("|")
            ident = ["-c", "user.name=" + name, "-c", "user.email=" + email]
        subprocess.run(["git", "-C", a.repo] + ident + ["commit", "-q", "-m", msg], check=True)
        print("committed:\n" + staged + git(a.repo, "log", "--oneline", "-1"))


if __name__ == "__main__":
    main()
