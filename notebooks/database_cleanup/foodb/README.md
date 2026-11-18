# foodb_v1.0_cleanup

## Description

`foodb_v1.0_cleanup` is a Jupyter notebook (`foodb_v1.0_cleanup.ipynb`) that cleans up the `FooDB v1.0` database (release 2020-04-07).
`FooDB` is the world's largest and most comprehensive resource on food constituents, chemistry, and biology. It contains information on both macronutrients and micronutrients, including many of the constituents that give foods their flavor, color, taste, texture, and aroma. It covers ca. 70,000 compounds found in ca. 800 food stuffs, linked through a content table that reports compound concentrations in individual foods.
More information is available at https://foodb.ca/.

## What does the notebook do

Main cleanup steps:

1. Configure paths and settings (first code cell) and load the Content CSV file.

2. Enrich the raw Compound table with PubChem data (built in; no separate tool needed):

- Relabel the raw `Compound.csv` columns by position (the 2020-04-07 header does not match the data order) and sanity-check the InChIKey and InChI columns.
- Rename columns to follow other similar databases, e.g., id to cpd_id, name to orig_name, and moldb_iupac to iupac_name.
- Retrieve PubChem names, IUPAC names, and InChIKeys via the PubChem PUG REST API: batched InChIKey lookups first, then a name-based fallback for misses.
- Requests are rate limited (adapts to the `X-Throttling-Control` header), run in parallel, and cached in `cache/PubChem_lookup_cache.csv`, so the step is resumable and safe to interrupt and re-run.
- Save the enriched table as `foodb_cleaned/Compound_FDB_PubChemNames.csv`.

3. Load the Food and enriched Compound CSV files (with encoding detection and fallback encodings if needed).

4. Clean the Food table:

- Rename columns to follow other similar databases, e.g., id to food_id, name to food_name, and public_id to public_food_id.
- Drop unnecessary columns (e.g., picture data, timestamps, creator/updater IDs, export flags, etc.).
- Create and populate a harmonized food group column (`food_group_harmonized`: food_group | food_subgroup | food_type), similar to the CPDat product use category.

5. Clean the Compound table:

- Drop unnecessary columns (e.g., state, annotation_quality, kingdom).
- Detect broken compound names (mojibake) and replace them with existing IUPAC names, PubChem IUPAC names, or PubChem names.
- Remove compounds with no InChIKey values.
- Rename and reorder PubChem columns (`name` for the PubChem name, `iupac_name_pubchem`).

6. Remove compounds:

- With specific InChIKey values (e.g., mixtures, inorganic compounds & inorganic mixtures, isotopically labeled compounds, ions, etc.).
- With unwanted keywords (e.g., mixtures, minerals, metals, inorganic compounds & inorganic mixtures, extracts, etc.), except for protected compound names.

7. Clean the Content table:

- Rename columns to follow other similar databases, e.g., id to cont_id, source_id to cpd_id, and orig_source_name to orig_name.
- Drop unnecessary columns (e.g., citations, timestamps, creator/updater IDs, methods, units expressions, standard content, preparation type, export flag, etc.).
- Remove nutrients (source_type == 'Nutrient') and summary entries (e.g., 'Carbohydrates, total', 'Fat, total (Lipids)', etc.).

8. Populate missing values in the Content table:

- Fill orig_food_common_name within each food_id, then from the Food table.
- Create food_name from the Food table using food_id.
- Fill orig_name from the Compound table using cpd_id.
- Reorder columns (food_name after food_id, cpd_id before orig_name).

9. Remove Content table entries:

- With no food_name or orig_name values.
- With cpd_id not present in the filtered Compound table.
- With empty or zero orig_content values.

10. Show stats (data types, unique values, and missing values per column) for the filtered Food, Compound, and Content tables.

11. Save filtered Food, Compound, and Content tables as CSV files.

12. Merge the filtered tables (Content + Food on food_id, then + Compound on cpd_id):

- Rename overlapping columns with `_food`, `_cont`, and `_cpd` suffixes and reorder columns.
- Create `food_sub_id` (`<food_id>_<nn>`), numbering the distinct orig_food_common_name values within each food_id.
- Show stats and save the merged table as a tab-separated file (`FooDB_Merged.csv`). An Excel export (`FooDB_Merged_XL.xlsx`) is available but commented out.

## Prerequisites

1. Python 3 (https://www.python.org/downloads/) with the packages `pandas`, `numpy`, `chardet`, `openpyxl`, and `requests` (install with `pip install -r requirements.txt`, or create a conda environment with `conda env create -f environment.yml` and `conda activate foodb_cleanup`).
2. The notebook is run in JupyterLab (https://jupyter.org/), or any other Jupyter-compatible environment.
3. FooDB CSV files (`Content.csv`, `Food.csv`, `Compound.csv`), available at https://foodb.ca/downloads. By default they are expected in `../foodb_2020_04_07_csv` (relative to the notebook); change `FOODB_CSV_DIR` in the configuration cell if needed.
4. Internet access for the PubChem enrichment step (https://pubchem.ncbi.nlm.nih.gov/).

## How to use the notebook

1. Edit the settings in the configuration cell if needed:

- `FOODB_CSV_DIR`: folder with the raw FooDB CSV files.
- `OUTPUT_DIR` / `CACHE_DIR`: output (`foodb_cleaned`) and cache (`cache`) folders, created next to the notebook.
- `LOOKUP_LIMIT`: set to e.g. 50 for a quick test run of the PubChem lookups; `None` runs all compounds.
- `MAX_REQ_PER_SEC` and `N_WORKERS`: PubChem request rate (<= 5 requests/second is requested by PubChem) and number of parallel workers.

2. Run the notebook cell by cell (or all cells). The first PubChem enrichment run takes a while; later runs reuse the cache.

## Output files

All files are written to `foodb_cleaned/`:

| File | Description |
| --- | --- |
| `Compound_FDB_PubChemNames.csv` | Raw Compound table with PubChem names and InChIKeys |
| `Food_Fltrd.csv` | Cleaned Food table |
| `Compound_Fltrd.csv` | Cleaned and filtered Compound table |
| `Content_Fltrd.csv` | Cleaned and filtered Content table |
| `FooDB_Merged.csv` | Merged Content, Food, and Compound tables (tab-separated) |

## License

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
