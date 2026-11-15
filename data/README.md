# Working folder (`data_dir`)

This folder holds all input files and, after running the notebooks, all outputs. Its content is **not** part of the repository (see `.gitignore`), with one exception: the `priors/` subfolder (source weights and priors, see below) is tracked in git. The location and the subfolder names are set in `config.yaml` in the repository root (`data_dir`, `folders`); the defaults are used below.

## Inputs to place here

**Part 1 input – `preprocessing_in/`** (create it yourself; Part 1 stops with an error if it is missing). The source database files must be in the subfolder `preprocessing_in/source_databases/` (fixed name, not configurable):

| Path | Content | Where to get it |
|---|---|---|
| `preprocessing_in/Sample_Data.xlsx` | Non-target screening results, one column per sample | Your own data, or the synthetic test data in `../example_data/preprocessing_in/` |
| `analysis_in/geo_metadata_outputs/household_metadata_priors.csv` | Optional household priors (see `docs/household_priors.md`) | Your own data, or the synthetic test data `../example_data/analysis_in/geo_metadata_outputs/household_metadata_priors.csv`; not needed if `USE_GEO_PRIORS = False` in Part 2 |
| `preprocessing_in/lookups/source_class_mapping.xlsx` | Mapping of source categories to the reporting classes `source_class` / `source_class_domain` | Your own data, or the synthetic test data `../example_data/preprocessing_in/lookups/source_class_mapping.xlsx` |
| `preprocessing_in/source_databases/Own_Household_Products.csv`, `Own_Household_Products_Metadata.csv` | Own analyzed household products | Your own data, or the synthetic test data `../example_data/preprocessing_in/source_databases/Own_Household_Products.csv`, `../example_data/preprocessing_in/source_databases/Own_Household_Products_Metadata.csv` |
| `preprocessing_in/source_databases/Literature_Products.csv` | Consumer-product compounds compiled from the literature | Your own data, or the synthetic test data `../example_data/preprocessing_in/source_databases/Literature_Products.csv` |
| `preprocessing_in/source_databases/CPDat/product_compositions.tsv`, `CPDat/products.tsv`, `CPDat/product_use_categories.tsv` | US EPA CPDat v4.0 (processed) | Rebuild from the original (https://www.epa.gov/chemical-research/chemical-and-products-database-cpdat) with https://github.com/r3bryk/cpdat_v4.0_cleanup, or the synthetic test data in `../example_data/preprocessing_in/source_databases/CPDat` |
| `preprocessing_in/source_databases/FooDB.csv` | FooDB v1.0 (processed; tab-separated) | Rebuild from the original (https://foodb.ca) with https://github.com/r3bryk/foodb_v1.0_cleanup, or the synthetic test data `../example_data/preprocessing_in/source_databases/FooDB.csv` |
| `preprocessing_in/source_databases/SPECIATE.xlsx` | US EPA SPECIATE v5.4 (processed) | Rebuild from the original (https://www.epa.gov/air-emissions-modeling/speciate) with https://github.com/r3bryk/speciate_v5.4_cleanup, or the synthetic test data `../example_data/preprocessing_in/source_databases/SPECIATE.xlsx` |
| `preprocessing_in/source_databases/SPECIEUROPE.xlsx` | JRC SPECIEUROPE v3.0 (processed) | Rebuild from the original (https://source-apportionment.jrc.ec.europa.eu/Specieurope/index.aspx) with https://github.com/r3bryk/specieurope_v3.0_cleanup, or the synthetic test data `../example_data/preprocessing_in/source_databases/SPECIEUROPE.xlsx` |

**Part 2 input – `priors/`** (included in the repository; read by Part 2, no action needed for indoor dust). CSV files with the source-origin weights, the prior of every source kind and source category, and the weights of the household-information modules. The folder name is set by `folders.priors` in `config.yaml`. Details and how to adapt them to another matrix: [Source weights and priors](#source-weights-and-priors-priors).

**Testing without the real databases:** `../example_data/` contains small synthetic versions of **all** inputs in this table (same file names and subfolders; 60 sources per database). Copy its two folders `preprocessing_in/` and `analysis_in/` into this folder to test the pipeline; see [example_data/README.md](../example_data/README.md).

**License of the shared data:** CC BY-NC 4.0 (non-commercial; required because the source database contains FooDB-derived data). Please also cite the original databases (see the main README).

Formats and mandatory columns: [docs/input_data.md](../docs/input_data.md).

## Source weights and priors (`priors/`)

Part 2 reads these values from plain CSV files, so they can be reviewed, versioned and changed without editing the notebook. The shipped values were designed for **indoor dust**.

| File | Columns | Content |
|---|---|---|
| `source_weights.csv` | `source_origin`, `weight`, `rationale` | Weight per source database (origin); also defines the tier order of the set cover (equal weights share a tier) |
| `prior_tables.csv` | `source_origin`, `kind_table`, `category_table`, `default_kind_prior` | Which kind/category table each origin uses (origins may share tables) and the default kind prior |
| `kind_priors.csv` | `table`, `source_kind`, `prior`, `group`, `rationale` | Prior per source kind |
| `category_priors.csv` | `table`, `source_general_category`, `prior`, `group`, `rationale` | Prior per general source category (SPECIATE/SPECIEUROPE categories are hierarchical: "A; B; C" falls back to "A; B", then "A") |
| `module_weights.csv` | `module`, `weight`, `group`, `rationale` | Influence of each household-information module (`*_likelihood` column of the household priors file); 0 = not used |

Scale for all priors: 1.0 = well-documented direct contributor to the matrix, about 0.5 = plausible or indirect, 0.1 or lower = mainly industrial/occupational or remote. The final prior of a source is `weight(origin) * sqrt(kind_prior * category_prior)`. Evidence and references: [priors/README.md](priors/README.md).

**Adapting the priors to another matrix (e.g. indoor air):**

1. Copy `priors/` to a new folder (e.g. `priors_air/`) and set `folders.priors` in `config.yaml` to its name. This keeps the dust values intact and makes runs reproducible.
2. Re-evaluate `source_weights.csv` (how well does each database represent sources of this matrix?) and the `kind_priors.csv`/`category_priors.csv` values, using literature for the new matrix. Record the reason and reference in the `rationale` column.
3. Make sure every `source_kind` and `source_general_category` of your source database has a row. Missing entries are not an error: they fall back to the origin's `default_kind_prior` (kind) or to the kind prior (category). The list of categories per origin is written by the optional export cell in Part 2 (`analysis_out/lookups/source_categories_per_origin.csv`).
4. Review `module_weights.csv`; set the weight to 0 for modules that are not directional for the new matrix (e.g. `ventilation_likelihood`). The module list must match the `*_likelihood` columns of your household priors file, and the links between modules and source categories (`MODULE_SOURCE_MAP`) in Part 2 may also need adapting.
5. Re-tune `alpha` (penalty weight) in Part 2, because it was tuned for the dust priors (see [docs/method_and_limitations.md](../docs/method_and_limitations.md)).

File rules: comma-separated, UTF-8, header row required, keys unique per file/table, values between 0 and 1. Part 2 stops with an error on missing columns, duplicate keys, out-of-range values or unknown tables. Edit with a tool that does not reinterpret text (the category `NoID` must stay text) and do not rename the columns.

## Outputs created here

| Folder | Created by | Content |
|---|---|---|
| `preprocessing_out/` | Part 1 | `databases_id_w_suffix/`, `databases_standardized/`, `all_sources_aggregated/`, `masked_sources/`, `lookups/` (unmapped source categories) |
| `analysis_out/` | Part 2 (input of Part 3) | `lookups/`, `geo_check/`, `alpha_tuning/`, `validation_outputs/`, `set_cover_outputs/` |
| `visualization_out/` | Part 3 | Figures (html/png) |

See [docs/codebook.md](../docs/codebook.md). A full run needs about 6 GB of free disk space.
