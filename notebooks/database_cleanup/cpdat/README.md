# cpdat_v4.0_cleanup

## Description

`cpdat_v4.0_cleanup` is designed to clean the `CPDat v4.0` database up.
`CPDat (Chemical and Products Database)` is a collection of commercial use information for thousands of chemicals.
More information and downloadable files are available at https://doi.org/10.23645/epacomptox.5352997.v5.

## What does the notebook do

Main cleanup steps (`cpdat_v4.0_cleanup.ipynb`):

1. Configure paths and settings (first code cell) and load the CPDat product composition CSV (`cpdat_v4.0_product_composition_data.csv`).

2. Drop rows with no values in both `cas` and `name` columns (renamed from `curated_casrn` and `curated_chemical_name` after loading; `raw_chemical_name` becomes `orig_name`).

3. Check product_title column values and replace if missing/NaN/NA/etc. `MISSING_VALUES = ["", " ", "-", "—", "–", "NA", "NaN", "nan", "N/A", "n/a"]`. Fill missing product_title first from data_document_title, then from product_upc columns.

4. Retrieve InChIKeys and SMILES from PubChem (built in; no separate tool needed):

- This replaces the former manual run of `PubChem_retriever/PubChem_Retriever.py` on the CPDat table.
- Look up each unique `cas`, `dtxsid`, and `name` combination via the PubChem PUG REST API (CAS# first, then DTXSID, then name), using the shared client in `../inquire_common/pubchem.py`.
- Requests are rate limited (adapts to the `X-Throttling-Control` header), run in parallel, and cached in `cache/PubChem_lookup_cache.csv`, so the step is resumable and safe to interrupt and re-run.
- The columns `inchikey`, `smiles`, `pubchem_cid`, and `pubchem_lookup_method` are added before `dtxsid`.

5. Create weight_fraction column with midpoint values of lower_weight_fraction, upper_weight_fraction, and central_weight_fraction values, and save the intermediate table.

6. Remove compounds:

- With no InChIKey values.
- With specific InChIKey values (e.g., mixtures, inorganic compounds & inorganic mixtures, etc.), from the shared list in `../inquire_common/filters/`.
- With unwanted keywords (e.g., mixtures, minerals, inorganic compounds & inorganic mixtures, etc.), from the shared keyword lists `keywords_common.txt` and `keywords_cpdat.txt`, except for protected compound names (`keyword_exceptions.txt`).

7. Shorten & rename general product use category (puc_general_category) values.

8. Populate puc_product_type missing values:

- Extract use-related keyword from puc_product_family based on puc_product_family → product_title keyword matching.
- Extract use-related keyword from product_title.
- Fallback to puc_product_family value.
- Final fallback to puc_general_category value.
- Infer unknown keyword when all four PUC cols are missing.

9. Additional PUC columns cleanup:

- Singularization / canonical cleanup of puc_product_type.
- Replace 'and' with '&' in puc_product_family and puc_product_type.
- Apostrophe vs. prime vs. mojibake character normalization.
- Final puc_product_type unconditional replacements (phrase-level).
- Convert selected PUC columns (puc_kind, puc_product_family, puc_product_type) to Title Case.
- Final cleanup and conditional replacements for PUC columns.

10. Fill empty puc_product_type cells with 'Unknown' and replace all other missing values in all PUC columns with 'NoID'.

11. Create and populate puc_harmonized column in a format 'puc_kind | puc_general_category | puc_product_family | puc_product_type'.

12. Sort and save filtered CPDat as CSV file, show descriptive statistics, and save summary tables.

## Prerequisites

1. Python 3 (https://www.python.org/downloads/) with the packages `pandas`, `numpy`, and `requests`.
2. The notebook is run in JupyterLab (https://jupyter.org/), or any other Jupyter-compatible environment.
3. The shared `inquire_common` folder (utilities, PubChem client, and filter lists), located in the parent folder of the notebook.
4. The CPDat v4.0 files (https://doi.org/10.23645/epacomptox.5352997.v5). By default `cpdat_v4.0_product_composition_data.csv` is expected in `../original_databases/cpdat_v4.0` (relative to the notebook); change `CSV_PATH` in the configuration cell if needed.
5. Internet access for the PubChem step (https://pubchem.ncbi.nlm.nih.gov/).

## How to use the notebook

1. Edit the settings in the configuration cell if needed:

- `CSV_PATH`: the raw CPDat product composition CSV file.
- `OUTPUT_DIR` / `CACHE_DIR`: output (`cpdat_cleaned`) and cache (`cache`) folders, created next to the notebook.
- `LOOKUP_LIMIT`: set to e.g. 50 for a quick test run of the PubChem lookups; `None` runs all compounds.
- `MAX_REQ_PER_SEC` and `N_WORKERS`: PubChem request rate (<= 5 requests/second is requested by PubChem) and number of parallel workers.

2. Run the notebook cell by cell (or all cells). The first PubChem run takes a while; later runs reuse the cache.

## Output files

Written to `cpdat_cleaned/`:

| File | Description |
| --- | --- |
| `cpdat_v4.0_products_PubChem_Fltrd.csv` | Cleaned table with PubChem data, before InChIKey/keyword filtering |
| `cpdat_v4.0_products_PubChem_KeyFltrd.csv` | After InChIKey/keyword filtering |
| `cpdat_v4.0_products_PubChem_KeyFltrd_ProdType.csv` | After PUC cleanup and `puc_product_type` population |
| `cpdat_v4.0_products_PubChem_KeyFltrd_PUC_harm.csv` | Final table with the `puc_harmonized` column |
| `cpdat_puc_summary.csv` | Unique values of the PUC columns |
| `cpdat_cas_product_composition_summary.csv` | Per-compound statistics (one row per `cas`) |

## License

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
