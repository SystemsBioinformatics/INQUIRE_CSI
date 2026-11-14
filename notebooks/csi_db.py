"""SQLite database for the Part 1 results of INQUIRE_CSI.

Builds `docs/schema.sql` from the CSV files written by INQUIRE_CSI_Pt1_Preprocessing,
exports the views as CSV/Excel copies for inspection and checks that the views reproduce
the original CSV files.

Typical use (end of Part 1)::

    csi_db.build_database(PREP_OUT_DIR, SAMPLE_FILE, DB_FILE)
    csi_db.export_all(DB_FILE, PREP_OUT_DIR / "inspection")
    csi_db.verify_against_csv(DB_FILE, PREP_OUT_DIR, SAMPLE_FILE)

Typical use (Part 2)::

    con = csi_db.connect(DB_FILE)
    sources_masked = csi_db.read_view(con, "sources_masked")
    sample_universes = csi_db.read_sample_universes(con)
"""

from __future__ import annotations

import io
import os
import sqlite3
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "docs" / "schema.sql"
DB_NAME = "inquire_csi_pt1.sqlite"
MULTI_SEP = "; "  # separator of multi-valued cells in all_compounds_standardized.csv

ORIGIN_SUFFIX = {
    "CPDAT": "_CPD",
    "HOUSEHOLD_PRODUCTS": "_HHP",
    "LIT_CONSUMER_PRODUCTS": "_COP",
    "FOODB": "_FDB",
    "SPECIATE": "_SUS",
    "SPECIEUROPE": "_SEU",
}

# view name (without "v_") -> original CSV, relative to the Part 1 output folder
LEGACY_CSV = {
    "all_sources_standardized": "databases_standardized/all_sources_standardized.csv",
    "all_sources_aggregated": "all_sources_aggregated/all_sources_aggregated.csv",
    "sources_masked": "masked_sources/sources_masked.csv",
    "sources_meta_standardized": "databases_standardized/sources_meta_standardized.csv",
    "all_compounds_standardized": "databases_standardized/all_compounds_standardized.csv",
    "equivalence_groups_members": "databases_standardized/equivalence_groups_members.csv",
    "equivalence_groups_summary": "databases_standardized/equivalence_groups_summary.csv",
    "masked_equivalence_groups_members": "masked_sources/masked_equivalence_groups_members.csv",
    "counts_masked": "masked_sources/counts_masked.csv",
    "valid_sources_masked": "masked_sources/valid_sources_masked.csv",
}
SAMPLE_META_COLS = ["inchikey", "Feature Name", "Class", "Concentration Type"]


def _log(msg):
    print(msg)


def _read_str(path):
    """Read a CSV as text; empty cells stay '' (no NA parsing), so that nothing is altered."""
    return pd.read_csv(path, dtype=str, keep_default_na=False, low_memory=False)


def _null(s: pd.Series) -> pd.Series:
    """Empty string -> NULL."""
    return s.where(s != "", None)


def connect(db_path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON")
    return con


def read_view(con: sqlite3.Connection, name: str) -> pd.DataFrame:
    """Read view `v_<name>` as a DataFrame (NULL -> NaN, like an empty CSV cell read by pandas)."""
    name = name if name.startswith("v_") else f"v_{name}"
    return pd.read_sql(f"SELECT * FROM {name}", con)


def _sample_matrix(con) -> pd.DataFrame:
    """Wide sample table (rows: compounds in original order; columns: samples in original order)."""
    samples = [r[0] for r in con.execute("SELECT sample_id FROM sample ORDER BY position")]
    meta = pd.read_sql(
        "SELECT inchikey, feature_name AS 'Feature Name', compound_class AS 'Class', "
        "concentration_type AS 'Concentration Type' FROM detected_compound ORDER BY position",
        con,
    )
    long = pd.read_sql("SELECT sample_id, inchikey, concentration FROM sample_compound", con)
    wide = long.pivot(index="inchikey", columns="sample_id", values="concentration")
    wide = wide.reindex(index=meta["inchikey"], columns=samples).reset_index(drop=True)
    return pd.concat([meta, wide], axis=1)


def read_samples_standardized(con) -> pd.DataFrame:
    """Same content as dust_standardized.csv."""
    return _sample_matrix(con)


def read_sample_universes(con, na_value=float("nan")) -> pd.DataFrame:
    """Same content as sample_universes.csv: one row per InChIKey detected in any sample,
    one column per sample; the InChIKey if detected (> 0), otherwise `na_value`."""
    samples = [r[0] for r in con.execute("SELECT sample_id FROM sample ORDER BY position")]
    det = read_view(con, "sample_detections")
    keys = pd.Index(sorted(det["inchikey"].unique()))
    present = np.zeros((len(keys), len(samples)), dtype=bool)
    present[keys.get_indexer(det["inchikey"]), pd.Index(samples).get_indexer(det["sample_id"])] = True
    values = np.where(present, keys.to_numpy(dtype=object)[:, None], na_value)
    return pd.concat([pd.DataFrame({"inchikey": keys}), pd.DataFrame(values, columns=samples)], axis=1)


# ----------------------------------------------------------------------------- build

def build_database(prep_out_dir, sample_file, db_path=None, schema_file=SCHEMA_FILE, log=_log) -> Path:
    """Build the SQLite database from the Part 1 CSV files. Written to a temporary file and
    renamed at the end, so an interrupted run never leaves a half-built database."""
    prep = Path(prep_out_dir)
    db_path = Path(db_path) if db_path else prep / DB_NAME
    tmp = db_path.with_suffix(db_path.suffix + ".tmp")
    tmp.unlink(missing_ok=True)

    con = sqlite3.connect(str(tmp))
    try:
        con.executescript(Path(schema_file).read_text(encoding="utf-8"))

        # sources
        meta = _read_str(prep / LEGACY_CSV["sources_meta_standardized"])
        origins = pd.DataFrame({"source_origin": sorted(meta["source_origin"].unique())})
        origins["id_suffix"] = origins["source_origin"].map(ORIGIN_SUFFIX)
        classes = meta[["source_class", "source_class_domain"]].drop_duplicates()
        if classes["source_class"].duplicated().any():
            raise ValueError("A source_class has more than one source_class_domain")
        src_cols = ["source_id", "source_name", "source_origin", "source_kind",
                    "source_general_category", "source_harmonized", "source_class"]
        for col in ("source_name", "source_kind", "source_general_category", "source_harmonized"):
            meta[col] = _null(meta[col])
        _append(con, "source_origin", origins)
        _append(con, "source_class", classes)
        _append(con, "source", meta[src_cols])

        # compounds
        comp = _read_str(prep / LEGACY_CSV["all_compounds_standardized"])
        _append(con, "compound", pd.DataFrame({"inchikey": comp["inchikey"],
                                               "feature_name": _null(comp["feature_name"])}))
        for table, col, out in (("compound_name", "all_feature_names", "name"),
                                ("compound_cas", "cas", "cas"),
                                ("compound_dtxsid", "dtxsid", "dtxsid")):
            rows = (comp[["inchikey", col]][comp[col] != ""]
                    .assign(**{out: lambda d, c=col: d[c].str.split(MULTI_SEP)})
                    .explode(out))
            rows["position"] = rows.groupby("inchikey").cumcount()
            _append(con, table, rows[["inchikey", "position", out]])

        # source x compound with stage flags
        std = _read_str(prep / LEGACY_CSV["all_sources_standardized"])[["source_id", "inchikey"]]
        flags = std.copy()
        for flag, rel in (("in_aggregated", "all_sources_aggregated"), ("in_masked", "sources_masked")):
            sub = _read_str(prep / LEGACY_CSV[rel])[["source_id", "inchikey"]]
            idx = pd.MultiIndex.from_frame(std)
            sub_idx = pd.MultiIndex.from_frame(sub)
            missing = sub_idx.difference(idx)
            if len(missing):
                raise ValueError(f"{len(missing)} rows of {rel} are not in all_sources_standardized, "
                                 f"e.g. {missing[0]}")
            flags[flag] = idx.isin(sub_idx).astype(int)
        _append(con, "source_compound", flags)

        # equivalence groups
        agg = _read_str(prep / LEGACY_CSV["equivalence_groups_members"])
        _append(con, "source_group", pd.DataFrame({
            "stage": "aggregated", "representative_id": agg["eqsetID"], "member_id": agg["sourceID"]}))
        masked_file = prep / LEGACY_CSV["masked_equivalence_groups_members"]
        if masked_file.exists():  # only written if REAGGREGATE_AFTER_MASKING = True
            mk = _read_str(masked_file)
            _append(con, "source_group", pd.DataFrame({
                "stage": "masked", "representative_id": mk["masked_eqsetID"], "member_id": mk["source_id"],
                "masked_hash": _null(mk["masked_hash"]), "hh_household": _null(mk["hh_household"])}))

        # samples (long format)
        dust = pd.read_csv(sample_file, low_memory=False, float_precision="round_trip")  # exact floats
        # Sample columns = all columns after "Concentration Type"; of the leading columns only
        # the 4 required metadata columns are kept (any extra leading columns are ignored)
        missing = [c for c in SAMPLE_META_COLS if c not in dust.columns]
        if missing:
            raise ValueError(f"Required columns missing in {sample_file}: {missing}")
        start = list(dust.columns).index("Concentration Type") + 1
        sample_cols = list(dust.columns[start:])
        dust = dust[SAMPLE_META_COLS + sample_cols]
        dust = aggregate_duplicate_inchikeys(dust, log)
        _append(con, "sample", pd.DataFrame({"sample_id": sample_cols, "position": range(len(sample_cols))}))
        det = dust[SAMPLE_META_COLS].copy()
        det.columns = ["inchikey", "feature_name", "compound_class", "concentration_type"]
        det["position"] = range(len(det))
        _append(con, "detected_compound", det)
        long = (dust[["inchikey"] + sample_cols]
                .melt(id_vars="inchikey", var_name="sample_id", value_name="concentration")
                .dropna(subset=["concentration"]))
        _append(con, "sample_compound", long[["sample_id", "inchikey", "concentration"]])

        con.commit()
        bad = con.execute("PRAGMA foreign_key_check").fetchall()
        if bad:
            raise ValueError(f"Foreign key violations (table, rowid, parent): {bad[:5]}")
        counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for (t,) in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")}
    finally:
        con.close()

    os.replace(tmp, db_path)
    log(f" - SQLite database written: {db_path} ({db_path.stat().st_size / 1e6:.1f} MB)")
    log(" - Rows per table: " + ", ".join(f"{t}={n:,}" for t, n in counts.items()))
    return db_path


def aggregate_duplicate_inchikeys(dust, log=_log):
    """Warn about rows of the sample table that share an InChIKey and merge them into one row
    (at the position of the first one): concentrations of the sample columns (all columns after
    "Concentration Type") are summed (a sample stays empty if all merged rows are empty), feature
    names are joined with MULTI_SEP, all other columns come from the first row. All columns are kept."""
    dup = dust.loc[dust["inchikey"].notna() & dust["inchikey"].duplicated(keep=False)]
    if dup.empty:
        return dust
    cols = list(dust.columns)
    sample_cols = cols[cols.index("Concentration Type") + 1:]
    names = dup.groupby("inchikey", sort=False)["Feature Name"].agg(lambda s: " | ".join(map(str, s)))
    msg = (f"{len(names)} InChIKey(s) occur in more than one row of the sample table. Rows with the "
           f"same InChIKey are aggregated by summing the concentrations and joining the feature names "
           f"(\"{MULTI_SEP.strip()}\"):\n" + "\n".join(f"   {k}: {v}" for k, v in names.items()))
    warnings.warn(msg, UserWarning, stacklevel=3)
    log(" - WARNING: " + msg)
    has_key = dust["inchikey"].notna()
    keep, rest = dust[has_key], dust[~has_key]
    grp = keep.groupby("inchikey", sort=False)
    other = [c for c in cols if c not in sample_cols and c not in ("inchikey", "Feature Name")]
    out = pd.concat([grp[other].first(),
                     grp["Feature Name"].agg(lambda s: MULTI_SEP.join(dict.fromkeys(str(x) for x in s.dropna()))),
                     grp[sample_cols].sum(min_count=1)], axis=1).reset_index()[cols]
    return pd.concat([out, rest], ignore_index=True)


def _append(con, table, df):
    df.to_sql(table, con, if_exists="append", index=False, chunksize=50_000)


# ----------------------------------------------------------------------------- export

def _views(con):
    return [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='view' AND name LIKE 'v\\_%' ESCAPE '\\' ORDER BY name")]


def _export_frames(con):
    """name -> (DataFrame, na_rep) of everything that is exported."""
    frames = {v[2:]: (read_view(con, v), "") for v in _views(con)}
    frames["sample_universes"] = (read_sample_universes(con, na_value="NA"), "NA")
    frames["dust_standardized"] = (_sample_matrix(con), "")
    return frames


def export_all(db_path, out_dir, excel=True, excel_max_rows=100_000, log=_log):
    """Write every view (and the two wide sample tables) as CSV to `out_dir`, and optionally
    all tables with up to `excel_max_rows` rows as sheets of one Excel workbook."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    con = connect(db_path)
    try:
        frames = _export_frames(con)
    finally:
        con.close()
    for name, (df, na_rep) in frames.items():
        df.to_csv(out_dir / f"{name}.csv", index=False, na_rep=na_rep)
    log(f" - Exported {len(frames)} CSV copies to {out_dir}")
    if excel:
        xlsx = out_dir / "inquire_csi_pt1.xlsx"
        skipped = [n for n, (d, _) in frames.items() if len(d) > excel_max_rows]
        with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
            for name, (df, _) in frames.items():
                if len(df) <= excel_max_rows:
                    df.to_excel(xw, sheet_name=name[:31], index=False)
        log(f" - Excel workbook written: {xlsx}")
        if skipped:
            log(f" - Not in Excel (more than {excel_max_rows:,} rows; CSV only): {', '.join(skipped)}")


# ----------------------------------------------------------------------------- verify

def verify_against_csv(db_path, prep_out_dir, sample_file, log=_log) -> pd.DataFrame:
    """Compare every exported table with the original CSV file (cell by cell, as text).
    Returns a table with one status per file: identical / same rows, other order / DIFFERENT."""
    prep = Path(prep_out_dir)
    targets = {k: prep / v for k, v in LEGACY_CSV.items()}
    targets["sample_universes"] = prep / "masked_sources" / "sample_universes.csv"
    targets["dust_standardized"] = Path(sample_file)
    con = connect(db_path)
    try:
        frames = _export_frames(con)
    finally:
        con.close()

    rows = []
    for name, path in targets.items():
        if not path.exists():
            rows.append((name, "original file not found (skipped)", None, None))
            continue
        df, na_rep = frames[name]
        buf = io.StringIO()
        df.to_csv(buf, index=False, na_rep=na_rep)
        buf.seek(0)
        new = pd.read_csv(buf, dtype=str, keep_default_na=False)
        old = _read_str(path)
        if name == "dust_standardized":  # the CSV may have extra leading columns; the database keeps 4 + samples
            cols = list(old.columns)
            old = old[SAMPLE_META_COLS + cols[cols.index("Concentration Type") + 1:]]
        if list(new.columns) != list(old.columns) or new.shape != old.shape:
            status = "DIFFERENT (columns or row count)"
        elif new.equals(old):
            status = "identical"
        else:
            key = list(new.columns)
            same = (new.sort_values(key).reset_index(drop=True)
                    .equals(old.sort_values(key).reset_index(drop=True)))
            status = "same rows, other order" if same else "DIFFERENT (values)"
        rows.append((name, status, len(old), len(new)))
    result = pd.DataFrame(rows, columns=["table", "status", "rows_csv", "rows_db"])
    for r in result.itertuples():
        log(f" - {r.table}: {r.status}")
    return result
