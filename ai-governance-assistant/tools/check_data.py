"""Check that the datasets are internally consistent. Exit code 1 if any check fails.

Usage: python -I tools/check_data.py data
Checks: required columns; ids unique and prefixed with the framework; every parent exists; headers are not assessable and assessable rows
are leaves; counts in framework.yaml match; facets and evidence point at real rows; the ISO text policy holds (no standard wording);
theme links and official links point at rows that exist when they say they do.
"""
import csv, pathlib, re, sys
import yaml

data = pathlib.Path(sys.argv[1])
CORE = ["id", "framework", "parent", "level", "ordinal", "title", "kind", "is_header", "assessable", "source_text", "aliases", "status", "note", "source_ref"]
fails, infos = [], []
def fail(msg): fails.append(msg)

prov, by_fw = {}, {}
for d in sorted((data / "frameworks").iterdir()):
    if not d.is_dir(): continue
    fw = d.name; meta = yaml.safe_load(open(d / "framework.yaml")); rows = list(csv.DictReader(open(d / "provisions.csv")))
    missing = [c for c in CORE if c not in rows[0]]
    if missing: fail(f"{fw}: missing columns {missing}")
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)): fail(f"{fw}: duplicate ids {[i for i in set(ids) if ids.count(i) > 1][:5]}")
    bad_prefix = [i for i in ids if not i.startswith(fw + ":")]
    if bad_prefix: fail(f"{fw}: ids without the framework prefix {bad_prefix[:3]}")
    idset = set(ids); kids = {}
    for r in rows: kids.setdefault(r["parent"], []).append(r["id"])
    orphans = [r["id"] for r in rows if r["parent"] and r["parent"] not in idset]
    if orphans: fail(f"{fw}: parents missing for {orphans[:5]}")
    for r in rows:
        if r["is_header"] == "yes" and r["assessable"] == "yes": fail(f"{fw}: header marked assessable: {r['id']}")
        if r["assessable"] == "yes" and kids.get(r["id"]): fail(f"{fw}: assessable row has children: {r['id']}")
    lv = {}
    for r in rows: lv[r["level"]] = lv.get(r["level"], 0) + 1
    for k, v in (meta.get("counts") or {}).items():
        if lv.get(k) != v: fail(f"{fw}: framework.yaml says {v} {k}, dataset has {lv.get(k)}")
    if meta.get("text_policy") == "STRUCTURE_ONLY" and any(r["source_text"] for r in rows): fail(f"{fw}: STRUCTURE_ONLY but source_text is filled")
    for fn in ("facets.csv", "evidence_expected.csv"):
        p = d / fn
        if p.exists():
            bad = [r["provision_id"] for r in csv.DictReader(open(p)) if r["provision_id"] not in idset]
            if bad: fail(f"{fw}/{fn}: rows point at missing provisions {bad[:3]}")
    for r in rows: prov[r["id"]] = r
    by_fw[fw] = (len(rows), sum(1 for r in rows if r["assessable"] == "yes"), lv)

themes = {r["theme_id"] for r in csv.DictReader(open(data / "themes.csv"))}
links = list(csv.DictReader(open(data / "links" / "theme_links.csv")))
for r in links:
    if r["theme_id"] not in themes: fail(f"theme_links: unknown theme {r['theme_id']}")
    if r["resolution"] in ("exact", "group") and r["provision_id"] not in prov: fail(f"theme_links: {r['provision_id']} says {r['resolution']} but is not in the data")
    if r["resolution"] in ("unresolved",) and r["provision_id"] in prov: fail(f"theme_links: {r['provision_id']} says unresolved but exists")
official = data / "links" / "official_nist_to_ai_verify_2023.csv"
if official.exists():
    for r in csv.DictReader(open(official)):
        if r["from_id"] not in prov: fail(f"official links: from {r['from_id']} missing")
        if r["resolution_2025"] == "exact" and r["to_id"] not in prov: fail(f"official links: to {r['to_id']} says exact but missing")

unres = [(r["theme_id"], r["provision_id"]) for r in links if r["resolution"] == "unresolved"]
print(f"{'framework':14}{'rows':>6}{'assessable':>12}   levels")
for fw, (n, a, lv) in by_fw.items(): print(f"{fw:14}{n:>6}{a:>12}   {lv}")
print(f"\nthemes {len(themes)} | theme links {len(links)} | unresolved links {len(unres)}: {unres}")
print("\nFAILED:" if fails else "\nAll checks passed.")
for f in fails: print(" -", f)
sys.exit(1 if fails else 0)
