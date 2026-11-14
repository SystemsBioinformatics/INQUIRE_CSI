# Part 1 – INQUIRE_CSI_Pt1_Preprocessing

## Purpose

Part 1 prepares all data for the source identification in Part 2. It
1. cleans and harmonizes six source data sets into **one master contaminant source database (MCSDB)** with a common set of columns,
2. adds two harmonized reporting levels (`source_class`, `source_class_domain`) from a mapping file,
3. builds one lookup table of all compounds of all source databases (InChIKey, names, CAS numbers, DTXSIDs),
4. merges sources that contain exactly the same compounds (so that the optimization does not have to choose between identical sources),
5. keeps only the compounds that actually occur in the samples ("masking") and merges sources that become identical after masking,
6. converts the sample data into one **compound universe** per sample (the list of InChIKeys detected in that sample),
7. stores all results in one **SQLite database** (input of Part 2) and writes CSV/Excel copies for inspection.

## Inputs

From `data/preprocessing_in/` (set by `config.yaml`; the folder must exist, otherwise Part 1 stops with an error); formats and mandatory columns in [input_data.md](input_data.md):

| Input | File |
|---|---|
| Sample data | `Sample_Data.xlsx` |
| Own household products + metadata | `Own_Household_Products.csv`, `Own_Household_Products_Metadata.csv` |
| Literature consumer products | `Literature_Products.csv` |
| CPDat | `CPDat/product_compositions.tsv`, `products.tsv`, `product_use_categories.tsv` |
| FooDB | `FooDB.csv` (tab-separated) |
| SPECIATE | `SPECIATE.xlsx` |
| SPECIEUROPE | `SPECIEUROPE.xlsx` |
| Source class mapping | `lookups/source_class_mapping.xlsx` |

All outputs are written to `data/preprocessing_out/` (created automatically; paths below are relative to it).

## Outputs

| Folder / file | Content | Used by |
|---|---|---|
| `databases_id_w_suffix/*.csv` | Each database with its database-specific ID suffix; only written if `EXPORT_TRACE_TABLES = True` | traceability |
| `databases_standardized/all_sources_standardized.csv` | All sources in the harmonized schema incl. `source_class`, `source_class_domain`; one row per source × compound (before aggregation) | traceability, Zenodo |
| `databases_standardized/sources_meta_standardized.csv` | Metadata (name, origin, kind, category, harmonized label, class, class domain) of **all** sources; one row per source | **Part 2** |
| `databases_standardized/all_compounds_standardized.csv` | One row per compound (InChIKey) of all source databases: preferred name, all names, CAS numbers, DTXSIDs | reference, Zenodo |
| `databases_standardized/dust_standardized.csv` | Sample table after removing rows without InChIKey and blank/QC columns | **Part 2** (compound names) |
| `databases_standardized/<database>_standardized.csv` | Each database separately in the harmonized schema (with class columns where possible); only written if `EXPORT_TRACE_TABLES = True` | traceability, Zenodo |
| `databases_standardized/equivalence_groups_members.csv`, `equivalence_groups_summary.csv` | First aggregation: which sources were merged into which representative | traceability |
| `all_sources_aggregated/all_sources_aggregated.csv` | Source database after the first aggregation | traceability, Zenodo |
| `masked_sources/sources_masked.csv` | **Final source database used for the samples**: only compounds found in the samples, after the second aggregation | **Part 2** |
| `masked_sources/masked_equivalence_groups_members.csv` | Second aggregation: members per representative | traceability |
| `masked_sources/counts_masked.csv`, `valid_sources_masked.csv` | Rows (compounds) per source before the last filter; retained sources | QC |
| `masked_sources/sample_universes.csv` | InChIKeys detected per sample (one column per sample) | **Part 2** |
| `lookups/source_class_unmapped.csv`, `source_class_unmapped_std_dbs.csv` | Category keys missing from the mapping file (only written if there are any) | QC |
| **`inquire_csi_pt1.sqlite`** | SQLite database with all Part 1 results except the raw per-database copies (normalized tables and views that reproduce the CSV files; see [codebook, section 2.8](codebook.md#28-sqlite-database-and-inspection-copies) and [schema.sql](schema.sql)) | **Part 2** |
| `inspection/*.csv`, `inspection/inquire_csi_pt1.xlsx` | Read-only CSV copies of all database views and sample tables, and an Excel workbook (tables up to 100,000 rows) | inspection |

The CSV files in the table that are marked for Part 2 are still written, but **Part 2 now reads the same content from the database**. All columns are explained in the [codebook](codebook.md).

## Runtime

About 14 minutes on the test laptop (INQUIRE reference run: 00:13:39). Loading the large CPDat, FooDB, and SPECIATE files and saving the standardized tables take most of the time.

---

## Notebook sections in run order

**0. Title.** Name, purpose and link to this page (no computation).

**1. Reset environment.** Clears all variables of a previous run, so that nothing old is reused by accident.

**2. Imports & setup.** Loads the packages, starts logging (messages appear in the notebook and in `inquire_csi_pt1_preprocessing_log_<yymmdd>.log`), defines helper functions (reading CSV/Excel with automatic encoding fallback over `ENCODINGS`, column checks, whitespace stripping) and sets `GLOBAL_SEED = 1`.

**3. Check necessary columns.** Reads `config.yaml` and sets `DATA_DIR`, `PREP_IN_DIR` and `PREP_OUT_DIR` (stops if the working or input folder does not exist; creates the output folders), reads only the header row of every input file and checks the mandatory columns. Stops with a list of missing and available columns if a column is missing. This is fast and avoids loading large files only to fail later.

**4. Load raw input data.** Loads all files and prints their numbers of rows and columns. SPECIATE profiles named "Overall Average" are removed, because they are averages over many sources, not real sources.

**5. Whitespace cleanup.** First removes leading/trailing spaces from all **column names** (e.g., `"InChIKey "` → `"InChIKey"`; stops if this would create two columns with the same name), then from the **values** of the ID, name, category and InChIKey columns listed in `STRIP_COLUMNS`. Invisible spaces otherwise make identical InChIKeys or categories look different.

**6. InChIKey cleanup.** Cleans the InChIKey column of all six source databases and of the sample data (both the filtered and the full dust table), so that every later step (ID suffixes, standardization, aggregation, masking, sample universes and all saved files) uses the corrected keys:
- all keys are converted to upper case;
- obvious junk is set to missing: empty cells, placeholders ("nan", "NA", "n/a", "null", "-", …), numbers (e.g., "0", "12.5") and values without any letter. These rows are later removed like any other row without an InChIKey;
- a digit "0" is replaced by the letter "O" (real InChIKeys contain only the letters A–Z and hyphens, never digits);
- keys that still do not match the standard format (14 letters – 10 letters – 1 letter) are **kept** and only listed in the log.

The tables to clean are set in `INCHIKEY_DFS`, the possible names of the InChIKey column in `INCHIKEY_COL_NAMES` (`inchikey`, `InChIKey`, `InChiKey`; found automatically). A table that does not exist or has no InChIKey column is skipped with a warning.

**7. Working copies and ID suffixes.** Creates working copies and adds a database suffix to every source ID: `_CPD` (CPDat), `_HHP` (own household products), `_COP` (literature consumer products), `_FDB` (FooDB), `_SUS` (SPECIATE), `_SEU` (SPECIEUROPE). The suffixed tables are saved in `databases_id_w_suffix/` if `EXPORT_TRACE_TABLES = True`.

**8. Standardize and harmonize the source databases.** Converts every database to the common schema `source_id, source_name, inchikey, source_origin, source_kind, source_general_category, source_harmonized` (mapping per database in [input_data.md, section 2](input_data.md#2-source-databases-part-1)). Specific steps:
- CPDat: keeps one product-use category (PUC) per product and adds product titles as names.
- FooDB: if a food contains the same compound several times (e.g., "Niacin" and "Niacin, from tryptophan"), keeps only the entry with the highest content.
- SPECIATE/SPECIEUROPE: build `source_harmonized` as "level 1 | level 2 | level 3" of the profile classification.
- All databases are concatenated; rows without InChIKey are removed.

**9. Add reporting classes and clean the standardized tables.** Reads `lookups/source_class_mapping.xlsx` and adds `source_class` ("Domain | Type") and `source_class_domain` ("Domain") to every source by matching origin, kind, general category and harmonized label ([input_data.md, section 3](input_data.md#3-source-class-mapping-part-1)). Sources missing from the mapping are labelled "Unmapped Sources" and listed in `lookups/source_class_unmapped.csv`. The same classes are added to the separate standardized databases; from those, the uninformative columns `ID` and `#` are dropped, and, optionally (`DROP_EMPTY_COLS_STD`), completely empty columns. These reporting classes do **not** affect the aggregation, the priors or the optimization.

**10. Standardize source metadata; save standardized databases.** Builds the metadata table of all sources (missing kind/category/harmonized labels → "Unknown") and saves it as `sources_meta_standardized.csv` with **one row per source** (the first row per `source_id` is kept; the log warns if a source has more than one set of metadata). Saves all standardized tables to `databases_standardized/`.

**11. Build the all-compounds lookup.** Collects, for every InChIKey in any of the six source databases (before aggregation and masking), its names, CAS numbers and DTXSIDs (US EPA CompTox substance IDs), and saves them as `databases_standardized/all_compounds_standardized.csv`. The table is a reference for users (e.g., to look up names or identifiers of compounds in the results); the identification in Part 2 does not use it.
- **Columns used per database** are set in `COMPOUND_COLS` (e.g., `Feature_Name`, `Raw_Name`, `PubChem_Name`, `Raw_CAS`, `DTXSID` for the product files; `Feature name`, `Name_Original`, `CAS#`, `DSSTox_ID` for SPECIATE/SPECIEUROPE; `orig_feature_name_cpd`, `feature_name_pubchem`, `iupac_name_pubchem`, `cas` for FooDB; `curated_chemical_name` for CPDat). These columns are optional: a missing column is logged and skipped ([input_data.md](input_data.md)).
- **`feature_name`** (one preferred name per compound) is taken from the first database in `FEATURE_NAME_PRIORITY` (default: CPDat, SPECIATE, SPECIEUROPE, FooDB, literature products, own household products) that has a name for the compound; within that database the most frequent name is used. **`all_feature_names`**, **`cas`** and **`dtxsid`** list all distinct values found, separated by `MULTI_SEP` ("; ").
- **Cleaning:** placeholder text ("nan", "NA", "-", "0", …) is treated as missing; CAS numbers stored without hyphens are reformatted (e.g., `117817` → `117-81-7`) and only valid CAS and DTXSID patterns are kept. The InChIKeys are cleaned with the same rules as in step 6 (junk skipped, digit "0" → letter "O", non-standard keys kept and reported in the log), so the keys in this table match those in `sources_masked.csv`, the sample data and the results.

**12. Aggregate equivalent sources (first aggregation).** Many sources, especially in CPDat, contain exactly the same set of compounds and are indistinguishable for the optimization. This step:
- computes a fingerprint (hash) of the compound set of every source;
- groups sources with the **same compound set AND the same origin, kind, general category and harmonized label** (`GROUP_META_COLS`); sources from different databases or categories are never merged, so no category information is lost;
- keeps one **representative** per group: the source with the most complete metadata; ties → alphabetically first `source_id`;
- prints diagnostics (largest groups, an equality check of two members, reduction per origin) and saves the group membership so that every merged source can be traced back.

The next two cells print column statistics before and after aggregation and save `all_sources_aggregated/all_sources_aggregated.csv`.

**13. Reshape sample data and build per-sample compound universes.** Removes rows without InChIKey; if `DROP_QC_COLUMNS = True`, removes the blank/QC columns listed in `dust_cols_drop` (and warns if a column containing "blank" or starting with "7S_CS" remains) and saves `dust_standardized.csv`. Then builds, for every sample column (all columns right of `Concentration Type`), the sorted list of InChIKeys with a value > 0: the **compound universe** of that sample.

**14. Mask sources to sample compounds and second aggregation.** Removes from every source all compounds that do not occur in **any** sample; sources left without compounds are dropped. After masking, many sources become identical again (e.g., two CPDat products that differed only in compounds never found in the samples). With `REAGGREGATE_AFTER_MASKING = True` they are merged with the same rules as in step 12. **Own household products with different sample keys are never merged** (key `LLNN` read from the product ID `LLNN_CPnn_HHP`), because Part 2 needs each product's key to prefer it for the samples with the same key. The masked database, merge table, counts and list of valid sources are saved in `masked_sources/`.

**15. Save sample universes.** Writes `masked_sources/sample_universes.csv`: one row per InChIKey found in any sample, one column per sample; a cell contains the InChIKey if detected in that sample, otherwise `NA`.

**16. Build the SQLite database and the inspection copies.** Imports `notebooks/csi_db.py` and builds `inquire_csi_pt1.sqlite` from the CSV files written in the previous steps (schema in [schema.sql](schema.sql); tables and views in [codebook, section 2.8](codebook.md#28-sqlite-database-and-inspection-copies)). Every source, compound and sample value is stored once; the three flat source tables (standardized, aggregated, masked) become one `source_compound` table with the flags `in_aggregated` and `in_masked`. The database is written to a temporary file and renamed at the end, so an interrupted run never leaves a half-built database. The same cell writes a CSV copy of every view to `inspection/` and, with `EXPORT_EXCEL = True`, one Excel workbook; with `VERIFY_AGAINST_CSV = True` it compares every view with the original CSV file cell by cell and stops with an error if one differs. The raw per-database copies (`databases_id_w_suffix/`, `<database>_standardized.csv`) are kept as files only. Only Part 1 results are in the database; Part 2 still writes CSV files.

---

## User-settable parameters

| Parameter | Cell | Default | Meaning | When to change |
|---|---|---|---|---|
| `config.yaml` (`data_dir`, `folders`) | Check columns | `data`; `preprocessing_in`, `preprocessing_out` | Working folder; Part 1 reads `PREP_IN_DIR` and writes `PREP_OUT_DIR` | Different folder or folder names: edit `config.yaml`, not the notebook |
| Input file names | Check columns / Load raw input data | see Inputs | Names of the input files | Other file names |
| `GLOBAL_SEED` | Imports & setup | 1 | Random seed (no random step in Part 1; kept for consistency) | – |
| `ENCODINGS` | Imports & setup | utf-8, utf-8-sig, cp1252, cp1250, latin1 | Text encodings tried, in this order | Files in other encodings |
| `STRIP_COLUMNS` | Whitespace cleanup | ID, name, category and InChIKey columns of all databases | Columns whose values are stripped of spaces | New databases or renamed columns |
| `INCHIKEY_DFS` | InChIKey cleanup | all six source databases + both dust tables | Tables whose InChIKeys are cleaned | New databases |
| `INCHIKEY_COL_NAMES` | InChIKey cleanup | `inchikey`, `InChIKey`, `InChiKey` | Possible names of the InChIKey column | InChIKey column with another name |
| `INCHIKEY_MISSING` | InChIKey cleanup | "", "nan", "none", "na", "n/a", "null", "<na>", "-", "--" | Placeholder values treated as missing | Other placeholders in your files |
| `INCHIKEY_STANDARD` | InChIKey cleanup | `[A-Z]{14}-[A-Z]{10}-[A-Z]` | Standard InChIKey format; only used to report odd keys | – |
| `SOURCE_CLASS_FILE`, `SOURCE_CLASS_SHEET` | Add reporting categories | `preprocessing_in/lookups/source_class_mapping.xlsx` (`LOOKUP_IN_DIR`), `source_class_mapping` | Mapping file and sheet for `source_class` / `source_class_domain` | Other mapping file |
| `DROP_EMPTY_COLS_STD` | Add reporting categories | `False` | `True` drops completely empty columns from the separate standardized databases (core columns are protected) | Smaller output files |
| `DROP_COLS_STD` | Add reporting categories | `["ID", "#"]` | Columns dropped from the separate standardized databases | Other uninformative columns |
| `COMPOUND_COLS` | Save all compounds | name, CAS and DTXSID columns per database (see step 11) | Which input columns feed the all-compounds lookup | Other column names in your source files |
| `FEATURE_NAME_PRIORITY` | Save all compounds | CPDat, SPECIATE, SPECIEUROPE, FooDB, literature products, own household products | Order in which databases are checked for the preferred `feature_name` | Prefer names from another database |
| `MULTI_SEP` | Save all compounds | `"; "` | Separator between several values in one cell | – |
| `GROUP_META_COLS` | Aggregate equivalent products/sources | kind, general category, harmonized label | Columns that must be identical for two sources to be merged (in addition to origin and compound set) | Not recommended (categories would be lost) |
| `dust_cols_drop` | Reshape sample data | `7S_CS_01` … `7S_CS_04`, `Blank_NIST` (example) | Names of blank/QC sample columns | **Always** replace with your own blank/QC columns |
| `DROP_QC_COLUMNS` | Reshape sample data | `True` | `True` removes the columns in `dust_cols_drop` and saves `dust_standardized.csv`. `False` keeps them; they are then analyzed as samples, and the sample table is saved as `dust_standardized_qc_cols.csv` (see note) | `False` only to inspect blanks on purpose |
| `REAGGREGATE_AFTER_MASKING` | Mask products/sources | `True` | Second aggregation after masking | `False` only as a check |
| `EXPORT_EXCEL` | Build SQLite database | `True` | Also write `inspection/inquire_csi_pt1.xlsx` (tables with more than 100,000 rows are CSV only; `excel_max_rows` in `csi_db.export_all`) | `False` for faster runs with large databases |
| `VERIFY_AGAINST_CSV` | Build SQLite database | `True` | Check that every database view equals its original CSV file | `False` only to save time on large runs |
| `EXPORT_TRACE_TABLES` | Working copies and ID suffixes | `True` | `True` also writes the per-database traceability files `databases_id_w_suffix/*.csv`, `databases_standardized/<database>_standardized.csv` and `cpdat_*_standardized.csv` (traceability, Zenodo); they are not read by the SQLite database or Part 2. The other files in `databases_standardized/` are always written | `False` to save time and disk space |
| `DB_FILE`, `INSPECT_DIR` | Build SQLite database | `PREP_OUT_DIR/inquire_csi_pt1.sqlite`, `PREP_OUT_DIR/inspection` | Location of the database and the inspection copies | – |

**NB!** With `DROP_QC_COLUMNS = False`, Part 1 writes `dust_standardized_qc_cols.csv`, but Part 2 reads `dust_standardized.csv` (only used for compound names). Part 2 then uses an older `dust_standardized.csv` if one exists, or stops if none exists. The sample universes, which Part 2 analyzes, always follow the setting.

---

## Checks to look at

| Cell | What to look for | Interpretation |
|---|---|---|
| Check columns | "column check passed" for every file | Otherwise fix the column names in the input file |
| Load data | Row numbers as expected (compare with the [reference run](method_and_limitations.md#2-reference-run)) | Far fewer rows → wrong file or separator |
| Whitespace cleanup | Which columns were cleaned; "Column names already clean" | Information only |
| InChIKey cleanup | Per table: rows with junk set to missing, keys corrected "0" → "O" (first 5 shown), non-standard keys kept (first 5 shown); no "not found"/"no InChIKey column" warnings | Many junk rows or non-standard keys → check the InChIKeys in that input file |
| Standardize | Number of FooDB semi-duplicates removed; unified source rows and unique source IDs | Large unexpected changes → check input |
| Reporting classes | "all_sources_0 mapped to a source_class"; no "Unmapped Sources" warnings | Unmapped keys → add them to the mapping file (see `preprocessing_out/lookups/source_class_unmapped.csv`) |
| Standardize source metadata | "rows → … unique sources saved"; no warning about sources with more than one metadata row | A warning means one `source_id` carries different names or categories in the input; the first row is kept |
| SQLite database | Rows per table in the log; every file "identical" in the comparison | "DIFFERENT" stops the run: the database does not reproduce that CSV file, report it (do not use the database) |
| All-compounds lookup | Number of compounds and how many have a name, CAS and DTXSID; warnings about missing columns; junk, corrected and non-standard InChIKeys (same as in the InChIKey cleanup) | Missing columns are expected if your source files lack them; many corrected or non-standard keys → check the InChIKeys in the input |
| Aggregation | Reduction per origin; largest equivalence groups; "Equality check … True" for members of one group | The largest groups are typically CPDat products with one compound and "Unknown" category |
| Reshape sample data | "No blank/QC columns left" and **number of samples** | Must equal the number of real samples |
| Mask sources | Sources before/after re-aggregation per origin; remaining sources | `HOUSEHOLD_PRODUCTS` should hardly shrink (only identical products with the same sample key `LLNN` are merged) |

## Common errors

| Message | Cause | Solution |
|---|---|---|
| `FileNotFoundError: Working folder not found` | `data_dir` in `config.yaml` wrong | Correct `data_dir` in `config.yaml` |
| `FileNotFoundError: Input folder not found` | `data/preprocessing_in/` does not exist | Create it and copy the input files into it |
| `ValueError: [<dataset>] missing columns: …` | Column names in the input differ from the expected ones | Rename the columns in the input file (case-sensitive) or adapt the check and the mapping cell |
| `[source_class mapping] missing columns` | The mapping sheet is not the first sheet, or columns are missing | Make `source_class_mapping` the first sheet; check the six columns |
| `source_class mapping has … rows with the same key but different classes` | Duplicate keys with conflicting classes in the mapping file | Keep one class per key |
| `RuntimeError: Unable to decode header…` | Unusual text encoding | Save the file as UTF-8 or add the encoding to `ENCODINGS` |
| FooDB loads as one column | File is tab-separated; separator changed | Keep `sep="\t"` for `FooDB.csv` |
| `ValueError` / `TypeError` in "Add suffixes" | Non-integer `cpdat_product_id` or SPECIEUROPE `PROFILE_CODE` | Clean the ID columns |
| `PermissionError` when saving | Output CSV is open in Excel | Close the file and re-run the cell |
| `MemoryError` / very slow | Not enough RAM | Close other programs; 16 GB RAM recommended |
