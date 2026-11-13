-- INQUIRE_CSI Part 1 database (SQLite). Built by notebooks/csi_db.py at the end of
-- INQUIRE_CSI_Pt1_Preprocessing.ipynb. Rebuilt from scratch on every Part 1 run.
--
-- Tables hold each fact once (normalized). The views named v_<file name> reproduce the
-- flat CSV files of Part 1 column by column and in the same row order; they are the
-- user-facing layer (query them, or open the CSV/Excel copies in preprocessing_out/inspection/).
-- Multi-valued cells of the CSV files ("; " separated) are stored as one row per value
-- with a `position` column that keeps the original order.
--
-- Not in the database (kept as files only): the raw per-database copies in
-- databases_id_w_suffix/ and databases_standardized/<database>_standardized.csv.
-- Wide sample tables (one column per sample) are built by csi_db.py from the long tables.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- sources

CREATE TABLE source_origin (
    source_origin TEXT PRIMARY KEY,            -- e.g. CPDAT, FOODB
    id_suffix     TEXT                         -- e.g. _CPD, _FDB (NULL for unknown origins)
);

CREATE TABLE source_class (
    source_class        TEXT PRIMARY KEY,      -- "Domain | Type"
    source_class_domain TEXT NOT NULL          -- "Domain" (first part of source_class)
);

CREATE TABLE source (                          -- one row per source (all sources, before aggregation)
    source_id               TEXT PRIMARY KEY,  -- with database suffix, e.g. 12345_CPD
    source_name             TEXT,
    source_origin           TEXT NOT NULL REFERENCES source_origin (source_origin),
    source_kind             TEXT,
    source_general_category TEXT,
    source_harmonized       TEXT,
    source_class            TEXT NOT NULL REFERENCES source_class (source_class)
);

-- ---------------------------------------------------------------- compounds

CREATE TABLE compound (                        -- every InChIKey in any source database
    inchikey     TEXT PRIMARY KEY,
    feature_name TEXT                          -- preferred name
);

CREATE TABLE compound_name (                   -- all distinct names, main names first
    inchikey TEXT    NOT NULL REFERENCES compound (inchikey),
    position INTEGER NOT NULL,
    name     TEXT    NOT NULL,
    PRIMARY KEY (inchikey, position)
);

CREATE TABLE compound_cas (
    inchikey TEXT    NOT NULL REFERENCES compound (inchikey),
    position INTEGER NOT NULL,
    cas      TEXT    NOT NULL,
    PRIMARY KEY (inchikey, position)
);

CREATE TABLE compound_dtxsid (
    inchikey TEXT    NOT NULL REFERENCES compound (inchikey),
    position INTEGER NOT NULL,
    dtxsid   TEXT    NOT NULL,
    PRIMARY KEY (inchikey, position)
);

-- ---------------------------------------------------------------- source x compound

-- One row per source x compound of the standardized database. The two flags tell which
-- rows survive the later steps (a row in the masked table is always also aggregated).
CREATE TABLE source_compound (
    source_id     TEXT    NOT NULL REFERENCES source (source_id),
    inchikey      TEXT    NOT NULL REFERENCES compound (inchikey),
    in_aggregated INTEGER NOT NULL DEFAULT 0 CHECK (in_aggregated IN (0, 1)),
    in_masked     INTEGER NOT NULL DEFAULT 0 CHECK (in_masked IN (0, 1)),
    CHECK (in_masked = 0 OR in_aggregated = 1),
    PRIMARY KEY (source_id, inchikey)
);
CREATE INDEX ix_source_compound_inchikey ON source_compound (inchikey);

-- Equivalence groups: which sources were merged into which representative.
CREATE TABLE source_group (
    stage             TEXT NOT NULL CHECK (stage IN ('aggregated', 'masked')),
    representative_id TEXT NOT NULL REFERENCES source (source_id),
    member_id         TEXT NOT NULL REFERENCES source (source_id),
    masked_hash       TEXT,                    -- masked stage only
    hh_household      TEXT,                    -- masked stage only; own household products
    PRIMARY KEY (stage, member_id)
);

-- ---------------------------------------------------------------- samples

CREATE TABLE sample (
    sample_id TEXT PRIMARY KEY,
    position  INTEGER NOT NULL                 -- column order in the sample table
);

CREATE TABLE detected_compound (               -- row attributes of the sample table
    inchikey           TEXT PRIMARY KEY,
    feature_name       TEXT,
    compound_class     TEXT,
    concentration_type TEXT,
    position           INTEGER NOT NULL        -- row order in the sample table
);

CREATE TABLE sample_compound (                 -- long format; missing = not measured (no row)
    sample_id     TEXT NOT NULL REFERENCES sample (sample_id),
    inchikey      TEXT NOT NULL REFERENCES detected_compound (inchikey),
    concentration REAL NOT NULL,
    PRIMARY KEY (sample_id, inchikey)
);
CREATE INDEX ix_sample_compound_inchikey ON sample_compound (inchikey);

-- ================================================================ views
-- v_<name> is exported as <name>.csv

CREATE VIEW v_sources_meta_standardized AS
SELECT s.source_id, s.source_name, s.source_origin, s.source_kind, s.source_general_category,
       s.source_harmonized, s.source_class, c.source_class_domain
FROM source AS s
JOIN source_class AS c USING (source_class)
ORDER BY s.rowid;

CREATE VIEW v_all_sources_standardized AS
SELECT s.source_id, s.source_name, sc.inchikey, s.source_origin, s.source_kind,
       s.source_general_category, s.source_harmonized, s.source_class, c.source_class_domain
FROM source_compound AS sc
JOIN source AS s USING (source_id)
JOIN source_class AS c USING (source_class)
ORDER BY sc.rowid;

CREATE VIEW v_all_sources_aggregated AS
SELECT s.source_id, s.source_name, sc.inchikey, s.source_origin, s.source_kind,
       s.source_general_category, s.source_harmonized, s.source_class, c.source_class_domain
FROM source_compound AS sc
JOIN source AS s USING (source_id)
JOIN source_class AS c USING (source_class)
WHERE sc.in_aggregated = 1
ORDER BY sc.rowid;

CREATE VIEW v_sources_masked AS
SELECT s.source_id, s.source_name, sc.inchikey, s.source_origin, s.source_kind,
       s.source_general_category, s.source_harmonized, s.source_class, c.source_class_domain
FROM source_compound AS sc
JOIN source AS s USING (source_id)
JOIN source_class AS c USING (source_class)
WHERE sc.in_masked = 1
ORDER BY sc.rowid;

CREATE VIEW v_counts_masked AS
SELECT source_id, COUNT(*) AS n_compound_rows
FROM source_compound
WHERE in_masked = 1
GROUP BY source_id
ORDER BY source_id;

CREATE VIEW v_valid_sources_masked AS
SELECT source_id
FROM source_compound
WHERE in_masked = 1
GROUP BY source_id
ORDER BY source_id;

CREATE VIEW v_all_compounds_standardized AS
SELECT c.inchikey,
       c.feature_name,
       (SELECT group_concat(name, '; ') FROM
           (SELECT name FROM compound_name AS n WHERE n.inchikey = c.inchikey ORDER BY position)
       ) AS all_feature_names,
       (SELECT group_concat(cas, '; ') FROM
           (SELECT cas FROM compound_cas AS n WHERE n.inchikey = c.inchikey ORDER BY position)
       ) AS cas,
       (SELECT group_concat(dtxsid, '; ') FROM
           (SELECT dtxsid FROM compound_dtxsid AS n WHERE n.inchikey = c.inchikey ORDER BY position)
       ) AS dtxsid
FROM compound AS c
ORDER BY c.rowid;

CREATE VIEW v_equivalence_groups_members AS
SELECT r.source_origin, r.source_harmonized,
       g.representative_id AS eqsetID, g.member_id AS sourceID
FROM source_group AS g
JOIN source AS r ON r.source_id = g.representative_id
WHERE g.stage = 'aggregated'
ORDER BY g.rowid;

CREATE VIEW v_equivalence_groups_summary AS
SELECT r.source_origin, r.source_kind, r.source_general_category, r.source_harmonized,
       r.source_id AS eqsetID,
       (SELECT COUNT(*) FROM source_group AS m
         WHERE m.stage = 'aggregated' AND m.representative_id = r.source_id) AS n_sources,
       (SELECT group_concat(member_id, '; ') FROM
           (SELECT member_id FROM source_group AS m
             WHERE m.stage = 'aggregated' AND m.representative_id = r.source_id
             ORDER BY member_id)) AS source_ids,
       (SELECT group_concat(source_name, '; ') FROM
           (SELECT DISTINCT s.source_name FROM source_group AS m
              JOIN source AS s ON s.source_id = m.member_id
             WHERE m.stage = 'aggregated' AND m.representative_id = r.source_id
               AND s.source_name IS NOT NULL
             ORDER BY s.source_name)) AS source_names
FROM source AS r
WHERE r.source_id IN (SELECT representative_id FROM source_group WHERE stage = 'aggregated')
ORDER BY (SELECT MIN(rowid) FROM source_group
           WHERE stage = 'aggregated' AND representative_id = r.source_id);

CREATE VIEW v_masked_equivalence_groups_members AS
SELECT g.representative_id AS masked_eqsetID, g.member_id AS source_id,
       s.source_origin, s.source_kind, s.source_general_category, s.source_harmonized,
       g.hh_household, g.masked_hash
FROM source_group AS g
JOIN source AS s ON s.source_id = g.member_id
WHERE g.stage = 'masked'
ORDER BY g.rowid;

-- Long format of the per-sample compound universes (concentration > 0). The wide
-- sample_universes.csv is built from this view by csi_db.py.
CREATE VIEW v_sample_detections AS
SELECT sa.sample_id, sc.inchikey
FROM sample_compound AS sc
JOIN sample AS sa USING (sample_id)
WHERE sc.concentration > 0
ORDER BY sa.position, sc.inchikey;
