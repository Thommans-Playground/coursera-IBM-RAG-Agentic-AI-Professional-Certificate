# AI governance assistant: data

Structured data for four frameworks, a shared set of themes and the links between them, ready to load. Nothing here is a chatbot yet.

## Layout

```
data/
  frameworks/<framework>/   framework.yaml · provisions.csv · facets.csv · (evidence_expected.csv | definitions.csv)
  themes.csv                the 12 shared themes (formerly "canonical principles")
  links/                    theme_links.csv (theme -> provision) · official_nist_to_ai_verify_2023.csv
  verification/             row-by-row comparisons of the old workbook with the official sources
docs/verification-log.md    what was checked, against what, and what is still unchecked
tools/                      build scripts and the checks
```

## Status

| Framework | Kind | Rows | Source | Status |
|---|---|---:|---|---|
| `nist-ai-rmf` | risk framework | 95 | NIST AI 100-1 and the NIST Playbook | official text, two documents agree (5 rows noted) |
| `eu-ai-act` | law | 1,433 | Commission consolidated text, 27 Jul 2026 (with Digital Omnibus changes marked) | official reading text; not the Official Journal |
| `ai-verify` | testing framework | 211 | IMDA Testing Framework, 2025 edition | parsed from the official PDF |
| `iso-42001` | management system | 104 | the workbook only | **structure and titles only, unverified**; standard wording deliberately absent |

All of it is automated work that **no person has reviewed yet**.

## Run the checks

```
../.venv/bin/python -I tools/check_data.py data          # integrity: ids, parents, counts, links
../.venv/bin/python -I tools/resolve_links.py data       # re-check every theme link against the datasets
```

## Rebuild a dataset

Each `tools/build_*.py` has its usage in its docstring. NIST and EU read downloaded official pages; AI Verify needs `pdfplumber` (`uv run --no-project --with pdfplumber ...`); ISO reads the workbook with `openpyxl`.

## Things to know

- ISO/IEC 42001 is copyrighted. `source_text` is empty for it by design (`text_policy: STRUCTURE_ONLY`).
- The EU text is the Commission's consolidated reading text. Check anything that matters against EUR-Lex.
- The theme links come from the workbook's crosswalk and are theme-level. Their `support` column is empty until each link is graded; see `data/links/README.md`.
- The workbook itself was never modified. It is not needed to use the data, except to rebuild the ISO dataset.
