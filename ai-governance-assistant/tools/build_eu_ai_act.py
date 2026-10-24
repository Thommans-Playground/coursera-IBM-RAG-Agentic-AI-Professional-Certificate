"""Build the EU AI Act dataset from the European Commission's AI Act Service Desk pages.

Input: a folder of saved pages (article-1.html ... article-113.html, annex-1.html ... annex-14.html),
downloaded from https://ai-act-service-desk.ec.europa.eu/en/ai-act/<slug>. The site says its text is the
EUR-Lex consolidated version as at 27 July 2026 and marks Digital Omnibus changes NEW / AMENDED / DELETED.
That is a reading aid. The authentic text is the Official Journal.

Usage: python -I tools/build_eu_ai_act.py <pages dir> data/frameworks/eu-ai-act
Writes provisions.csv, facets.csv, definitions.csv.
"""
import csv, html, pathlib, re, sys

pages_dir, out_dir = map(pathlib.Path, sys.argv[1:3])
out_dir.mkdir(parents=True, exist_ok=True)
FW = "eu-ai-act"
BASE = "https://ai-act-service-desk.ec.europa.eu/en/ai-act/"
clean = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ")).strip()
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"]

# ---------------------------------------------------------------- navigation: chapters, sections, articles, annexes
nav_src = (pages_dir / "article-5.html").read_text(errors="ignore")
start = nav_src.find('class="ecl-accordion__item chapters'); end = nav_src.find("cnt-annex-list")
end = nav_src.find("</details>", end)
nav = nav_src[start:end]
tok = re.compile(r'ecl-accordion__toggle">\s*(Chapter [IVXLC]+: [^<]+?)\s*<span|<p class="section-item[^"]*">\s*(Section \d+: [^<]+?)\s*</p>|href="/en/ai-act/(article-[0-9a-z]+)">\s*([^<]+?)\s*</a>|href="/en/ai-act/(annex-\d+)"[^>]*>\s*(ANNEX [IVXL]+)\s*</a>')
structure = []     # ordered: ("chapter", id, title) ("section", id, title) ("article", slug, title) ("annex", slug, label)
chapter_id = section_id = None
for m in tok.finditer(nav):
    if m[1]:
        num, title = m[1].split(": ", 1); num = num.replace("Chapter ", "")
        chapter_id, section_id = f"Ch.{num}", None
        structure.append(("chapter", chapter_id, html.unescape(title), None, None))
    elif m[2]:
        num, title = m[2].split(": ", 1); num = num.replace("Section ", "")
        section_id = f"{chapter_id}.S{num}"
        structure.append(("section", section_id, html.unescape(title), chapter_id, None))
    elif m[3]:
        slug = m[3]; label = html.unescape(m[4]); title = label.split(": ", 1)[1] if ": " in label else label
        structure.append(("article", slug, title, chapter_id, section_id))
    elif m[5]:
        structure.append(("annex", m[5], m[6], None, None))
print("nav:", {k: sum(1 for s in structure if s[0] == k) for k in ("chapter", "section", "article", "annex")})

# ---------------------------------------------------------------- text of one page -> markers and paragraphs
def page_paras(slug):
    t = (pages_dir / f"{slug}.html").read_text(errors="ignore")
    blocks = re.findall(r'<div class="ecl cnt-parag-content">(.*?)</div>\s*</div>\s*</div>', t, re.S) or re.findall(r'<div class="ecl cnt-parag-content">(.*?)</div>', t, re.S)
    out, pending = [], ""
    for b in blocks:
        for m in re.finditer(r"<p([^>]*)>(.*?)</p>", b, re.S):
            attrs, txt = m[1], clean(m[2])
            if not txt: continue
            if "ecl-label" in attrs and txt in ("NEW", "AMENDED", "DELETED"): pending = txt; continue
            flag = pending or ("NEW" if "bg-success" in attrs else ""); pending = ""
            out.append((txt, flag))
    return out

def marker(txt):
    if m := re.match(r"^(\d+[a-z]?)[.)]\s+(.*)$", txt): return "NUM", m[1], m[2]
    if m := re.match(r"^\((\d+)\)\s+(.*)$", txt): return "PNUM", m[1], m[2]
    if m := re.match(r"^\(([a-z]{1,3})\)\s+(.*)$", txt): return "ALPHA", m[1], m[2]
    return None, None, txt

rows, facets, definitions = [], [], []
used = set()
def add(**r):
    base = dict(framework=FW, parent="", level="", ordinal="", title="", kind="OBLIGATION", is_header="no", assessable="no",
                source_text="", aliases="", status="verified-consolidated", note="", source_ref="")
    base.update(r); rows.append(base); return base

def build(slug, root_id, root_title, level, parent, ordinal, kind_default):
    paras = page_paras(slug)
    used.add(f"{FW}:{root_id}")
    root = add(id=f"{FW}:{root_id}", parent=parent, level=level, ordinal=ordinal, title=root_title, kind="GROUP", is_header="yes",
               source_ref=BASE + slug, aliases=root_id.replace("Art.", "Article ").replace("Annex.", "Annex "))
    markers = [marker(t)[:2] for t, _ in paras]
    nodes = []                      # (row, children count holder)
    stack = []                      # entries: dict(type, token, row, last_alpha, last_roman)
    ctx = dict(last_alpha=None)
    def top_paragraph():
        for e in reversed(stack):
            if e["type"] in ("NUM", "PNUM"): return e
        return None
    own_text = []
    for i, (txt, flag) in enumerate(paras):
        mtype, token, body = marker(txt)
        if mtype is None and level == "annex" and (sm := re.match(r"^Section ([A-Z0-9]+)\b\s*[—–.:-]?\s*(.*)$", body)):
            while stack: stack.pop()
            sec = add(id=f"{root['id']}.{sm[1]}", parent=root["id"], level="annex-section", ordinal=sm[1], title=f"Section {sm[1]}",
                      kind="GROUP", is_header="yes", source_text=sm[2], source_ref=BASE + slug)
            section_row = sec; stack.append(dict(type="SECTION", token=sm[1], row=sec))
            continue
        if mtype is None:
            if stack: tgt = stack[-1]["row"]; tgt["source_text"] = (tgt["source_text"] + " " + body).strip()
            else: own_text.append(body)
            continue
        # decide ALPHA vs ROMAN
        kind_marker = mtype
        if mtype == "ALPHA":
            para = top_paragraph(); last_alpha = None
            for e in reversed(stack):
                if e["type"] == "ALPHA": last_alpha = e["token"]; break
                if e["type"] in ("NUM", "PNUM"): break
            expected = "a" if last_alpha is None else (chr(ord(last_alpha[-1]) + 1) if len(last_alpha) == 1 else None)
            last_roman = next((e["token"] for e in reversed(stack) if e["type"] == "ROMAN"), None)
            nxt = markers[i + 1][1] if i + 1 < len(markers) else None
            is_roman = False
            if token in ROMAN:
                if last_roman and ROMAN.index(token) == ROMAN.index(last_roman) + 1 and stack[-1]["type"] == "ROMAN": is_roman = True
                elif token == "i" and nxt == "ii": is_roman = True
                elif token not in (expected,) and last_alpha is not None and not (last_alpha and token == chr(ord(last_alpha[-1]) + 1)): is_roman = True
            kind_marker = "ROMAN" if is_roman else "ALPHA"
        # pop the stack to the right parent
        if kind_marker in ("NUM",):
            while stack and stack[-1]["type"] != "SECTION": stack.pop()
        elif kind_marker == "PNUM":
            while stack and stack[-1]["type"] not in ("NUM", "SECTION"): stack.pop()
        elif kind_marker == "ALPHA":
            while stack and stack[-1]["type"] in ("ALPHA", "ROMAN"): stack.pop()
        elif kind_marker == "ROMAN":
            while stack and stack[-1]["type"] == "ROMAN": stack.pop()
        parent_row = stack[-1]["row"] if stack else root
        pid = parent_row["id"].split(":", 1)[1]
        cite = f"{token}" if kind_marker == "NUM" else token
        rid = f"{pid}({cite})"
        dup_note = ""
        if f"{FW}:{rid}" in used:
            n = 2
            while f"{FW}:{rid}[{n}]" in used: n += 1
            rid = f"{rid}[{n}]"; dup_note = "second list with the same lettering under the same paragraph"
        used.add(f"{FW}:{rid}")
        lvl = {"NUM": "paragraph", "PNUM": "item", "ALPHA": "point", "ROMAN": "subpoint"}[kind_marker]
        row = add(id=f"{FW}:{rid}", parent=parent_row["id"], level=lvl, ordinal=token, title="", kind=kind_default,
                  source_text=body, aliases="", note=dup_note, source_ref=BASE + slug)
        if body.startswith("Not present after the amendment"):
            row["source_text"] = ""; row["note"] = "deleted by the Digital Omnibus on AI"; row["kind"] = "DELETED"; flag = "DELETED"
        if flag: facets.append(dict(provision_id=row["id"], facet="digital_omnibus", value=flag.lower(), source="Commission consolidated text"))
        stack.append(dict(type=kind_marker, token=token, row=row))
    if own_text:
        if level == "annex" and len(own_text) > 1:
            root["title"] = f"{root_title}: {own_text[0]}"; root["source_text"] = " ".join(own_text[1:])
        elif level == "annex": root["title"] = f"{root_title}: {own_text[0]}"
        else: root["source_text"] = " ".join(own_text)
    return root

# ---------------------------------------------------------------- walk the structure in order
ordinals = {}
for kind, a, b, c, d in structure:
    if kind == "chapter":
        add(id=f"{FW}:{a}", level="chapter", title=b, kind="GROUP", is_header="yes", ordinal=a.replace("Ch.", ""), source_ref=BASE + "article-5", aliases="Chapter " + a.replace("Ch.", ""))
    elif kind == "section":
        add(id=f"{FW}:{a}", parent=f"{FW}:{b and c}", level="section", title=b, kind="GROUP", is_header="yes", ordinal=a.split(".S")[-1], source_ref=BASE + "article-5", aliases="Section " + a.split(".S")[-1])
for kind, a, b, c, d in structure:
    if kind == "article":
        num = a.replace("article-", ""); parent = f"{FW}:{d}" if d else f"{FW}:{c}"
        ordinals[parent] = ordinals.get(parent, 0) + 1
        kd = "DEFINITION" if num == "3" else "OBLIGATION"
        build(a, f"Art.{num}", b, "article", parent, ordinals[parent], kd)
    elif kind == "annex":
        roman = b.replace("ANNEX ", "")
        build(a, f"Annex.{roman}", b, "annex", "", roman, "LIST_ENTRY")

# fix article / annex header flags from their children
children = {}
for r in rows: children.setdefault(r["parent"], []).append(r)
for r in rows:
    kids = children.get(r["id"], [])
    if r["level"] in ("paragraph", "point", "subpoint", "item"):
        r["assessable"] = "no" if (kids or r["kind"] == "DELETED") else "yes"
    elif r["level"] in ("article", "annex"):
        if not kids and r["source_text"]: r["is_header"], r["assessable"], r["kind"] = "no", "yes", ("LIST_ENTRY" if r["level"] == "annex" else "OBLIGATION")
        elif r["source_text"] and r["level"] == "article": r["is_header"], r["kind"] = "no", "OBLIGATION"
    # annex titles: the first unnumbered line is the annex subtitle
for r in rows:
    if r["level"] == "annex" and r["source_text"] and not children.get(r["id"]): pass

for r in rows:
    if r["level"] == "article" and re.fullmatch(r"eu-ai-act:Art\.\d+[a-z]", r["id"]):
        facets.append(dict(provision_id=r["id"], facet="digital_omnibus", value="new", source="article number with a letter suffix in the consolidated text"))

# ---------------------------------------------------------------- application dates (Article 113, consolidated)
def chapter_of(article_row):
    p = article_row["parent"]
    while p and not p.split(":", 1)[1].startswith("Ch."):
        p = next((x["parent"] for x in rows if x["id"] == p), "")
    return p.split(":", 1)[1] if p else ""
byid = {r["id"]: r for r in rows}
def article_of(r):
    while r and r["level"] != "article": r = byid.get(r["parent"])
    return r
def dates(r):
    art = article_of(r)
    if not art: return []
    num = art["id"].split(":", 1)[1].replace("Art.", ""); n = int(re.match(r"\d+", num)[0])
    full = r["id"].split(":", 1)[1]
    sec = art["parent"].split(":", 1)[1] if art["parent"] else ""
    ch = sec.split(".S")[0]
    if ch in ("Ch.I", "Ch.II"):
        if re.match(r"Art\.5\(1\)\((ba|bb)\)|Art\.5\((1a|1b)\)", full): return [("2026-12-02", "")]
        return [("2025-02-02", "")]
    if ch == "Ch.III" and sec.split(".S")[-1] in ("1", "2", "3"):
        if full.startswith("Art.6(5)"): return [("2026-08-02", "general rule")]
        return [("2027-12-02", "annex-iii systems"), ("2028-08-02", "annex-i systems")]
    if (ch == "Ch.III" and sec.split(".S")[-1] == "4") or ch in ("Ch.V", "Ch.VII", "Ch.XII") or n == 78:
        return [("2025-08-02", "")] if n != 101 else [("2026-08-02", "general rule")]
    if re.match(r"Art\.(10[2-9]|110)$", "Art." + str(n)) and ch == "Ch.XIII": return [("2026-07-27", "")]
    return [("2026-08-02", "general rule")]
for r in rows:
    if r["level"] in ("article", "paragraph", "point", "subpoint", "item"):
        for d, q in dates(r):
            facets.append(dict(provision_id=r["id"], facet="applies_from", value=d + (f" ({q})" if q else ""), source="derived from Art. 113 of the consolidated text"))

# ---------------------------------------------------------------- definitions (Article 3)
for r in rows:
    if r["parent"] == f"{FW}:Art.3" and r["level"] == "item":
        m = re.match(r"^[‘'’]([^’']+)[’']\s+(.*)$", r["source_text"])
        if m: definitions.append(dict(term=m[1], provision_id=r["id"], text=r["source_text"]))
        else: definitions.append(dict(term="", provision_id=r["id"], text=r["source_text"]))

with open(out_dir / "provisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
with open(out_dir / "facets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "facet", "value", "source"]); w.writeheader(); w.writerows(facets)
with open(out_dir / "definitions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["term", "provision_id", "text"]); w.writeheader(); w.writerows(definitions)
lv = {}
for r in rows: lv[r["level"]] = lv.get(r["level"], 0) + 1
print(len(rows), "rows;", lv, "| facets", len(facets), "| definitions", len(definitions))
