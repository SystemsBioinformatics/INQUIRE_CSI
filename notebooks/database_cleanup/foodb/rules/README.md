# FooDB cleanup rules

CSV rule tables used by `foodb_v1.0_cleanup.ipynb` (loaded through `inquire_common/rules.py`). Edit a CSV to change a rule; no notebook code changes are needed. Files are UTF-8 with a header row.

- `summary_name_patterns.csv`: `Content` rows whose `orig_name` contains one of these strings (literal, case-insensitive) are dropped as summary entries (e.g. "Fat, total (Lipids)").
