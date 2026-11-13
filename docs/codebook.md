# Codebook: output files and variables

This codebook lists every file the pipeline writes and explains its columns. All files are written to subfolders of the working folder `data/` (`data_dir` in `config.yaml`); folders are created automatically. The three output folders are named `preprocessing_out` (Part 1), `analysis_out` (Part 2) and `visualization_out` (Part 3); paths in the file map and section headings are relative to `data/`. Input files are described in [input_data.md](input_data.md).

**Bold** file names are read by a later part; all others are for traceability, quality control, and reporting. Part 2 reads the four bold Part 1 tables from the **SQLite database** `preprocessing_out/inquire_csi_pt1.sqlite` (section 2.8), which holds the same content as the CSV files; the CSV files are still written and can be used for inspection.

**Terms used below**
- **Sample universe** – the InChIKeys detected in a sample.
- **Attributable compound** – a sample compound that occurs in at least one source of the database. **Unattributed compound** – a sample compound without any source.
- **Candidate source** – a source that contains at least one compound of the sample.
- **Cover** – a set of sources that together contain every attributable compound of a sample. `cover_id = 1` is the best (cheapest) cover.
- **Cost** – what the optimizer minimizes. Cost of one source = `P_i + alpha × penalty_i` (prior/coverage term plus frequency penalty, see [method_and_limitations.md](method_and_limitations.md)); cost of a cover = sum over its sources. Costs are unitless; only differences between covers of the same sample are meaningful.
- **Temperature T** – `POSTERIOR_TEMPERATURE`, the scale used to turn cost differences into probabilities (Part 2, cell *Convert costs to probabilities*).

---

## 1. File map

| Folder | File | Written by | Read by | Section |
|---|---|---|---|---|
| `preprocessing_out/` | **`inquire_csi_pt1.sqlite`** (database with all Part 1 results except the raw per-database copies) | Part 1 | Part 2 | 2.8 |
| `preprocessing_out/inspection/` | CSV copy of every database view and sample table, `inquire_csi_pt1.xlsx` | Part 1 | – (inspection) | 2.8 |
| `preprocessing_out/databases_id_w_suffix/` | `cpdat_products_suffix.csv`, `cpdat_products_meta_suffix.csv`, `cpdat_puc_suffix.csv`, `household_metadata_suffix.csv`, `household_products_no-suffix.csv`, `consumer_products_suffix.csv`, `foodb_suffix.csv`, `specieurope_suffix.csv`, `speciate_suffix.csv` | Part 1 | – | 2.1 |
| `preprocessing_out/databases_standardized/` | `all_sources_standardized.csv` | Part 1 | – | 2.2 |
| | **`sources_meta_standardized.csv`** | Part 1 | Part 2 (via database) | 2.2 |
| | `household_products_standardized.csv`, `lit_consumer_products_standardized.csv`, `foodb_standardized.csv`, `specieurope_standardized.csv`, `speciate_standardized.csv`, `cpdat_*_standardized.csv` | Part 1 | – | 2.3 |
| | `all_compounds_standardized.csv` | Part 1 | – (reference) | 2.3 |
| | `equivalence_groups_members.csv`, `equivalence_groups_summary.csv` | Part 1 | – | 2.4 |
| | **`dust_standardized.csv`** (or `dust_standardized_qc_cols.csv`) | Part 1 | Part 2 (via database) | 2.5 |
| `preprocessing_out/all_sources_aggregated/` | `all_sources_aggregated.csv` | Part 1 | – | 2.2 |
| `preprocessing_out/masked_sources/` | **`sources_masked.csv`** | Part 1 | Part 2 (via database) | 2.2 |
| | `masked_equivalence_groups_members.csv` | Part 1 | – | 2.4 |
| | `counts_masked.csv`, `valid_sources_masked.csv` | Part 1 | – | 2.6 |
| | **`sample_universes.csv`** | Part 1 | Part 2 (via database) | 2.5 |
| `preprocessing_in/lookups/` | `source_class_mapping.xlsx` | user (input) | Part 1 | [input_data.md](input_data.md#3-source-class-mapping-part-1) |
| `preprocessing_out/lookups/` | `source_class_unmapped.csv`, `source_class_unmapped_std_dbs.csv` | Part 1 | – | 2.7 |
| `analysis_out/lookups/` | `source_categories_per_origin.csv`, `source_metadata_lookup.csv`, `source_metadata_lookup_dict.csv`, `source_prior_lookup.csv`, `source_compound_sets.csv`, `hh_metadata_lookup.csv`, `compound_to_sources_lookup.csv` | Part 2 | – | 3.6 |
| `analysis_in/geo_metadata_outputs/` | `household_metadata_priors.csv` | user (optional input) | Part 2 | [household_priors.md](household_priors.md) |
| `analysis_out/geo_check/` | `geo_mapping_check.csv` | Part 2 | – | 3.7 |
| `analysis_out/alpha_tuning/` | `alpha_greedy.csv`, `alpha_beam.csv`, `alphas_greedy_vs_beam.png`, `alphas_greedy_vs_beam_non-log.png`, `prior_strength_calibration.csv` | Part 2 | – | 3.8 |
| `analysis_out/validation_outputs/` | `master_validation_summary.csv`, `synthetic_validation_precision.png`, `synthetic_validation_boxplot.png`, `loso_jaccard_plot.png` | Part 2 | – | 3.9 |
| | `posterior_summary.csv`, `robustness_summary.csv` | Part 2 | – | 3.4, 3.5 |
| | `final_checks_per_sample.csv`, `own_household_products_check.csv` | Part 2 | – | 3.10, 3.11 |
| `analysis_out/set_cover_outputs/` | **`cover_results_all_samples_beam.csv`**, `<sample>_beam.csv` | Part 2 | Part 3 | 3.1 |
| | `unattributed_results_all_samples_beam.csv` | Part 2 | – | 3.2 |
| | `source_posterior_all_samples_beam.csv` | Part 2 | – | 3.3 |
| | `compound_attribution_per_origin.csv` | Part 2 | – | 3.12 |
| `visualization_out/` | `inquire_csi_figure.html`, `inquire_csi_figure_<LL>.html`, `inquire_csi_country-source_category_heatmap.png`, `…_heatmap_land.png`, `inquire_csi_country-source_sankey.html`, `inquire_csi_country-source_category_sankey.html` | Part 3 | – | 4 |
| `notebooks/` | `inquire_csi_pt1_preprocessing_log_<yymmdd>.log`, `inquire_csi_pt2_analysis_and_validation_log_<yymmdd>.log`, `inquire_csi_pt3_visualization_log_<yymmdd>.log` | Parts 1–3 | – | run logs |

---

## 2. Part 1 outputs

### 2.1 Databases with ID suffixes (`preprocessing_out/databases_id_w_suffix/`)
Copies of the input databases, unchanged except that the ID column carries a database suffix: `_CPD` (CPDat), `_HHP` (own household products; note: the file `household_products_no-suffix.csv` *does* contain the suffix despite its name), `_COP` (literature products), `_FDB` (FooDB), `_SUS` (SPECIATE), `_SEU` (SPECIEUROPE). Columns as in the input files ([input_data.md](input_data.md)).

### 2.2 Harmonized source tables
`all_sources_standardized.csv` (all sources), `all_sources_aggregated.csv` (after first aggregation), **`sources_masked.csv`** (after masking and second aggregation). One row per source × compound.

| Column | Meaning |
|---|---|
| `source_id` | Unique source ID with database suffix (e.g., `FR01_CP04_HHP`, `12345_CPD`) |
| `source_name` | Name of the product, food or emission profile |
| `inchikey` | InChIKey of one compound of the source |
| `source_origin` | Database: `HOUSEHOLD_PRODUCTS`, `LIT_CONSUMER_PRODUCTS`, `CPDAT`, `FOODB`, `SPECIATE`, `SPECIEUROPE` |
| `source_kind` | Higher classification level of the source within its database (CPDat PUC kind; FooDB food group; SPECIATE/SPECIEUROPE generation mechanism; consumer products `Group1`) – used for priors |
| `source_general_category` | Lower classification level (CPDat PUC general category; FooDB food subgroup; SPECIATE/SPECIEUROPE sector/equipment; consumer products `Group2`) – used for priors and household-prior links |
| `source_harmonized` | Full harmonized label (CPDat PUC style; SPECIATE/SPECIEUROPE "level 1 \| level 2 \| level 3") |
| `source_class` | Cross-database reporting class "Domain \| Type" from `source_class_mapping.xlsx`; "Unmapped Sources \| <origin>" if not in the mapping |
| `source_class_domain` | Reporting domain (first part of `source_class`) |

`sources_meta_standardized.csv` has the same columns without `inchikey`, with **one row per source** (if a `source_id` has more than one set of metadata in the input, the first row is kept and Part 1 logs a warning). Missing `source_kind`, `source_general_category` and `source_harmonized` are set to "Unknown".

### 2.3 Separate standardized databases (`preprocessing_out/databases_standardized/<database>_standardized.csv`)
Each database on its own after renaming to the harmonized schema, with all original columns kept (minus `ID`, `#` and, if `DROP_EMPTY_COLS_STD = True`, completely empty columns), plus `source_class` and `source_class_domain` where the key columns exist. Additional harmonized columns: `feature_name` (compound name in that database) and `source_type` (third classification level, e.g., `Group3`, `food_type`, SPECIATE level 3). The CPDat helper files are `cpdat_products_standardized.csv` (compositions), `cpdat_products_meta_standardized.csv` (product titles), `cpdat_puc_standardized.csv` (one PUC per product), `cpdat_products_simple_standardized.csv` (product × InChIKey), `cpdat_sources_standardized.csv` (CPDat in the harmonized schema) and `cpdat_titles_standardized.csv`.

**All-compounds lookup (`all_compounds_standardized.csv`).** One row per compound (InChIKey) found in any of the six source databases (all sources, before aggregation and masking). Several values in one cell are separated by "; " (`MULTI_SEP`). Reference table only; not used by Part 2.

| Column | Meaning |
|---|---|
| `inchikey` | InChIKey of the compound (cleaned as in all other Part 1 outputs: upper case, digit "0" → letter "O"; see [01_preprocessing.md](01_preprocessing.md), steps 6 and 11) |
| `feature_name` | Preferred compound name: most frequent name in the first database of `FEATURE_NAME_PRIORITY` (CPDat → SPECIATE → SPECIEUROPE → FooDB → literature products → own household products) that has a name |
| `all_feature_names` | All distinct names from all databases (main names first, then other names such as raw, PubChem or IUPAC names; duplicates ignoring upper/lower case removed) |
| `cas` | All distinct CAS numbers (format `NNNNNNN-NN-N`); empty if none |
| `dtxsid` | All distinct US EPA CompTox substance IDs (`DTXSID…`); empty if none |

### 2.4 Equivalence groups (merged sources)

`equivalence_groups_members.csv` (first aggregation; one row per original source):

| Column | Meaning |
|---|---|
| `source_origin`, `source_harmonized` | Database and harmonized label of the group |
| `eqsetID` | `source_id` of the representative that is kept |
| `sourceID` | `source_id` of a member (the representative is also listed as its own member) |

`equivalence_groups_summary.csv` (one row per group): `source_origin`, `source_kind`, `source_general_category`, `source_harmonized`, `eqsetID` (representative), `n_sources` (number of merged sources), `source_ids` and `source_names` (all members, separated by "; ").

`masked_equivalence_groups_members.csv` (second aggregation, after masking; one row per source):

| Column | Meaning |
|---|---|
| `masked_eqsetID` | `source_id` of the representative kept after masking |
| `source_id` | Member source |
| `source_origin`, `source_kind`, `source_general_category`, `source_harmonized` | Group key (identical within a group) |
| `hh_household` | For own household products: household code from the ID (e.g., `FR01`); products of different households are never merged. Empty for other origins |
| `masked_hash` | Fingerprint of the masked compound set (identical within a group) |

### 2.5 Sample tables
`dust_standardized.csv`: the sample table (`inchikey`, `Feature Name`, `Class`, `Concentration Type`, one column per sample) after removing rows without InChIKey and blank/QC columns. With `DROP_QC_COLUMNS = False` it is saved as `dust_standardized_qc_cols.csv` instead.

`sample_universes.csv`: one row per InChIKey detected in any sample (`inchikey`) and one column per sample; a cell contains the InChIKey if the compound was detected (value > 0) in that sample, otherwise `NA`.

### 2.6 Masking counts
`counts_masked.csv`: `source_id` and `n_compound_rows` (number of sample compounds per source after masking). `valid_sources_masked.csv`: `source_id` of every source retained in `sources_masked.csv`.

### 2.7 Unmapped categories
`source_class_unmapped.csv`: category keys (`source_origin`, `source_kind`, `source_general_category`, `source_harmonized`) that are missing from `source_class_mapping.xlsx`. `source_class_unmapped_std_dbs.csv`: the same for the separate standardized databases, with the column `standardized_db` naming the database. Only written if unmapped keys exist.

### 2.8 SQLite database and inspection copies
`preprocessing_out/inquire_csi_pt1.sqlite` is written at the end of Part 1 (last notebook cell) and rebuilt from scratch on every run. It stores the Part 1 results without repetition (normalized) and is the input of Part 2. It contains **only Part 1 results**; the raw per-database copies (`databases_id_w_suffix/`, `databases_standardized/<database>_standardized.csv`) stay as files and are not loaded. The full definition is in [schema.sql](schema.sql); helper functions are in `notebooks/csi_db.py`.

**Tables**

| Table | One row per | Content |
|---|---|---|
| `source_origin` | database | `source_origin` and its ID suffix (`id_suffix`, e.g. `_CPD`) |
| `source_class` | reporting class | `source_class` ("Domain \| Type") and `source_class_domain` |
| `source` | source (all sources, before aggregation) | `source_id`, `source_name`, `source_origin`, `source_kind`, `source_general_category`, `source_harmonized`, `source_class` |
| `compound` | InChIKey of any source database | `inchikey`, preferred `feature_name` |
| `compound_name`, `compound_cas`, `compound_dtxsid` | value | The multi-valued cells of `all_compounds_standardized.csv`, one row per value in original order (`position`) |
| `source_compound` | source × compound | `source_id`, `inchikey`, flags `in_aggregated` and `in_masked` (1 if the row is part of `all_sources_aggregated.csv` / `sources_masked.csv`; every row belongs to `all_sources_standardized.csv`) |
| `source_group` | source in an equivalence group | `stage` (`aggregated` or `masked`), `representative_id`, `member_id`; for `masked` also `masked_hash` and `hh_household` |
| `sample` | sample | `sample_id`, `position` (column order) |
| `detected_compound` | row of the sample table | `inchikey`, `feature_name`, `compound_class`, `concentration_type`, `position` (row order) |
| `sample_compound` | sample × compound with a value | `sample_id`, `inchikey`, `concentration` (long format; missing values have no row) |

**Views** reproduce the CSV files of Part 1 with the same columns and row order (each view `v_<name>` corresponds to `<name>.csv`); use them for queries, e.g. `SELECT * FROM v_sources_masked WHERE source_origin = 'CPDAT'`.

| View | Corresponds to |
|---|---|
| `v_all_sources_standardized`, `v_all_sources_aggregated`, `v_sources_masked` | `all_sources_standardized.csv`, `all_sources_aggregated.csv`, `sources_masked.csv` |
| `v_sources_meta_standardized` | `sources_meta_standardized.csv` |
| `v_all_compounds_standardized` | `all_compounds_standardized.csv` (multi-valued cells joined with "; ") |
| `v_equivalence_groups_members`, `v_equivalence_groups_summary`, `v_masked_equivalence_groups_members` | the three equivalence group files (2.4) |
| `v_counts_masked`, `v_valid_sources_masked` | `counts_masked.csv`, `valid_sources_masked.csv` (2.6) |
| `v_sample_detections` | new: long format of the sample universes (`sample_id`, `inchikey` with concentration > 0) |

The two wide sample tables (`dust_standardized.csv`, `sample_universes.csv`) cannot be a fixed view because the number of sample columns varies; `csi_db.read_dust_standardized()` and `csi_db.read_sample_universes()` build them from the long tables. With `DROP_QC_COLUMNS = False` the QC columns are samples in the database.

**Inspection copies (`preprocessing_out/inspection/`).** Every view and both wide sample tables as CSV (same names, columns and row order as the original files), and `inquire_csi_pt1.xlsx` with one sheet per table that has at most 100,000 rows (larger tables only as CSV). These are convenience copies for opening in Excel or a text editor; they are overwritten on every run and are not read by any notebook. Do not edit the database or the copies; change the inputs and re-run Part 1.

**Check.** Unless `VERIFY_AGAINST_CSV = False`, Part 1 compares every view with the original CSV file cell by cell and stops if a table differs (`csi_db.verify_against_csv()`).

---

## 3. Part 2 outputs

### 3.1 Main result table: `analysis_out/set_cover_outputs/cover_results_all_samples_beam.csv` (and `<sample>_beam.csv`)
One row per **sample × cover × source × compound**, for compounds present in the sample. A compound explained by two sources of the same cover appears twice; count unique `inchikey` values, not rows.

| Column | Level | Meaning |
|---|---|---|
| `sample` | sample | Sample ID (column name in `Sample_Data.xlsx`) |
| `cover_id` | cover | Rank of the cover within the sample by total cost; `1` = best (cheapest) cover |
| `source_id` | source | Source in this cover |
| `source_name`, `source_origin`, `source_kind`, `source_general_category`, `source_harmonized`, `source_class`, `source_class_domain` | source | Source metadata (section 2.2) |
| `cost` | cover | Total cost of the cover = Σ over its sources of (`P_i` + alpha × penalty_i). Lower = better. Only comparable between covers of the same sample |
| `P` | cover | Probability of the cover within the sample: exp(−(cost − lowest cost) / T), normalized so that the covers of a sample sum to 1. Ranks the covers relative to a typical cost gap; **not a calibrated uncertainty** |
| `marginal_P` | sample × source | Sum of `P` over all covers of the sample that contain this source = probability that the source is part of the explanation (0–1). Values of different sources do not sum to 1 |
| `posterior_P` | sample × source | Inclusion probability of the source computed in the posterior-model cell; same definition and same temperature as `marginal_P`, so the two are equal (up to rounding) |
| `source_prior` | sample × source | Household-aware prior of the source for this sample: SOURCE_WEIGHT × √(kind prior × category prior) × geo multiplier × household factor (own products only) |
| `source_coverage` | sample × source | Share of the sample's attributable compounds that the source contains (0–1) |
| `source_log10P` | sample × source | log10 of p(source), where p(source) ∝ prior^PRIOR_STRENGTH × coverage, normalized over **all** candidate sources of the sample (= −P_i / ln 10). Always ≤ 0 and usually strongly negative (e.g., −238.3 means p = 4.5 × 10⁻²³⁹); stored as a logarithm because p itself is too small and would be 0 |
| `source_log10P_rel` | sample × cover × source | `source_log10P` minus the highest `source_log10P` among the sources of the same cover: 0 = the source of the cover favored most by the prior/coverage model; −1 = 10 times less likely; −10 = 10¹⁰ times less likely |
| `solution_frequency` | sample × source | Share of the sample's covers that contain the source (unweighted) |
| `total_covers` | sample | Number of distinct covers retained for the sample (greedy + beam search, duplicates removed) |
| `ci_low`, `ci_high` | sample × source | 95% interval of `solution_frequency` from a Beta(n + 1, N − n + 1) distribution (n = covers containing the source, N = `total_covers`). Describes how consistently the source appears among the alternative covers, not measurement uncertainty |
| `count` | sample × source | Number of covers of the sample that contain the source (= n) |
| `inchikey` | compound | Compound of the sample explained by this source |
| `feature_name` | compound | Compound name (from `Feature Name` in the sample data) |
| `n_unique_chemicals` | cover | Number of sample compounds covered by the cover (= attributable compounds of the sample) |
| `n_unique_sources` | cover | Number of sources in the cover |
| `n_unique_source_harmonized` | cover | Number of distinct `source_harmonized` labels in the cover |
| `n_source_classes` | cover | Number of distinct `source_class` values in the cover |
| `n_source_class_domains` | cover | Number of distinct `source_class_domain` values in the cover |

**Typical use:** filter `cover_id == 1` for the best explanation; count unique `inchikey` per `source_class_domain` (or another category) for category shares.

### 3.2 `analysis_out/set_cover_outputs/unattributed_results_all_samples_beam.csv`
Compounds of each sample that do not appear in any cover of that sample, mainly compounds without any source in the masked database, plus all compounds of samples that were skipped.

| Column | Meaning |
|---|---|
| `sample` | Sample ID |
| `inchikey` | Unattributed compound |
| `feature_name` | Compound name |

### 3.3 `analysis_out/set_cover_outputs/source_posterior_all_samples_beam.csv`
One row per sample × source that appears in at least one cover.

| Column | Meaning |
|---|---|
| `sample`, `source_id` | Sample and source |
| `posterior_P` | Inclusion probability (sum of cover probabilities `P` of the covers containing the source; capped at 1) |
| `cover_support` | Number of covers of the sample containing the source |
| `posterior_share` | `posterior_P` divided by the sum of `posterior_P` over all sources of the sample (sums to 1 per sample); the source's share of the explanation |

### 3.4 `analysis_out/validation_outputs/posterior_summary.csv`
One row per sample; computed from the source shares (`posterior_P` normalized over the sources of the sample).

| Column | Meaning |
|---|---|
| `posterior_entropy` | Shannon entropy of the source shares; higher = explanation spread over more sources |
| `posterior_ess` | Effective number of sources = 1 / Σ share² |
| `top1_posterior`, `top5_posterior_mass` | Share of the largest source; summed share of the five largest |
| `posterior_concentration` | `top1_posterior` / `top5_posterior_mass` |
| `posterior_gini` | Gini coefficient of the source shares (0 = all equal, → 1 = dominated by few sources) |
| `n_covers` | Number of covers of the sample |
| `mean_solution_frequency`, `median_solution_frequency`, `sd_solution_frequency` | Summary of `solution_frequency` over the sources of the sample |

### 3.5 `analysis_out/validation_outputs/robustness_summary.csv`
One row per sample × source: `solution_frequency`, `weighted_frequency` (sum of `P` of the covers containing the source / sum of `P` of all covers), `covers_present` (n), `total_covers` (N), `ci_low`, `ci_high`, `ci_width` (definitions as in 3.1).

### 3.6 Lookups (`analysis_out/lookups/`)

| File | Columns | Meaning |
|---|---|---|
| `source_categories_per_origin.csv` | `source_origin`, `source_kind`, `source_general_category`, `n_sources`, `example_source_names` | Every category combination in the database, number of sources and up to three example names; basis for the prior tables |
| `source_metadata_lookup.csv` | `source_id` + metadata columns (section 2.2) | One row per source |
| `source_metadata_lookup_dict.csv` | `source_id`, `origins` | Origin, kind and category per source (as a dictionary text) |
| `source_prior_lookup.csv` | `source_id`, `source_weight` | Household-independent prior of each source: SOURCE_WEIGHT × √(kind prior × category prior) |
| `source_compound_sets.csv` | `source_id`, `inchikey` | Set of InChIKeys per masked source (as text) |
| `hh_metadata_lookup.csv` | `household_id`, `likelihoods` | Household likelihoods as used (dictionary text); empty if `USE_GEO_PRIORS = False` |
| `compound_to_sources_lookup.csv` | `inchikey`, `sources` | All masked sources containing each compound |

### 3.7 `analysis_out/geo_check/geo_mapping_check.csv`
One row per label in `MODULE_SOURCE_MAP`: `module`, `source_origin`, `label`, `status` (`OK`, `NOT FOUND` = label matches no source, `ORIGIN NOT IN DB`), `n_sources_matched`.

### 3.8 Tuning (`analysis_out/alpha_tuning/`)
- `alpha_greedy.csv`, `alpha_beam.csv`: `alpha` (penalty weight tested) and `score` (mean over synthetic mixtures of compound precision − 0.25 × (expansion − 1); higher = better).
- `alphas_greedy_vs_beam.png`, `alphas_greedy_vs_beam_non-log.png`: tuning curves (log and linear alpha axis).
- `prior_strength_calibration.csv`: per sample, `neg_log_prior_range` (5th–95th percentile spread of −log(prior) over the candidate sources) and `penalty_range` (same for alpha × penalty). `PRIOR_STRENGTH` = `PRIOR_TO_PENALTY_RATIO` × median(`penalty_range`) / median(`neg_log_prior_range`).

### 3.9 `analysis_out/validation_outputs/master_validation_summary.csv` and figures

| Column | Meaning |
|---|---|
| `Category` | Validation block (synthetic perturbation robustness, synthetic recovery, source ambiguity, cost model, beam search, database redundancy, algorithm robustness) |
| `Metric` | Metric name |
| `Value` | Mean value over replicates (or sources) |
| `Interpretation` | Excellent / Good / Moderate / Weak, from the thresholds in `METRIC_INFO` |
| `Interpretation Explanation` | Short text for that category |
| `Metric Description` | What the metric measures |

Metric definitions: compound precision, recall, F1, Jaccard, source precision/recall/F1 and false discovery rate as in [02_analysis_and_validation.md, section E](02_analysis_and_validation.md#e-validation); **cost ratio** = cost of the recovered cover / cost of the true sources (1 = equally plausible, < 1 = optimizer found a cheaper explanation); **posterior entropy, effective sample size, top-1, top-5** = concentration of the cover probabilities in the beam-search block (computed with temperature 1); **maximum Jaccard** (`best_jaccard`) = mean similarity of each source to its closest other source; **recoverable fraction** = share of a removed source's compounds that other sources still contain.

Figures: `synthetic_validation_precision.png` (mean compound precision with 95% CI and mean number of recovered sources vs. mixture size), `synthetic_validation_boxplot.png` (distribution of compound precision vs. mixture size), `loso_jaccard_plot.png` (histogram of best Jaccard per source).

### 3.10 `analysis_out/validation_outputs/final_checks_per_sample.csv`

| Column | Meaning |
|---|---|
| `sample`, `household` | Sample and its sample key `LLNN` (sample ID without suffix; used to match household priors and own products) |
| `household_has_analyzed_products` | `True` if own products with the same key (`LLNN_CPnn`) are in the database |
| `n_own_hh_candidates` | Own products with the same key among the candidate sources |
| `n_own_hh_in_best_cover` | …of which in the best cover |
| `n_any_hh_in_best_cover` | Own products of any key in the best cover |
| `n_sources_in_best_cover` | Sources in the best cover |
| `best_cover_is_greedy` | `True` if the best cover equals the greedy cover |
| `n_covers` | Covers retained for the sample |
| `n_compounds_attributable`, `n_compounds_unattributed` | Sample compounds with / without a source in the database |
| `share_unattributed` | Unattributed / (attributable + unattributed) |

### 3.11 `analysis_out/validation_outputs/own_household_products_check.csv`
One row per sample whose own household products are candidates.

| Column | Meaning |
|---|---|
| `n_own_candidates`, `n_own_in_best_cover` | Own products among candidates / in the best cover |
| `n_sample_compounds_in_own_products` | Sample compounds that occur in at least one own product |
| `share_explained_by_own_products` | Share of these compounds explained by own products in the best cover |
| `main_origin_explaining_the_rest`, `n_rest_explained_by_main_origin` | Database explaining most of the remaining compounds, and how many |
| `hh_factor_own_products`, `hh_factor_other_hh_products` | Mean household factor applied to own products (should equal `HH_SAME_HOUSEHOLD`) and to products with another key (0.2–0.5) |

### 3.12 `analysis_out/set_cover_outputs/compound_attribution_per_origin.csv`
Best cover only. Each attributed compound is assigned once, to the highest-priority database (by `SOURCE_WEIGHT`) among the sources of the best cover that contain it.

| Column | Meaning |
|---|---|
| `sample`, `source_origin` | Sample and database |
| `n_compounds` | Compounds assigned to this database |
| `share_of_attributed_compounds` | `n_compounds` / attributable compounds of the sample (shares of a sample sum to 1) |

---

## 4. Part 3 outputs (`visualization_out/`)

| File | Content |
|---|---|
| `inquire_csi_figure.html` | Interactive 3D network (best cover, all samples): samples (diamonds, colored by sample group = first two letters of the sample ID, e.g., country) – compounds (gray circles) – sources (squares, colored by source category). Hover: sample/compound/source details and numbers of links |
| `inquire_csi_figure_<LL>.html` | The same for one sample group (`LL` = 2-letter sample code) |
| `inquire_csi_country-source_category_heatmap.png`, `…_heatmap_land.png` | Sample groups × source categories; cell = number of unique compounds explained by sources of the category and percentage of the group's unique attributed compounds (non-exclusive) |
| `inquire_csi_country-source_sankey.html` | Sankey diagram sample group → source category (simple version) |
| `inquire_csi_country-source_category_sankey.html` | Final Sankey diagram with leader lines; link width = unique compounds per sample group × category; categories < 1% in every group merged into "Other" |
