# Framework datasets

One folder per framework. Only `nist-ai-rmf/` is built so far, from NIST's own files. It is the reference for the layout.

**These column choices are proposals that you have not yet confirmed**: ids prefixed with the framework, a `parent`/`level`/`ordinal` tree of variable depth, `is_header` and `assessable` flags, and facets in a separate long table.

`provisions.csv`

| Column | Meaning |
|---|---|
| `id` | `<framework>:<official citation>`, e.g. `nist-ai-rmf:GV-1.4` |
| `parent` | id of the parent row (blank at the top) |
| `level` | named level for this framework, listed in `framework.yaml` |
| `ordinal` | order among siblings |
| `kind` | `GROUP`, `OUTCOME`, `OBLIGATION`, `REQUIREMENT`, `CONTROL`, `TEST` |
| `is_header` | the row only groups others and carries no requirement |
| `assessable` | the row can receive a Finding (set explicitly, not just the leaves) |
| `source_text` | the official wording where the text policy allows it |
| `status` | `verified`, `verified-variant`, ... defined in `framework.yaml` |
| `note` | for example the other document's wording where two official sources differ |

`facets.csv`: `provision_id, facet, value, source`. Tags that cut across the tree (here NIST's own AI actors and topics).

Rebuild NIST with `tools/build_nist_ai_rmf.py` when NIST updates the Playbook or AI RMF.
