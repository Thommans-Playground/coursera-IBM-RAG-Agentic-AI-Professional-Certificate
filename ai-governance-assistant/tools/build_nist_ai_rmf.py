"""Build the NIST AI RMF 1.0 dataset from NIST's own files.

Inputs (both from NIST, US government works):
  playbook.json   https://airc.nist.gov/docs/playbook.json
  ai-100-1.txt    text of https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf (extract with pypdf)

Usage: python -I tools/build_nist_ai_rmf.py playbook.json ai-100-1.txt data/frameworks/nist-ai-rmf
AI 100-1 is the framework text and wins. Subcategory text is taken from the Playbook (clean, no PDF
hyphenation damage) when it agrees with AI 100-1 (similarity 0.95 or more). Where the two differ, the
AI 100-1 wording is stored, status is "verified-variant", and the Playbook wording goes in `note`.
"""
import ast, csv, difflib, json, pathlib, re, sys

playbook_path, pdf_text_path, out_dir = sys.argv[1:4]
out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
FUNCS = [("GOVERN", "GV"), ("MAP", "MP"), ("MEASURE", "MS"), ("MANAGE", "MG")]
PRE = dict(FUNCS)
norm = lambda s: re.sub(r"[^a-z0-9]+", "", s.lower())
squash = lambda s: re.sub(r"\s+", " ", s).strip()

# ---- Playbook: subcategories plus NIST's own tags
play = {}
for e in json.load(open(playbook_path)):
    m = re.fullmatch(r"(GOVERN|MAP|MEASURE|MANAGE) (\d+)\.(\d+)", e["title"].strip())
    if m:
        play[(m[1], int(m[2]), int(m[3]))] = e

# ---- PDF text: category statements, and a second copy of the subcategory statements
txt = open(pdf_text_path).read()
entry = re.compile(r"^(GOVERN|MAP|MEASURE|MANAGE) (\d+)(?:\.(\d+))?:\s*(.*?)(?=^(?:GOVERN|MAP|MEASURE|MANAGE) \d+(?:\.\d+)?:|^Table \d|\Z)", re.S | re.M)
cats, pdf_subs = {}, {}
for m in entry.finditer(txt):
    t = squash(m[4]); t = squash(re.split(r"Categories Subcategories|NIST AI 100-1| Page \d+", t)[0])
    if m[3] is None:
        key = (m[1], int(m[2]));  cats[key] = max(cats.get(key, ""), t, key=len)
    else:
        key = (m[1], int(m[2]), int(m[3]));  pdf_subs[key] = max(pdf_subs.get(key, ""), t, key=len)
# GOVERN 4's statement continues after a page break in the PDF ("Table 1 ... (Continued)")
if cats[("GOVERN", 4)].endswith("committed to a culture"):
    cats[("GOVERN", 4)] += " that considers and communicates AI risk."
assert len(cats) == 19 and len(play) == 72, (len(cats), len(play))

# ---- provisions
HYPHEN_REPAIRS = {"contextspecific": "context-specific"}   # lost at a line break in the PDF text
rows, facets, review = [], [], []
def pid(*a):
    f, c, s = (list(a) + [None, None])[:3]
    return f"nist-ai-rmf:{PRE[f]}" + (f"-{c}" if c else "") + (f".{s}" if s else "")
for i, (fn, p) in enumerate(FUNCS, 1):
    rows.append(dict(id=pid(fn), framework="nist-ai-rmf", parent="", level="function", ordinal=i, title=fn, kind="GROUP",
                     is_header="yes", assessable="no", source_text="", aliases=fn, status="verified", note="",
                     source_ref="NIST AI 100-1, Section 5"))
    for c in sorted({k[1] for k in cats if k[0] == fn}):
        rows.append(dict(id=pid(fn, c), framework="nist-ai-rmf", parent=pid(fn), level="category", ordinal=c, title=f"{fn} {c}",
                         kind="OUTCOME", is_header="no", assessable="no", source_text=cats[(fn, c)], aliases=f"{fn} {c}",
                         status="verified", note="", source_ref=f"NIST AI 100-1, Table {[x[0] for x in FUNCS].index(fn)+1}"))
        for s in sorted({k[2] for k in play if k[0] == fn and k[1] == c}):
            e = play[(fn, c, s)]
            text = squash(e["description"]); other = pdf_subs.get((fn, c, s), "")
            sim = difflib.SequenceMatcher(None, norm(text), norm(other)).ratio() if other else 0.0
            note = ""
            if sim >= 0.95: status = "verified"
            else:
                status = "verified-variant"; note = "Playbook wording: " + text
                text = other
                text = re.sub(r"(?<=[a-z])- (?=[a-z])", "", text)         # word split at a line break: "docu- mented"
                for bad, good in HYPHEN_REPAIRS.items(): text = text.replace(bad, good)
            rows.append(dict(id=pid(fn, c, s), framework="nist-ai-rmf", parent=pid(fn, c), level="subcategory", ordinal=s,
                             title=f"{fn} {c}.{s}", kind="OUTCOME", is_header="no", assessable="yes", source_text=text,
                             aliases=f"{fn} {c}.{s}", status=status, note=note, source_ref="NIST AI RMF Playbook (airc.nist.gov); cross-checked with NIST AI 100-1"))
            review.append((pid(fn, c, s), round(sim, 3), status))
            for facet, key in (("ai_actor", "AI Actors"), ("topic", "Topic")):
                raw = e.get(key)
                vals = ast.literal_eval(raw) if isinstance(raw, str) else (raw or [])
                for v in vals: facets.append(dict(provision_id=pid(fn, c, s), facet=facet, value=v, source="NIST AI RMF Playbook"))

with open(out / "provisions.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
with open(out / "facets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, ["provision_id", "facet", "value", "source"]); w.writeheader(); w.writerows(facets)
n = lambda lvl: sum(1 for r in rows if r["level"] == lvl)
print(f"functions {n('function')}, categories {n('category')}, subcategories {n('subcategory')}, facets {len(facets)}")
print("status counts:", {s: sum(1 for _, _, x in review if x == s) for s in ("verified", "verified-variant")})
print("verified-variant (Playbook and AI 100-1 word it differently):", [(a.split(':')[1], b) for a, b, c in review if c != "verified"])
