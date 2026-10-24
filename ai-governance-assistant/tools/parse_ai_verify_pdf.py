"""Parse the IMDA AI Verify Testing Framework PDF into outcomes and processes (JSON).

Source: https://file.go.gov.sg/aivtf-pdf.pdf  ("AI Verify Testing Framework for Traditional and Generative AI", IMDA, 2025)
Each page is a set of cards: an OUTCOME label with its statement, then PROCESS labels with the process wording (large type)
and the evidence type and description (small type). Cards are stacked, side by side, or both. This reads them by position
and font size.
Needs pdfplumber:  uv run --no-project --with pdfplumber python -I tools/parse_ai_verify_pdf.py aivtf.pdf out.json
"""
import json, re, sys
import pdfplumber

ID_O, ID_P = re.compile(r"^\d+\.\d+$"), re.compile(r"^\d+\.\d+\.\d+$")
TAG_WORDS = {"TRADITIONAL", "AND", "GENERATIVE", "AI"}
SKIP = {"Yes", "No", "N/A"}
group = lambda ws: [sorted(g, key=lambda w: w["x0"]) for _, g in sorted({round(w["top"] / 4): [] for w in ws}.items())] and None

def lines(ws):
    rows = {}
    for w in ws: rows.setdefault(round(w["top"] / 4), []).append(w)
    return [sorted(rows[k], key=lambda w: w["x0"]) for k in sorted(rows)]

def join(ws): return re.sub(r"\s+", " ", " ".join(w["text"] for w in ws)).strip()

outcomes, processes = {}, {}
pdf = pdfplumber.open(sys.argv[1])
for pno, page in enumerate(pdf.pages, 1):
    W = page.width
    words = page.extract_words(extra_attrs=["size"])
    labels = []
    for i, w in enumerate(words[:-1]):
        nx = words[i + 1]
        if w["text"] in ("OUTCOME", "PROCESS") and abs(nx["top"] - w["top"]) < 6 and nx["x0"] - w["x1"] < 30:
            if (w["text"] == "OUTCOME" and ID_O.match(nx["text"])) or (w["text"] == "PROCESS" and ID_P.match(nx["text"])):
                labels.append(dict(kind=w["text"][0], id=nx["text"], x0=w["x0"], top=w["top"]))
    if not labels: continue
    # horizontal bands: labels on (roughly) the same row sit side by side
    for lb in labels:
        row = sorted([o for o in labels if abs(o["top"] - lb["top"]) < 15], key=lambda o: o["x0"])
        k = row.index(lb)
        lb["xl"] = 0 if k == 0 else (row[k - 1]["x0"] + lb["x0"]) / 2
        lb["xr"] = W if k == len(row) - 1 else (lb["x0"] + row[k + 1]["x0"]) / 2
    stops = [w for w in words if w["text"] == "PROCESS" and False]
    check_lines = [w for w in words if w["text"] == "CHECKS"]       # "PROCESS CHECKS COMPLETED ELABORATION" closes a process card
    for lb in labels:
        band = [w for w in words if lb["xl"] <= w["x0"] < lb["xr"]]
        below = [o for o in labels if o["xl"] < lb["xr"] and o["xr"] > lb["xl"] and o["top"] > lb["top"] + 10]
        y_end = min([o["top"] for o in below], default=page.height)
        if lb["kind"] == "P":
            y_end = min([y_end] + [c["top"] for c in check_lines if c["top"] > lb["top"] and lb["xl"] <= c["x0"] < lb["xr"]])
        zone = [w for w in band if lb["top"] + 8 < w["top"] < y_end]
        if lb["kind"] == "O":
            st = join([w for ln in lines(zone) for w in ln if 21 <= w["size"] < 30])
            outcomes[lb["id"]] = dict(id=lb["id"], statement=st, page=pno)
            continue
        tag = join([w for w in band if abs(w["top"] - lb["top"]) < 40 and w["text"] in TAG_WORDS and w["size"] < 30 and w["top"] >= lb["top"] - 5])
        tag = {"TRADITIONAL AND GENERATIVE AI": "Traditional and Generative AI", "TRADITIONAL AI": "Traditional AI", "GENERATIVE AI": "Generative AI"}.get(tag, tag)
        header = [w for w in zone if w["text"] in TAG_WORDS and w["size"] < 30 and w["top"] < lb["top"] + 45]
        rest = [w for w in zone if w not in header and w["text"] not in SKIP]
        ev_label = next((w for w in sorted(rest, key=lambda w: w["top"]) if w["text"] in ("EVIDENCE", "METRICS")), None)
        metrics_card = ev_label is not None and ev_label["text"] == "METRICS"     # technical-test cards say METRICS instead of EVIDENCE
        rest = [w for w in rest if w is not ev_label]
        if ev_label is None: stm_words, ev_words = rest, []
        elif ev_label["x0"] > 400:                      # side by side: statement on the left, evidence on the right
            stm_words = [w for w in rest if w["x0"] < ev_label["x0"] - 15]; ev_words = [w for w in rest if w["x0"] >= ev_label["x0"] - 15]
        else:                                           # stacked: statement above the EVIDENCE label, evidence below
            stm_words = [w for w in rest if w["top"] < ev_label["top"] - 3]; ev_words = [w for w in rest if w["top"] >= ev_label["top"] - 3]
        statement = join([w for ln in lines(stm_words) for w in ln])
        ev = [ln for ln in lines(ev_words) if join(ln)]
        # evidence type: the first line(s). Side-by-side cards set the type a point larger than the description; stacked cards use one size
        if ev:
            sizes = [round(ln[0]["size"]) for ln in ev]
            n = 1
            if len(ev) > 1 and sizes[0] > sizes[1]:
                while n < len(ev) and sizes[n] == sizes[0]: n += 1
            etype, edesc = join([w for ln in ev[:n] for w in ln]), join([w for ln in ev[n:] for w in ln])
        else: etype = edesc = ""
        if metrics_card: etype, edesc = "Technical test results", join([w for ln in ev for w in ln])
        processes[lb["id"]] = dict(id=lb["id"], statement=statement, technical_test=metrics_card, ai_type=tag, evidence_type=etype, evidence=edesc, page=pno)
json.dump(dict(outcomes=outcomes, processes=processes), open(sys.argv[2], "w"), indent=1)
print(len(outcomes), "outcomes;", len(processes), "processes")
