"""Cleaning helpers shared by the source-database cleanup notebooks (CAS formatting, name cleaning, uid hashing,
PubChem cache bookkeeping).

Every PubChem cache is keyed by ``uid``: a hash of the identifier values of a compound (see ``add_uid``), so a cache
stays valid when the row order of the input changes.
"""

import hashlib
import os
import re

import numpy as np
import pandas as pd

# Values that stand in for 'no value' (compared case-insensitively, after stripping)
PLACEHOLDERS = {"", "none", "nan", "n/a", "na", "null", "unknown", "-", "--", "?"}


def clean_value(value):
    """Return a stripped string, or None for missing values and placeholders.
    Covers the string 'None'/'nan' (from astype(str)) and entries such as '-', which PubChem rejects with an
    error instead of 'not found' (that would otherwise make the compound fail on every re-run)."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower() in PLACEHOLDERS or not any(ch.isalnum() for ch in value):
        return None
    return value


# ---------------------------------------------------------------------------
# CAS numbers
# ---------------------------------------------------------------------------
def format_cas(cas):
    """Format a CAS number without hyphens (e.g. 50000 or '50000.0') as 'XXXX-XX-X'. Missing/too short -> NaN."""
    if pd.isna(cas):
        return float("nan")

    # convert to string and strip unwanted chars and whitespace
    cas_str = str(cas).strip().lstrip("»»").rstrip("»»").strip()

    # remove decimal part if present
    cas_str = cas_str.split(".")[0]

    if len(cas_str) < 4:
        return float("nan")

    # format as regular CAS number
    return f"{cas_str[:-3]}-{cas_str[-3:-1]}-{cas_str[-1]}"


def normalize_cas(series):
    """Strip a CAS column that already has hyphens; '', 'none' and 'nan' become NaN. Returns an object Series."""
    cas = series.astype("string").str.strip()
    cas = cas.mask(cas.str.lower().isin(["", "none", "nan"]))
    return cas.astype(object).where(cas.notna(), np.nan)


def count_odd_cas(series):
    """Number of non-missing values that do not look like a CAS number (2-7 digits, 2 digits, 1 digit)."""
    return int((~series.dropna().str.fullmatch(r"\d{2,7}-\d{2}-\d")).sum())


# ---------------------------------------------------------------------------
# Name cleaning
# ---------------------------------------------------------------------------
SYNONYM_PATTERN = r"\s*\(or|\s*\|\|"


def truncate_synonyms(series):
    """Split on ' (or' and then ' ||' (if still present) and keep the first part."""
    return series.str.split(SYNONYM_PATTERN, n=1, regex=True).str[0].str.strip()


def strip_guillemets(df, cols, force_text=False):
    """Remove every run of '»' from ``cols`` (in place) and report how many rows were affected.
    ``force_text`` first converts the columns to text (needed when the CSV was read with its own dtypes)."""
    for col in cols:
        if force_text:
            df[col] = df[col].astype("string").astype(object)
        mask = df[col].str.contains(r"»+", regex=True, na=False)
        df[col] = df[col].str.replace(r"»+", "", regex=True).str.strip()
        print(f"Column '{col}': '»' removed from {mask.sum():,} rows")
    print()
    return df


def drop_mixtures(df, col, separators, label):
    """Drop rows whose ``col`` contains any of the mixture ``separators``; print diagnostics. Returns the new df."""
    n_total = len(df)
    sep_counts = {sep: df[col].str.contains(re.escape(sep), na=False).sum() for sep in separators}
    mask = df[col].str.contains("|".join(map(re.escape, separators)), regex=True, na=False)
    out = df[~mask].reset_index(drop=True)

    print(f"Total rows before {label} filtration: \n{n_total:,}\n")
    print(f"{label} containing mixture patterns (to be removed): \n{mask.sum():,}\n")
    print(f"{label} actually removed: \n{n_total - len(out):,}\n")
    print(f"Remaining rows after filtering: \n{len(out):,}\n")
    print(f"Number of {label} containing each separator pattern:")
    for sep, count in sep_counts.items():
        print(f"  '{sep}': {count:,}")
    print()
    return out


def clean_names(df, name_cols=("Name",), cas_cols=("CAS",), separators=(";", "/", "+"), force_text=False):
    """Name & CAS cleaning shared by SPECIATE and SPECIEUROPE.

    Expects an ``<col>_Original`` copy of each name column in ``df``. Steps: (1) remove '»' from the name and CAS
    columns, (2) keep only the first synonym of each name column, (3) drop rows whose first name column
    (``name_cols[0]``) holds a mixture separator, (4) drop rows whose first CAS column holds one. Returns the
    cleaned DataFrame (``df`` is not modified).
    """
    df = df.copy()
    strip_guillemets(df, [*cas_cols, *name_cols], force_text=force_text)

    for col in name_cols:
        df[col] = truncate_synonyms(df[col])
        original = df[f"{col}_Original"]
        n_candidates = original.str.contains(r"\(or|\|\|", regex=True, na=False).sum()
        n_changed = (original != df[col]).sum()
        print(f"Total '{col}' values: \n{len(df):,}\n")
        print(f"'{col}' containing synonym patterns (to be fixed): \n{n_candidates:,}\n")
        print(f"'{col}' actually fixed: \n{n_changed:,}\n")

    df = drop_mixtures(df, name_cols[0], separators, "Names")
    df = drop_mixtures(df, cas_cols[0], separators, "CAS#")
    print(f"Filtered DF shape: \n{df.shape[0]:,} rows × {df.shape[1]} columns\n")
    return df


# ---------------------------------------------------------------------------
# uid hashing and cache bookkeeping
# ---------------------------------------------------------------------------
def make_uid(values):
    """Stable 16-character hash of a tuple of identifier values."""
    return hashlib.md5("\x1f".join(map(str, values)).encode("utf-8")).hexdigest()[:16]


def add_uid(df, key_cols):
    """Distinct combinations of ``key_cols`` with a ``uid`` column (hash of the values; asserts it is unique).
    Missing values hash as 'nan', so convert text columns (e.g. CAS#) to str in the full table too if the result
    is merged back on ``key_cols``."""
    df_unique = df[list(key_cols)].drop_duplicates().reset_index(drop=True)
    df_unique["uid"] = [make_uid(vals) for vals in df_unique[list(key_cols)].itertuples(index=False, name=None)]
    assert df_unique["uid"].is_unique, "uid collision in the unique identifier sets"
    return df_unique


def load_cache(path, cache_cols):
    """Read the lookup cache (all rows), or an empty frame with ``cache_cols`` if it does not exist yet."""
    if os.path.exists(path):
        cache = pd.read_csv(path)
        if "uid" not in cache.columns:
            raise ValueError(f"{path} has no 'uid' column; convert it with migrate_cache_key() or delete it.")
        return cache
    return pd.DataFrame(columns=cache_cols)


def read_cache(path, cache_cols=None):
    """Cache as one row per uid (last entry wins), with CID as nullable integer. Empty if there is no cache file."""
    if not os.path.exists(path):
        return pd.DataFrame(columns=cache_cols or ["uid"])
    return pd.read_csv(path, dtype={"CID": "Int64"}).drop_duplicates("uid", keep="last")


def append_cache(path, records, cache_cols):
    """Append lookup records (list of dicts) to the cache CSV; the header is written only for a new file."""
    if records:
        pd.DataFrame(records, columns=cache_cols).to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def migrate_cache_key(path, df_unique, legacy_key):
    """One-off: convert a cache keyed by ``legacy_key`` (e.g. 'cpd_id') to ``uid``. ``df_unique`` must hold both
    columns (see ``add_uid``). Does nothing if the cache is missing or already has a 'uid' column.
    Entries of the legacy key that are not in ``df_unique`` are dropped."""
    if not os.path.exists(path):
        return
    cache = pd.read_csv(path)
    if "uid" in cache.columns or legacy_key not in cache.columns:
        return
    n_old = len(cache)
    cache = cache.merge(df_unique[[legacy_key, "uid"]], on=legacy_key, how="inner").drop(columns=legacy_key)
    cache = cache[["uid", *[c for c in cache.columns if c != "uid"]]]
    cache.to_csv(path, index=False)
    print(f"Cache converted to 'uid' key: {len(cache):,} of {n_old:,} entries kept.")
