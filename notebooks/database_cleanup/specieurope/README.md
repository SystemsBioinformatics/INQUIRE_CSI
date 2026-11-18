# specieurope_v3.0_cleanup

## Description

`specieurope_v3.0_cleanup` is a Jupyter notebook (`specieurope_v3.0_cleanup.ipynb`) that cleans up the `SPECIEUROPE v3.0` database.
`SPECIEUROPE` is a database of European air pollution source profiles, designed for source apportionment and emission analysis, with species encoding aligned to the US EPA SPECIATE system. It contains ca. 200 particulate chemical profiles (organic and inorganic) derived from measurements, source apportionment studies, composites, and theoretical estimates.
More information is available at https://source-apportionment.jrc.ec.europa.eu/Specieurope/index.aspx.

## What does the notebook do

Main cleanup steps:

1. Configure paths and settings (first code cell), load the SPECIEUROPE CSV file, and rename columns to follow other similar databases, e.g., Relative Mass to weight_fraction, Specie to orig_name, and Id to PROFILE_CODE:

- The CSV has mixed UTF-8 / Windows-1252 encoding, which is decoded run by run.
- The empty column created by the trailing comma on every line is dropped.

2. Check `orig_name` and CAS for odd characters (`»`) and synonym patterns, and remove mixtures (names or CAS values containing `;`, `/`, or `+`). The original name is kept in `orig_name_Original`.

3. Format CAS: create the `cas` column, with missing values kept as real nulls and converted to text before exports to avoid unwanted Excel conversion.

4. Retrieve PubChem data (built in; no separate tool needed):

- Look up each unique `orig_name`, SPECIES_ID, and `cas` combination via the PubChem PUG REST API (CAS first, then name) to get the PubChem name (`name`), IUPAC name, and InChIKey.
- Requests are rate limited (adapts to the `X-Throttling-Control` header), run in parallel, and cached in `cache/PubChem_lookup_cache.csv`, so the step is resumable and safe to interrupt and re-run.

5. Save the cleaned SPECIEUROPE (intermediate) as a CSV file if needed.

6. Merge the PubChem data (`name`, `inchikey`, `IUPACName`, `CID`, `Lookup_method`) into the table.

7. Remove compounds:

- With no InChIKey values.
- With specific InChIKey values (e.g., mixtures, inorganic compounds & inorganic mixtures, etc.), from the shared list in `../inquire_common/filters/`.
- With unwanted keywords (e.g., mixtures, minerals, metals, inorganic compounds & inorganic mixtures, etc.), from the shared keyword lists `keywords_common.txt` and `keywords_specieurope.txt`, except for protected compound names (`keyword_exceptions.txt`).

8. Sort the filtered SPECIEUROPE (by PROFILE_CODE, weight_fraction, and name) and save it as a CSV file.

9. Show descriptive statistics and save per-compound statistics (one row per `cas`) as a CSV file.

## Prerequisites

1. Python 3 (https://www.python.org/downloads/) with the packages `pandas`, `numpy`, `chardet`, and `requests`.
2. The notebook is run in JupyterLab (https://jupyter.org/), or any other Jupyter-compatible environment.
3. The shared `inquire_common` folder (utilities, PubChem client, and filter lists), located in the parent folder of the notebook.
4. The SPECIEUROPE CSV file `Source 999 - all sources.csv` (see `../original_databases/README.md` for how it was downloaded from https://source-apportionment.jrc.ec.europa.eu/Specieurope/). By default it is expected in `../original_databases` (relative to the notebook); change `CSV_PATH` in the configuration cell if needed.
5. Internet access for the PubChem step (https://pubchem.ncbi.nlm.nih.gov/).

## How to use the notebook

1. Edit the settings in the configuration cell if needed:

- `CSV_PATH`: the raw SPECIEUROPE CSV file.
- `OUTPUT_DIR` / `CACHE_DIR`: output (`specieurope_cleaned`) and cache (`cache`) folders, created next to the notebook.
- `LOOKUP_LIMIT`: set to e.g. 50 for a quick test run of the PubChem lookups; `None` runs all compounds.
- `MAX_REQ_PER_SEC` and `N_WORKERS`: PubChem request rate (<= 5 requests/second is requested by PubChem) and number of parallel workers.

2. Run the notebook cell by cell (or all cells). The first PubChem run takes a while; later runs reuse the cache.

## Output files

All files are written to `specieurope_cleaned/`:

| File | Description |
| --- | --- |
| `SPECIEUROPE_Profiles_All_01_Fltrd.csv` | Cleaned table before InChIKey/keyword filtering |
| `SPECIEUROPE_Profiles_All_02_Fltrd.csv` | Final filtered table |
| `SPECIEUROPE_Profiles_All_03_CAS_Profile_Composition.csv` | Per-compound statistics |

## License

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
