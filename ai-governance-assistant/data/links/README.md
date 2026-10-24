# Theme links

`theme_links.csv` is the standardised form of the `Crosswalk` sheet in `Open AIaaS Framework.xlsx`: one row per link from a **Theme** to a **Provision**. `theme_links_wide.tsv` is the same data, one row per theme, for pasting back into a spreadsheet. `../themes.csv` holds the 12 themes (formerly "canonical principles", `CP-01` to `CP-12`).

Generated once on 2026-10-24 from the workbook, which was not changed. The generating script was not kept, so from now on **these files are the source** and the workbook's Crosswalk sheet is the old version.

| Column | Meaning |
|---|---|
| `theme_id` | Theme the link hangs from |
| `framework` | `ai-verify`, `nist-ai-rmf`, `eu-ai-act` or `iso-42001` |
| `provision_id` | `<framework>:<official citation>`, e.g. `eu-ai-act:Art.15(3)`, `iso-42001:A.6.2.4`, `ai-verify:7.2.1`. Empty when the source states there is no counterpart |
| `link_to` | What the link points at: principle, process, subcategory, article, provision, control, clause, annex-item or none |
| `basis` | `theme-derived` (same shared theme, indicative) or `stated-in-source` (the sheet says there is no counterpart). Other bases come later: official, reviewed, suggested |
| `support` | Left empty on purpose: nobody has graded these links yet. `none` where the source says there is no counterpart |
| `reviewed` | `no` for every row |
| `resolution` | Does `provision_id` exist in the finished datasets under `../frameworks/`? `exact`, `group` (a heading or aggregate row whose children exist), `via-parent` (an Annex C item inside the single row `C.2`), `unresolved`, or `n/a`. Re-run `tools/resolve_links.py data` after changing any dataset |
| `resolution_note` | Detail, e.g. how many provisions are in the group |
| `verification` | Set only where the id was checked: `text-checked-ok`, `wrong-paragraph`, `provision-deleted`, `check` (EU AI Act paragraphs); `version-drift` (an AI Verify id that exists only in the 2023 numbering); `not-in-framework` (an AI Verify id that exists in neither edition). Empty means not checked |
| `suggested_provision_id` | Where the id looks wrong, the id that matches the description. A suggestion for a person to confirm, not a correction applied |
| `verification_note` | What the official text says |
| `raw_ref` | The text exactly as written in the sheet |
| `legacy_rating` | The old FULL / PARTIAL / WEAK / GAP for this theme and framework. It means "same topic", not a support level, so it is kept for reference only |

## Id normalisation

- EU AI Act: official citation style, `Art.9(2)(a)`. The sheet's `Art.9.2` becomes `Art.9(2)`, and `Art.5(a)` becomes `Art.5(1)(a)`.
- ISO 42001: clauses are bare (`5.3`), annex items keep their letter (`A.6.2.4`, `B.9.3`, `C.2.9`).
- AI Verify: no `P` prefix; a principle is `ai-verify:7`, an outcome `7.1`, a process `7.1.1`.
- NIST AI RMF: unchanged (`GV-1.4`, `MP-5.1`, `MS-2.8`, `MG-1.1`).

## Verification so far

Of the 8 EU paragraph-level references, 4 were checked and are fine, 2 point at the wrong paragraph (`Art.15(3)`, `Art.10(2)`), 1 points at a provision the Digital Omnibus deleted (`Art.10(5)`), and 1 needs a decision (`Art.26(7)`). See `../verification/`. No other framework's links have been checked against official text yet, except that all NIST ids exist in `../frameworks/nist-ai-rmf/`.

## Known problems

- 11 AI Verify ids are not in the 2025 edition. Six of them (1.2.4, 3.14.1, 4.5.4, 7.4.2, 10.1.2, 10.2.3) are named in the official October 2023 NIST/IMDA crosswalk, which uses the 2023 numbering (marked `version-drift`). The other five (1.2.2, 1.2.3, 1.4.2, 3.13.1, 4.5.3) are in neither edition's numbering as far as can be seen (`not-in-framework`; they may sit inside ranges in the 2023 crosswalk).
- `iso-42001:B.9.3` has no row (the workbook has one summary row for Annex B).
- 5 ISO links to `C.2.x` resolve only to the single row `C.2`.
- The links are theme-level and `support` is empty until each link is graded.

## Official links

`official_nist_to_ai_verify_2023.csv` is a separate file: the NIST AI RMF categories mapped to AI Verify by NIST and IMDA on 12 October 2023 (basis `official`). It uses the 2023 numbering of AI Verify, so a process id there can name a different process in the 2025 edition. Treat the principle-level rows as reliable and the process-level rows as needing review.
