# speciate_v5.4_cleanup

## Description

`speciate_v5.4_cleanup` is a Jupyter notebook (`speciate_v5.4_cleanup.ipynb`) that cleans up the `SPECIATE v5.4` database.
`SPECIATE` is a database maintained by the US EPA that contains speciation profiles for organic gases and particulate matter (PM) emitted from various air pollution sources.
More information is available at https://www.epa.gov/air-emissions-modeling/speciate.

## What does the notebook do

Main cleanup steps:

0. Configure paths and settings (first code cell) and build a flat table (one row per profile-species pair) from the SPECIATE Access database (`.accdb`). The table is written to `SPECIATE_Profiles_All.csv` and reused if it already exists. The species name (`SPECIES_NAME`) becomes `orig_name`.

1. Check `orig_name`, CAS, CAS no hyphen, and SPECIES_NAMES for odd characters (`»`) and synonym patterns, keep the first synonym, and remove mixtures (names or CAS values containing `;`, `/`, `+`, or `&`). The original values are kept in `orig_name_Original` and `SPECIES_NAMES_Original`.

2. Create the `weight_fraction` column from `WEIGHT_PERCENT` (divided by 100).

3. Format CAS: create the `cas` column from `CAS no hyphen`, with missing values kept as real nulls and converted to text before exports to avoid unwanted Excel conversion.

4. Retrieve PubChem data (built in; no separate tool needed):

- Look up each unique `orig_name`, SPECIES_NAMES, `cas`, DSSTox_ID, and Smiles Notation combination via the PubChem PUG REST API (CAS first, then SMILES, then name, then SPECIES_NAMES) to get the PubChem name (`name`), IUPAC name, and InChIKey.
- Requests are rate limited (adapts to the `X-Throttling-Control` header), run in parallel, and cached in `cache/PubChem_lookup_cache.csv`, so the step is resumable and safe to interrupt and re-run.

5. Save the cleaned SPECIATE (intermediate) as a CSV file if needed.

6. Merge the PubChem data (`name`, `inchikey`, `IUPACName`, `CID`, `Lookup_method`) into the table.

7. Remove compounds:

- With no InChIKey values.
- With specific InChIKey values (e.g., mixtures, inorganic compounds & inorganic mixtures, etc.), from the shared list in `../inquire_common/filters/`.
- With unwanted keywords (e.g., mixtures, minerals, inorganic compounds & inorganic mixtures, etc.), from the shared keyword lists `keywords_common.txt` and `keywords_speciate.txt`, except for protected compound names (`keyword_exceptions.txt`).

8. Sort the filtered SPECIATE (by CATEGORY_LEVEL_1_Generation_Mechanism, PROFILE_CODE, weight_fraction, and name) and save it as a CSV file.

9. Show descriptive statistics and save per-compound statistics (one row per `cas`) as a CSV file.

## Prerequisites

1. Python 3 (https://www.python.org/downloads/) with the packages `pandas`, `numpy`, `chardet`, `requests`, and `access-parser` (`pip install access-parser`, a pure-Python `.accdb` reader).
2. The notebook is run in JupyterLab (https://jupyter.org/), or any other Jupyter-compatible environment.
3. The shared `inquire_common` folder (utilities, PubChem client, and filter lists), located in the parent folder of the notebook.
4. The SPECIATE 5.4 Access database (`SPECIATE 5.4 2025-09-08.accdb`, see `../original_databases/README.md`). By default it is expected in `../original_databases/final_speciate_5.4_2025-09-08` (relative to the notebook); change `ACCDB_PATH` in the configuration cell if needed.
5. Internet access for the PubChem step (https://pubchem.ncbi.nlm.nih.gov/).

## How to use the notebook

1. Edit the settings in the configuration cell if needed:

- `ACCDB_PATH`: the SPECIATE Access database. To start from a ready-made flat CSV instead, set `CSV_PATH` to it (the same columns are expected).
- `OUTPUT_DIR` / `CACHE_DIR`: output (`speciate_cleaned`) and cache (`cache`) folders, created next to the notebook.
- `LOOKUP_LIMIT`: set to e.g. 50 for a quick test run of the PubChem lookups; `None` runs all compounds.
- `MAX_REQ_PER_SEC`, `N_WORKERS`, and `CHUNK`: PubChem request rate (<= 5 requests/second is requested by PubChem), number of parallel workers, and number of compounds per cache write.

2. Run the notebook cell by cell (or all cells). The first PubChem run takes a while; later runs reuse the cache.

## Output files

All files are written to `speciate_cleaned/`:

| File | Description |
| --- | --- |
| `SPECIATE_Profiles_All.csv` | Flat table built from the Access database (step 0) |
| `SPECIATE_Profiles_All_01_Fltrd.csv` | Cleaned table before InChIKey/keyword filtering |
| `SPECIATE_Profiles_All_02_Fltrd.csv` | Final filtered table |
| `SPECIATE_Profiles_All_03_CAS_Profile_Composition.csv` | Per-compound statistics |

## License

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
