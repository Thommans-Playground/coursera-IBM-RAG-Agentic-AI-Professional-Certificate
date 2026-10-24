# Verification of the framework data

Each file compares one framework sheet in `Open AIaaS Framework.xlsx` with the official source, row by row.

| File | Source compared against | Status |
|---|---|---|
| `nist-ai-rmf-1.0-vs-sheet.csv` | NIST AI 100-1 (AI RMF 1.0), Section 5 tables, text extracted from the official PDF https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf | done |
| `eu-ai-act-vs-sheet.csv` | Consolidated AI Act as at 27 July 2026, published by the European Commission's AI Act Service Desk (https://ai-act-service-desk.ec.europa.eu), which states it is based on the EUR-Lex consolidated version and marks Digital Omnibus changes | done for the 72 sheet rows; all 133 article and annex pages retrieved |
| ISO/IEC 42001 | the standard is paywalled | **not verifiable here**. Structure checked only against the commonly cited shape (38 controls, 9 topics) |
| `ai-verify-vs-sheet.csv` | AI Verify Testing Framework for Traditional and Generative AI (IMDA, 2025), https://file.go.gov.sg/aivtf-pdf.pdf | done for the 112 processes and 88 outcomes |

## NIST columns

`similarity_to_official` is a text-similarity score from 0 to 1 between the sheet text and the official subcategory text. `best_match_id` is the official subcategory whose text is closest to the sheet text, which shows when the right words sit under the wrong id.

`status` is a **heuristic, not a verdict**:
- `matches`: similarity of 0.85 or more
- `paraphrase-or-partial`: 0.6 to 0.85, usually shortened or reworded
- `differs`: below 0.6. Some of these are only reworded (for example MP-1.1) and some are a different statement (for example MP-2.1). A person has to look at each one.
- `text-of-<id>`: the sheet text is the text of another subcategory
- `missing-from-sheet`: the official subcategory has no row

Limits: the PDF text had page-break debris, hyphenation and ligature differences that lower similarity scores, and NIST's wording was not compared to the Playbook JSON, only to the AI RMF 1.0 document itself.


## EU AI Act columns

`status`: `ok` (the sheet's id holds the matching text), `renumbered` (the text is in the official text under `best_id`, not under the sheet's id), `reworded` (right place, much shorter or different wording), `no-match` (the matcher found no good match; a person must look. Some are only paraphrases, for example a summary of a long list), `deleted-by-omnibus` (the provision no longer exists in the consolidated text).

`own_cov` and `best_cov` are the share of the sheet text's content words found in the official text at the sheet's own id and at the best-matching id. Heuristic scores, not verdicts.

`expected_applies_from` is derived from Article 113 of the consolidated text by chapter. `sheet_deadline` is what the sheet says. Rows where they differ were written before the Digital Omnibus.

Limits: this is the Commission's consolidated reading text, which is not the authentic legal text (that is the Official Journal). Check anything that matters against EUR-Lex.

## AI Verify columns

`status`: `sheet-condensed` (the sheet's text uses most of the same words as the official process text but is a shorter paraphrase) or `sheet-differs` (under 60% of the sheet's key words appear in the official text: the sheet describes something different. Ten rows: 5.8.1 to 5.12.1, 7.6.1, 7.9.1, 8.3.1, 9.9.1, 10.3.1). `word_coverage` is the share of the sheet text's content words found in the official text. Only 5 of 112 sheet texts are verbatim; the sheet is a paraphrase throughout, so the dataset in `data/frameworks/ai-verify` is built from the official PDF instead.

The process ids match exactly (112 of 112), and the applicability tag (traditional / generative / both) agrees on all 112. The sheet's Outcome ID column is stored as numbers, so 3.10, 4.10, 5.10, 7.10 and 9.10 collapsed into 3.1, 4.1, 5.1, 7.1 and 9.1: 88 cells, 83 distinct values.
