# CPDat cleanup rules

CSV rule tables used by `cpdat_v4.0_cleanup.ipynb` (loaded through `inquire_common/rules.py`). Edit a CSV to change a mapping; no notebook code changes are needed. Files are UTF-8 with a header row. Keys and values are matched literally, so leading/trailing spaces and letter case are significant.

All `key,value` maps are plain lookups, so **row order does not matter** for them unless noted below.

| File | Columns | Row order matters? | Notebook cell | What it does |
| --- | --- | --- | --- | --- |
| `puc_general_map.csv` | `key`, `value` | No | 25 | Renames `puc_general_category` values (original name -> short name). |
| `use_keywords.csv` | `label`, `phrase` | No | 28/29 | One row per phrase. If a phrase appears in a product title, `label` is a candidate for the missing `puc_product_type`. All matching labels are collected and sorted, so order is irrelevant. |
| `unknown_keywords.csv` | `key`, `value` | **Yes** | 28/29 | Substring (`key`) in the title -> `puc_product_type` (`value`), only for rows where all four PUC columns are empty. The first matching row wins, so put more specific keywords before shorter ones that they contain. |
| `puc_type_exact_map.csv` | `key`, `value` | No | 29 | Exact (lower-cased) `puc_product_type` -> cleaned value, right after missing values are filled. |
| `puc_type_final_remap.csv` | `key`, `value` | No | 29 | Exact (lower-cased) `puc_product_type` fixes after apostrophe/mojibake normalisation. |
| `puc_type_final_brush_map.csv` | `key`, `value` | No | 29 | Exact (lower-cased) phrase-level `puc_product_type` replacements. |
| `puc_type_full_cell_map.csv` | `key`, `value` | No | 29 | Whole-cell `puc_product_type` replacements. The cell is lower-cased before lookup, so keys must be lower case. |
| `conditional_puc_type_rules.csv` | `puc_product_type`, `match_column`, `contains`, `new_puc_product_type` | **Yes** (within one `puc_product_type`) | 27/29 | If the (lower-cased) type equals `puc_product_type` and `contains` occurs in the lower-cased `match_column` (`puc_general_category`, `puc_product_family` or `product_title`), the type becomes `new_puc_product_type`. The first matching row for that type wins. Rows for different types are independent. |
| `puc_product_type_final_manual.csv` | `key`, `value` | No | 29 | Last manual fixes of `puc_product_type`, after title-casing. Case-sensitive exact match. |
| `puc_product_family_final_manual.csv` | `key`, `value` | No | 29 | Same, for `puc_product_family`. |
| `puc_general_category_final_manual.csv` | `key`, `value` | No | 29 | Same, for `puc_general_category`. |
| `title_map.csv` | `key` (regex), `value` | **Yes** | 31 | Regex substitutions (case-insensitive) applied one after another to the three PUC columns, to fix the capitalisation of specific phrases. Later patterns see the output of earlier ones. |

## Notes

- To change what a rule does, edit the CSV and re-run the notebook from cell 25 onwards. Re-run cell 2 first if the notebook kernel was already running, so the loader picks up the files.
- `puc_type_full_cell_map.csv` is checked after lower-casing, so a key that contains capital letters will never match.
- Dead entries were pruned (multi-term `;` keys in `puc_type_exact_map.csv`, three redundant apostrophe patterns in `title_map.csv`, identity entries in the `*_final_manual.csv` files). If the raw data changes, a removed rule may be needed again.
- Some other entries are still never reached in the CPDat v4.0 data (for example single-term keys in `puc_type_exact_map.csv`). They are kept deliberately.
