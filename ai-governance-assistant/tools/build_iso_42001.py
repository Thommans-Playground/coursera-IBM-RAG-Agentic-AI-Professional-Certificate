"""Build the ISO/IEC 42001:2023 structure dataset from the project workbook (structure and titles only).

ISO/IEC 42001 is copyrighted and paywalled. This stores ids, titles and your own "evidence expected" notes. It does NOT store the
standard's requirement or control wording (source_text is left empty on purpose). Titles come from the workbook and are not
verified against the standard.

Usage: uv run --no-project --with openpyxl python -I tools/build_iso_42001.py "../Open AIaaS Framework.xlsx" data/frameworks/iso-42001
"""
import csv, pathlib, re, sys
import openpyxl

wb_path, out = sys.argv[1], pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
FW = "iso-42001"
ws = openpyxl.load_workbook(wb_path, data_only=True)["5_ISO42001"]
SRC = "ISO/IEC 42001:2023 (structure per workbook; not verified)"
TOPICS = {  # Annex A table A.1 topics (names from general knowledge; secondary sources confirm A.2 to A.4)
    "A.2": "Policies related to AI", "A.3": "Internal organization", "A.4": "Resources for AI systems", "A.5": "Assessing impacts of AI systems",
    "A.6": "AI system life cycle", "A.7": "Data for AI systems", "A.8": "Information for interested parties of AI systems",
    "A.9": "Use of AI systems", "A.10": "Third-party and customer relationships"}
GROUPS = {"A.6.1": "Management guidance for AI system development", "A.6.2": "AI system life cycle processes"}

rows, evidence, facets, titles = [], [], [], {}
def add(id_, parent, level, ordinal, title, kind, header, assessable, status="unverified-title", note="", aliases=""):
    rows.append(dict(id=f"{FW}:{id_}", framework=FW, parent=f"{FW}:{parent}" if parent else "", level=level, ordinal=ordinal, title=title, kind=kind,
                     is_header="yes" if header else "no", assessable="yes" if assessable else "no", source_text="", aliases=aliases, status=status, note=note, source_ref=SRC))
    titles[id_] = title

section_titles = {}          # "Clause 4" -> "Context of the organization", "Annex A" -> ...
src_rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    if r[0] and not r[1]:
        m = re.match(r"^(Clause \d+|Annex [A-D]|Clauses 1–3)\s*(.*)$", str(r[0]).strip())
        if m: section_titles[m[1]] = re.sub(r"\s*\((NORMATIVE|Informative|Informative)[^)]*\)\s*$", "", m[2]).strip()
    if r[1]: src_rows.append(r)

def part(i):
    return i

# headers: clauses and annexes
for n in range(1, 11):
    t = section_titles.get(f"Clause {n}", "")
    if n <= 3: t = {1: "Scope", 2: "Normative references", 3: "Terms and definitions"}[n]
    add(str(n), "", "clause", n, t, "REQUIREMENT", header=n > 3, assessable=False, aliases=f"Clause {n}")
for a in "ABCD":
    add(a, "", "annex", a, section_titles.get(f"Annex {a}", ""), "GUIDANCE" if a != "A" else "CONTROL", header=True, assessable=False, aliases=f"Annex {a}")
for t, name in TOPICS.items(): add(t, "A", "topic", t.split(".")[1], name, "GROUP", header=True, assessable=False)
for g, name in GROUPS.items(): add(g, "A.6", "group", g.split(".")[2], name, "GROUP", header=True, assessable=False)

def ensure_subclause(i):
    """clause 6.1 exists only as a parent of 6.1.1, 6.1.2, 6.1.3: derive its title from its children"""
    if i in titles: return
    kids = [str(r[1]).strip() for r in src_rows if str(r[1]).strip().startswith(i + ".")]
    first = next((str(r[2]) for r in src_rows if str(r[1]).strip() == kids[0]), "") if kids else ""
    add(i, i.split(".")[0], "subclause", i.split(".")[1], first.split(" — ")[0].strip(), "REQUIREMENT", header=True, assessable=False, aliases=f"Clause {i}")

for r in src_rows:
    raw, title, typ, ev = str(r[1]).strip(), str(r[2] or "").strip(), str(r[4] or "").strip(), str(r[5] or "").strip()
    if raw in ("1.0", "2.0", "3.0"):
        n = raw[0]; typ_note = "definitional clause"; rows_for = n
        evidence.append(dict(provision_id=f"{FW}:{n}", evidence_expected=ev, source="workbook")); facets.append(dict(provision_id=f"{FW}:{n}", facet="normative", value="definitional", source="workbook"))
        continue
    if re.fullmatch(r"\d+\.\d+", raw):
        add(raw, raw.split(".")[0], "subclause", raw.split(".")[1], title, "REQUIREMENT", header=False, assessable=True, aliases=f"Clause {raw}"); pid = raw
    elif re.fullmatch(r"\d+\.\d+\.\d+", raw):
        ensure_subclause(".".join(raw.split(".")[:2]))
        add(raw, ".".join(raw.split(".")[:2]), "subsubclause", raw.split(".")[2], title, "REQUIREMENT", header=False, assessable=True, aliases=f"Clause {raw}"); pid = raw
    elif raw.startswith("A."):
        parent = ".".join(raw.split(".")[:3 if raw.startswith("A.6.") else 2]) if raw.startswith("A.6.") else ".".join(raw.split(".")[:2])
        add(raw, parent, "control", raw.split(".")[-1], title, "CONTROL", header=False, assessable=True, aliases=f"Annex {raw}"); pid = raw
    elif raw[0] in "BCD":
        add(raw, raw[0], "annex-item", raw.split(".")[-1], title, "GUIDANCE", header=False, assessable=False, aliases=f"Annex {raw}"); pid = raw
    else:
        continue
    facets.append(dict(provision_id=f"{FW}:{pid}", facet="normative", value={"N": "normative", "I": "informative", "D": "definitional"}.get(typ, typ), source="workbook"))
    evidence.append(dict(provision_id=f"{FW}:{pid}", evidence_expected=ev, source="workbook"))
# clause 1-3 are leaves: make them assessable=no and not headers
for r in rows:
    if r["id"] in (f"{FW}:1", f"{FW}:2", f"{FW}:3"): r["is_header"] = r["assessable"] = "no"
byid = {r["id"] for r in rows}
assert all(r["parent"] in byid for r in rows if r["parent"]), [r["id"] for r in rows if r["parent"] and r["parent"] not in byid]
with open(out / "provisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
with open(out / "facets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "facet", "value", "source"]); w.writeheader(); w.writerows(facets)
with open(out / "evidence_expected.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "evidence_expected", "source"]); w.writeheader(); w.writerows(evidence)
lv = {}
for r in rows: lv[r["level"]] = lv.get(r["level"], 0) + 1
print(lv, "| controls:", sum(1 for r in rows if r["level"] == "control"))
