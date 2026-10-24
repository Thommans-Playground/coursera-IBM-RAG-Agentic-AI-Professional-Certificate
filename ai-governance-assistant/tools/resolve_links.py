"""Re-check every theme link against the framework datasets and rewrite its resolution columns.

Usage: python -I tools/resolve_links.py data
Resolution: exact (the id is an assessable row), group (a heading or aggregate row that has children), via-parent (only an ancestor exists;
the link points at an item inside it), unresolved (nothing matches), n/a (the source states there is no counterpart).
Also marks AI Verify ids that exist only in the 2023 numbering (verification = version-drift).
"""
import csv, pathlib, re, sys

data = pathlib.Path(sys.argv[1])
prov = {}
for d in (data / "frameworks").iterdir():
    if (d / "provisions.csv").exists():
        for r in csv.DictReader(open(d / "provisions.csv")): prov[r["id"]] = r
children = {}
for r in prov.values(): children.setdefault(r["parent"], []).append(r["id"])

def ancestors(pid):
    fw, local = pid.split(":", 1)
    cur = local
    while True:
        m = re.match(r"^(.*)(\([^()]*\)(?:\[\d+\])?|\.[^.()]+)$", cur)
        if not m or not m[1]: return
        cur = m[1]; yield f"{fw}:{cur}"

old_2023 = set()
f23 = data / "links" / "official_nist_to_ai_verify_2023.csv"
if f23.exists():
    old_2023 = {r["to_id"] for r in csv.DictReader(open(f23)) if r["resolution_2025"] == "not-in-2025-edition" and r["to_id"]}

p = data / "links" / "theme_links.csv"
rows = list(csv.DictReader(open(p)))
counts = {}
for r in rows:
    pid = r["provision_id"]
    if not pid: res, note = "n/a", r["resolution_note"] if r["basis"] == "stated-in-source" else ""
    elif pid in prov:
        has_kids = bool(children.get(pid))
        res, note = ("group", f"{len(children[pid])} children in dataset") if (has_kids and prov[pid]["assessable"] != "yes") else ("exact", "")
    else:
        anc = next((a for a in ancestors(pid) if a in prov), None)
        res, note = ("via-parent", f"item inside {anc.split(':',1)[1]}") if anc and prov[anc]["level"] == "annex-item" else ("unresolved", "no matching row in the dataset")
    if "recitals only" in r["resolution_note"] and pid: note = (note + "; recitals only, not the articles").strip("; ")
    r["resolution"], r["resolution_note"] = res, note
    if r["framework"] == "ai-verify" and res == "unresolved":
        if pid in old_2023:
            r["verification"], r["verification_note"] = "version-drift", "id exists only in the 2023 numbering of the AI Verify framework (October 2023 NIST/IMDA crosswalk); not in the 2025 edition"
        else:
            r["verification"], r["verification_note"] = "not-in-framework", "no such process or outcome in the 2025 edition, and not named individually in the 2023 NIST/IMDA crosswalk either (possibly inside a range there)"
    counts[(r["framework"], res)] = counts.get((r["framework"], res), 0) + 1
with open(p, "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
for k in sorted(counts): print(k, counts[k])
