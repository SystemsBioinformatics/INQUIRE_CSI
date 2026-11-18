"""Generic loader for the cleanup rule tables stored as CSV files in a notebook's ``rules/`` folder.

Rules are data, not code: edit the CSV files to change a mapping. Row order is preserved because some
rule sets are order-sensitive. Files are UTF-8 with a header row; values are matched literally, so
leading/trailing spaces and letter case are significant.

Usage::

    rules = RuleSet("rules")                  # folder relative to the notebook
    TITLE_MAP = rules.load_map("title_map")   # key,value -> dict
"""
import csv
from collections import OrderedDict
from pathlib import Path


class RuleSet:
    def __init__(self, rules_dir="rules"):
        self.rules_dir = Path(rules_dir).resolve()

    def _read_rows(self, name):
        with open(self.rules_dir / f"{name}.csv", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # header
            return [row for row in reader]

    def load_list(self, name):
        """Load ``<name>.csv`` (one column, header row) as a list of strings."""
        return [row[0] for row in self._read_rows(name) if row]

    def load_map(self, name):
        """Load ``<name>.csv`` (columns: key, value) as an ordered dict."""
        return dict(self._read_rows(name))

    def load_use_keywords(self, name="use_keywords"):
        """Load ``<name>.csv`` (columns: label, phrase) as OrderedDict[label, list[phrase]]."""
        out = OrderedDict()
        for label, phrase in self._read_rows(name):
            out.setdefault(label, []).append(phrase)
        return out

    def load_conditional_rules(self, name="conditional_puc_type_rules"):
        """Load ``<name>.csv`` (columns: key, match_column, contains, new_value) as a dict:
        key (as written) -> ordered list of (match_column, contains, new_value). The first matching rule wins."""
        out = {}
        for key, column, contains, new in self._read_rows(name):
            out.setdefault(key, []).append((column, contains, new))
        return out
