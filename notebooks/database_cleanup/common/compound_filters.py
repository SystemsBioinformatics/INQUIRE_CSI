"""Compound filters shared by the source-database cleanup notebooks."""

from pathlib import Path

FILTER_DIR = Path(__file__).parent / "filters"


def _read_keys(path):
    keys = []
    for line in path.read_text(encoding="utf-8").splitlines():
        key = line.split("#", 1)[0].strip()
        if key:
            keys.append(key)
    return keys


def load_drop_inchikeys(*sources):
    """Return the list of InChIKeys to drop.

    Always includes ``filters/drop_inchikeys.txt`` (shared by all sources).
    Each name in ``sources`` (e.g. ``"foodb"``) adds
    ``filters/drop_inchikeys_<source>.txt``. Order is kept, duplicates removed.
    """
    paths = [FILTER_DIR / "drop_inchikeys.txt"]
    for source in sources:
        path = FILTER_DIR / f"drop_inchikeys_{source}.txt"
        if not path.exists():
            raise FileNotFoundError(f"No InChIKey filter list for source '{source}': {path}")
        paths.append(path)
    return list(dict.fromkeys(key for p in paths for key in _read_keys(p)))


def drop_by_inchikey(df, inchikey_col, drop_inchikeys, name_col=None, verbose=True):
    """Remove rows whose InChIKey is in ``drop_inchikeys``.

    Returns ``(filtered_df, dropped)`` where ``dropped`` lists the unique
    removed InChIKeys (with ``name_col`` if given).
    """
    if inchikey_col not in df.columns or (name_col and name_col not in df.columns):
        raise KeyError(f"Required columns not found: {[inchikey_col, name_col]}")

    mask = df[inchikey_col].isin(set(drop_inchikeys))
    cols = [inchikey_col] + ([name_col] if name_col else [])
    dropped = df.loc[mask, cols].drop_duplicates().sort_values(inchikey_col)

    if verbose:
        print("Dropped compounds by InChIKey:")
        if dropped.empty:
            print("No matching InChIKeys found")
        for _, row in dropped.iterrows():
            label = f" >>> {row[name_col]}" if name_col else ""
            print(f"{row[inchikey_col]}{label}")
        print(f"\nDropped {dropped[inchikey_col].nunique():,} unique InChIKeys ({mask.sum():,} rows)")
        print(f"Rows remaining: {(~mask).sum():,}\n")

    return df.loc[~mask].copy(), dropped


def _read_terms(path):
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        term = line.split("#", 1)[0].strip()
        if term:
            terms.append(term)
    return terms


def load_keywords(*sources):
    """Unwanted name keywords: ``keywords_common.txt`` plus ``keywords_<source>.txt`` per source."""
    paths = [FILTER_DIR / "keywords_common.txt"]
    for source in sources:
        path = FILTER_DIR / f"keywords_{source}.txt"
        if not path.exists():
            raise FileNotFoundError(f"No keyword list for source '{source}': {path}")
        paths.append(path)
    return list(dict.fromkeys(t for p in paths for t in _read_terms(p)))


def load_keyword_exceptions():
    """Names (substrings) protected from keyword removal."""
    return _read_terms(FILTER_DIR / "keyword_exceptions.txt")


def build_pattern(terms, anchor_end=False):
    """Regex matching any term literally. Single words are anchored at a word start (so stems such as
    'magnes' match 'magnesium' but 'lead' does not match 'mislead'); phrases are matched as-is.
    With ``anchor_end`` single words must also end at a word boundary (whole words only, so stems
    like 'magnes' never match)."""
    import re

    end = r"\b" if anchor_end else ""
    parts = [rf"\b{re.escape(t)}{end}" if " " not in t else re.escape(t) for t in terms]
    return "|".join(parts)


def drop_by_keyword(df, name_col, terms, exceptions=(), anchor_end=False, verbose=True):
    """Remove rows whose ``name_col`` matches any keyword, unless the name contains an exception term.

    Returns ``(filtered_df, dropped_names)`` with the sorted unique removed names.
    """
    pattern = build_pattern(terms, anchor_end)
    names = df[name_col]
    unwanted = names.str.contains(pattern, case=False, na=False, regex=True)
    lowered = names.fillna("").astype(str).str.lower()
    protected = lowered.apply(lambda s: any(e.lower() in s for e in exceptions)) if exceptions else False
    drop = unwanted & ~protected
    dropped = sorted(names[drop].dropna().unique())

    if verbose:
        print(f"Dropped unique names by keyword: {len(dropped):,}\n")
        for name in dropped:
            print(name)
        print(f"\nRows: {len(df):,} -> {(~drop).sum():,}\n")
    return df.loc[~drop].copy(), dropped


def apply_standard_filters(df, source, inchikey_col="inchikey", name_col="name", anchor_end=True, drop_missing_inchikey=True,
                           inchikey_sources=None, label=None, verbose=True):
    """InChIKey and name-keyword filtering shared by all source databases.

    Uses the standard schema of the cleanup notebooks: ``inchikey`` (InChIKey) and ``name`` (PubChem compound name);
    pass ``inchikey_col`` / ``name_col`` only for a frame that deviates from it.

    Steps: (1) optionally drop rows without an InChIKey (``drop_missing_inchikey``), (2) drop InChIKeys listed
    in ``filters/drop_inchikeys.txt`` (plus ``drop_inchikeys_<s>.txt`` for each ``s`` in ``inchikey_sources``,
    default: none), (3) drop names matching ``keywords_common.txt`` + ``keywords_<source>.txt``, unless protected
    by ``keyword_exceptions.txt``. ``anchor_end=True`` matches whole words only; False also matches stems.

    Returns ``(filtered_df, dropped_inchikeys, dropped_names)``.
    """
    label = label or source
    initial_n = len(df)
    if verbose:
        print(f"Number of entries in {label} before InChIKey & keyword filtration: \n{initial_n:,}\n")

    if drop_missing_inchikey:
        # Keep individual chemicals only (no InChIKey = mixture or unidentified feature)
        df = df[df[inchikey_col].notna()].copy()
        if verbose:
            print(f"Dropped {initial_n - len(df):,} entries with no InChIKey values. \n\nRemaining rows: \n{len(df):,}\n")

    df, dropped_inchikeys = drop_by_inchikey(
        df, inchikey_col=inchikey_col, drop_inchikeys=load_drop_inchikeys(*(inchikey_sources or ())),
        name_col=name_col, verbose=verbose,
    )
    df, dropped_names = drop_by_keyword(
        df, name_col=name_col, terms=load_keywords(source), exceptions=load_keyword_exceptions(),
        anchor_end=anchor_end, verbose=verbose,
    )
    if verbose:
        print(f"Filtered {label}: \n{initial_n:,} → {len(df):,} rows\n")
    return df, dropped_inchikeys, dropped_names
