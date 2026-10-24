"""Import the official NIST / IMDA crosswalk of 12 October 2023 (NIST AI RMF 1.0 categories -> AI Verify) as links.

Source: https://airc.nist.gov/docs/NIST_AI_RMF_to_AI_Verify_Crosswalk.pdf (3 pages; text extracted with pypdf)
Usage: python -I tools/build_official_links.py crosswalk.txt data/links/official_nist_to_ai_verify_2023.csv data/frameworks

It uses the 2023 numbering of the AI Verify Testing Framework, which differs from the 2025 edition in data/frameworks/ai-verify.
Each reference is stored as written (raw_ref), as a canonical id, and checked against the 2025 dataset. A principle-level row per
category is also written, because principle numbers are stable across editions while process numbers are not.
"""
import csv, pathlib, re, sys

text, out, fw_dir = open(sys.argv[1]).read(), sys.argv[2], pathlib.Path(sys.argv[3])
text = re.sub(r"=====PAGE \d+=====", " ", text)
text = re.sub(r"Crosswalk\s+AI RMF \(1\.0\) and AI Verify\s+\d+", " ", text)
text = re.sub(r"\s+", " ", text)
PRINC = [("Human Agency (?:and|&) Oversight", 10, "Human Agency and Oversight"), ("Inclusive growth, Societal (?:and|&) Environmental Well-being", 11, "Inclusive Growth, Societal and Environmental Well-being"),
         ("Organisational Considerations", 12, "Organisational Considerations (2023 edition only)"), ("Data Governance", 8, "Data Governance"), ("Transparency", 1, "Transparency"),
         ("Explainability", 2, "Explainability"), ("Reproducibility", 3, "Reproducibility"), ("Safety", 4, "Safety"), ("Security", 5, "Security"), ("Robustness", 6, "Robustness"),
         ("Fairness", 7, "Fairness"), ("Accountability", 9, "Accountability")]
pname = re.compile("(" + "|".join(p[0] for p in PRINC) + ")", re.I)
num = r"\d+(?:\.\d+){0,2}"
refs_re = re.compile(rf"({num}(?:\s*[-–]\s*{num})?)")
PFX = {"GOVERN": "GV", "MAP": "MP", "MEASURE": "MS", "MANAGE": "MG"}
def principle_no(name):
    for pat, n, _ in PRINC:
        if re.fullmatch(pat, name, re.I): return n
cats = list(re.finditer(r"(GOVERN|MAP|MEASURE|MANAGE) (\d):", text))
ai25 = {r["id"] for r in csv.DictReader(open(fw_dir / "ai-verify" / "provisions.csv"))}
nist = {r["id"] for r in csv.DictReader(open(fw_dir / "nist-ai-rmf" / "provisions.csv"))}
rows = []
for i, c in enumerate(cats):
    body = text[c.end(): cats[i + 1].start() if i + 1 < len(cats) else len(text)]
    cid = f"nist-ai-rmf:{PFX[c[1]]}-{c[2]}"
    assert cid in nist, cid
    marks = list(pname.finditer(body))
    for j, m in enumerate(marks):
        seg = body[m.end(): marks[j + 1].start() if j + 1 < len(marks) else len(body)]
        n = principle_no(m[0])
        # references run until the text stops looking like numbers, commas and ranges
        refs = re.match(rf"\s*((?:{num}(?:\s*[-–]\s*{num})?\s*,?\s*)+)", seg)
        raw_list = [x.strip() for x in re.split(r",", refs[1]) if x.strip()] if refs else []
        rows.append(dict(from_id=cid, to_id=f"ai-verify:{n}" if n <= 11 else "", granularity="principle", raw_ref=m[0], principle_no=n, numbering="principle number (stable across editions)",
                         resolution_2025=("exact" if f"ai-verify:{n}" in ai25 else "not-in-2025-edition")))
        for raw in raw_list:
            parts = [p.strip() for p in re.split(r"[-–]", raw)]
            depth = parts[0].count(".") + 1
            gran = {1: "principle", 2: "outcome", 3: "process"}.get(depth, "?") + (" range" if len(parts) > 1 else "")
            if len(parts) == 1: tid = f"ai-verify:{parts[0]}" if n <= 11 else ""
            else: tid = ""
            rows.append(dict(from_id=cid, to_id=tid, granularity=gran, raw_ref=f"{m[0]} {raw}", principle_no=n, numbering="AI Verify 2023 numbering",
                             resolution_2025=("n/a" if not tid else ("exact" if tid in ai25 else "not-in-2025-edition"))))
for r in rows:
    r.update(basis="official", source="NIST/IMDA crosswalk, 12 Oct 2023", reviewed="no")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, ["from_id", "to_id", "granularity", "raw_ref", "principle_no", "numbering", "resolution_2025", "basis", "source", "reviewed"])
    w.writeheader(); w.writerows(rows)
import collections
print(len(cats), "categories;", len(rows), "rows;", dict(collections.Counter(r["granularity"] for r in rows)))
print("resolution against the 2025 edition:", dict(collections.Counter(r["resolution_2025"] for r in rows)))
