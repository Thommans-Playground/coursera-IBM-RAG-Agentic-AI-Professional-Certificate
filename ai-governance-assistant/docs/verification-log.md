# Verification log

Dated 2026-10-24. "Primary" means the issuing body's own document. Row-level evidence is in `data/verification/`.

## NIST AI RMF 1.0: verified against two NIST documents

| Check | Result |
|---|---|
| 72 subcategories (GOVERN 19, MAP 18, MEASURE 22, MANAGE 13) | **Confirmed** in both NIST AI 100-1 and the NIST Playbook JSON |
| The sheet's NIST data | 71 of 72 ids (`MS-4.3` missing). Wording matches in 33 rows, is a paraphrase in 12, and differs in 25. `MS-2.2` carries `MS-2.3`'s text |
| Replacement dataset | `data/frameworks/nist-ai-rmf/`: 4 functions, 19 categories, 72 subcategories, NIST's own tags. 67 rows agree between the two NIST documents; 5 are worded differently by the Playbook and AI 100-1 (AI 100-1 is stored, Playbook wording kept in `note`) |
| Not reviewed by a person | yes: cross-check is automated |

## EU AI Act: compared with the Commission's consolidated text as at 27 July 2026

Source: https://ai-act-service-desk.ec.europa.eu (European Commission). It says its text is based on the EUR-Lex consolidated version, with the Digital Omnibus on AI changes marked NEW or AMENDED. EUR-Lex itself blocks automated access (HTTP 202, empty). The consolidated text is a reading aid, not the authentic text.

| Check | Result |
|---|---|
| Digital Omnibus adopted and in force | **Confirmed by the Commission's own page**: consolidated at 27 July 2026, Art. 113 amended. (Regulation number (EU) 2026/1744 comes from secondary sources and was not seen on this page) |
| Application dates (Art. 113) | Chapters I and II from 2 Feb 2025, except Art. 5(1) points (ba) and (bb) and Art. 5(1a), (1b) from **2 Dec 2026**. Chapter III s4, Chapters V, VII, XII and Art. 78 from 2 Aug 2025 (not Art. 101). Chapter III s1-3 (except Art. 6(5)) from **2 Dec 2027** for Annex III systems and **2 Aug 2028** for Annex I. Articles 102-110 from 27 Jul 2026. Everything else 2 Aug 2026 |
| Sheet dates | 44 high-risk rows (Chapter III s1-3) are stale; 3 penalties rows (Chapter XII) should be 2 Aug 2025 |
| Sheet rows (72) | 42 ok; 20 renumbered; 3 reworded; 6 no automatic match (need a person); 1 deleted by the Omnibus (`Art.10.5`) |
| Art. 5 lettering | Sheet (c) biometric categorisation is official 5(1)(g); (d) social scoring is 5(1)(c); (e) criminal risk 5(1)(d); (f) scraping 5(1)(e); (g) emotion inference 5(1)(f). The sheet's `Art.5(a)` style is also not the official `Art.5(1)(a)` |
| Other renumberings | 9.3 is 9(4); 9.4 is 9(6); 10.1 is 10(2); 10.2 is 10(3); 10.3 is 10(4); 12.1 is 12(2); 12.2 is 12(3); 13.2 is 13(3); 14.3 is 14(4); 15.3 is 15(5); 26.6 is 26(7); 50.2 is 50(3); 50.3 is 50(4); 72.1 is 72(2) |
| Fundamental rights impact assessment | The sheet puts it at `Art.26.7`. It is **Article 27** |
| Art. 10(5) special categories for bias detection | Deleted from Art. 10; now **new Art. 4a** |
| Not covered | The sheet has no annex rows, so the annexes are in the dataset but were not compared |

Effect on the theme links: of 8 EU paragraph-level references, 4 are right, 2 point at the wrong paragraph (15(3) should be 15(5); 10(2) should be 10(3)), 1 points at a deleted provision (10(5)), 1 needs a decision (26(7)). See `data/links/theme_links.csv`, columns `verification` and `suggested_provision_id`.

## AI Verify: compared with the official IMDA Testing Framework (2025 edition)

Source: https://file.go.gov.sg/aivtf-pdf.pdf, 118 pages, parsed by position. Counts match the ids found by scanning the PDF text.

| Check | Result |
|---|---|
| 112 process ids | **All 112 match** the sheet |
| 88 outcomes | The sheet's Outcome ID column is stored as numbers, so 3.10, 4.10, 5.10, 7.10 and 9.10 collapsed into 3.1, 4.1, 5.1, 7.1, 9.1 (88 cells, 83 distinct values). All 88 are real |
| Wording | The sheet's process text is a paraphrase: only 5 of 112 are verbatim. 10 describe something different (5.8.1 to 5.12.1, 7.6.1, 7.9.1, 8.3.1, 9.9.1, 10.3.1) |
| Applicability tag (traditional / generative / both) | Agrees on all 112 |
| Technical-test processes | 2.1.1, 4.1.1, 6.1.1, 7.1.1, 7.2.1 |
| The 11 crosswalk ids not in the sheet | Not in the 2025 edition. Six are named in the October 2023 NIST/IMDA crosswalk, which uses 2023 numbering (version drift); five are in neither |
| Replacement dataset | `data/frameworks/ai-verify/`: 11 principles, 88 outcomes, 112 processes, evidence types and descriptions. Not reviewed by a person |

## ISO/IEC 42001: structure only

The standard is paywalled and could not be checked against its text. `data/frameworks/iso-42001/` holds 104 rows built from the sheet (ids, titles, normative flags, evidence notes, no standard wording): 38 controls in 9 topics (A.2 to A.10), clauses 4 to 10, Annexes A to D. 38 controls in 9 topics matches the commonly cited shape; secondary sources confirm the A.2 to A.4 titles. All titles are marked `unverified-title`.

## Data checks

`python -I tools/check_data.py data` checks ids, parents, counts, facets, links and the ISO text policy. It passes.

## Checked by research (earlier today), mostly secondary sources

| Claim | Result |
|---|---|
| NIST crosswalk AI RMF to ISO/IEC 23894 | **Confirmed, high.** Revised 14 Aug 2025 (INCITS/AI), function level |
| NIST and IMDA crosswalk AI RMF to AI Verify | **Confirmed, high.** Oct 2023, category level; a May 2025 one covers the Generative AI Profile (NIST AI 600-1) |
| NIST crosswalk to ISO/IEC 42001 | Listed on NIST AIRC but supplied by Microsoft, undated. No NIST-issued EU AI Act crosswalk found |
| ISO/IEC 42001 as a harmonised standard under the AI Act | **No** (Commission FAQ, March 2026). Status of the replacement standard prEN 18286 is unclear: sources conflict |
| AI Verify has 11 principles | Consistent; NIST's crosswalk numbers 12 groups, adding Organisational Considerations (weak evidence) |

## Not verified

- Art. 99 fine ceilings (the text is now in the dataset but not compared with a source of record)
- ISO 42001: control titles and certifiability
- AI Verify: no certification; Project Moonshot maintenance
