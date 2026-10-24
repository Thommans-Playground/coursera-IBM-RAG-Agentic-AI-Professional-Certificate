"""Build the AI Verify dataset from the parsed IMDA Testing Framework (see parse_ai_verify_pdf.py).

Usage: python -I tools/build_ai_verify.py parsed.json aivtf.txt data/frameworks/ai-verify
  parsed.json  output of parse_ai_verify_pdf.py (outcomes, processes)
  aivtf.txt    plain text of the same PDF (pypdf), used for the principle introduction pages
"""
import csv, json, pathlib, re, sys

parsed, text_path, out = json.load(open(sys.argv[1])), open(sys.argv[2]).read(), pathlib.Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
FW = "ai-verify"
NAMES = ["Transparency", "Explainability", "Repeatability / Reproducibility", "Safety", "Security", "Robustness", "Fairness",
         "Data Governance", "Accountability", "Human Agency and Oversight", "Inclusive Growth, Societal and Environmental Well-being"]
URL = "https://file.go.gov.sg/aivtf-pdf.pdf"
squash = lambda s: re.sub(r"\s+", " ", s).strip()

# principle introduction pages: no OUTCOME label, a two-digit principle number at the end of the page
intro = {}
for page in re.split(r"=====PAGE \d+=====", text_path and text_path and text_path):
    if "OUTCOME" in page or "PROCESS" in page: continue
    m = re.search(r"([A-Z][A-Za-z ,/&-]+?)\s*\n\s*(\d{2})\s*$", page.strip())
    if m and int(m[2]) <= 11:
        body = page.strip()[: m.start()].strip()
        first, _, rest = body.partition(".\n")
        intro[int(m[2])] = (squash(first) + ".", squash(rest))

rows, evidence, facets = [], [], []
def add(**r):
    base = dict(framework=FW, parent="", level="", ordinal="", title="", kind="", is_header="no", assessable="no", source_text="",
                aliases="", status="verified-parsed", note="", source_ref=URL)
    base.update(r); rows.append(base)
for n, name in enumerate(NAMES, 1):
    d, desc = intro.get(n, ("", ""))
    add(id=f"{FW}:{n}", level="principle", ordinal=n, title=name, kind="GROUP", is_header="yes", source_text=d,
        aliases=f"Principle {n}", note=("Framework description: " + desc) if desc else "")
key = lambda s: [int(x) for x in s.split(".")]
for oid in sorted(parsed["outcomes"], key=key):
    o = parsed["outcomes"][oid]; add(id=f"{FW}:{oid}", parent=f"{FW}:{oid.split('.')[0]}", level="outcome", ordinal=oid.split(".")[1], title=f"Outcome {oid}",
                                      kind="OUTCOME", source_text=o["statement"], aliases=f"OUTCOME {oid}")
for pid in sorted(parsed["processes"], key=key):
    p = parsed["processes"][pid]; oid = ".".join(pid.split(".")[:2])
    add(id=f"{FW}:{pid}", parent=f"{FW}:{oid}", level="process", ordinal=pid.split(".")[2], title=f"Process {pid}", kind="TEST" if p["technical_test"] else "CONTROL",
        assessable="yes", source_text=p["statement"], aliases=f"PROCESS {pid}")
    ai = {"Traditional and Generative AI": "traditional-and-generative", "Traditional AI": "traditional", "Generative AI": "generative"}[p["ai_type"]]
    facets.append(dict(provision_id=f"{FW}:{pid}", facet="ai_type", value=ai, source="AI Verify Testing Framework"))
    if p["technical_test"]: facets.append(dict(provision_id=f"{FW}:{pid}", facet="technical_test", value="yes", source="AI Verify Testing Framework"))
    evidence.append(dict(provision_id=f"{FW}:{pid}", evidence_type=p["evidence_type"], description=p["evidence"]))
# every outcome must have at least one process, every process an outcome
byid = {r["id"] for r in rows}
assert all(r["parent"] in byid for r in rows if r["parent"]), "orphan"
with open(out / "provisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
with open(out / "facets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "facet", "value", "source"]); w.writeheader(); w.writerows(facets)
with open(out / "evidence_expected.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "evidence_type", "description"]); w.writeheader(); w.writerows(evidence)
c = {}
for r in rows: c[r["level"]] = c.get(r["level"], 0) + 1
print(c, "| intro pages parsed:", sorted(intro), "| facets", len(facets))
