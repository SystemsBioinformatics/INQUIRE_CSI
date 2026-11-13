# Part 2 – INQUIRE_CSI_Pt2_Analysis_and_Validation (Contaminant Source Analysis and Validation)

## Purpose

Part 2 is the core of the pipeline. For every sample it finds a small and plausible set of sources from the master contaminant source database that together explain all **attributable** compounds of that sample (compounds for which at least one source exists). This is a **weighted set-cover problem**: every source "covers" the compounds it contains, and every source has a cost; the aim is to cover all compounds at the lowest total cost. Plausible sources (high prior) and sources that bring few compounds absent from the sample are cheap.

Part 2 also tunes the model, calibrates the balance between prior knowledge and chemical fit, and runs a series of validations that show how well the method recovers known sources.

The model is explained in [method_and_limitations.md](method_and_limitations.md); this page describes how the notebook does it. All output columns are explained in the [codebook](codebook.md).

## Inputs

Part 1 files are read from `data/preprocessing_out/`, the optional priors from `data/analysis_in/` (folder names set in `config.yaml`).

| File | From | Content |
|---|---|---|
| `preprocessing_out/databases_standardized/sources_meta_standardized.csv` | Part 1 | Names, categories and reporting classes of all sources |
| `preprocessing_out/databases_standardized/dust_standardized.csv` | Part 1 | Sample table (used for compound names) |
| `preprocessing_out/masked_sources/sources_masked.csv` | Part 1 | Final source database (source × compound) |
| `preprocessing_out/masked_sources/sample_universes.csv` | Part 1 | InChIKeys detected per sample |
| `analysis_in/geo_metadata_outputs/household_metadata_priors.csv` | optional, user-provided ([household_priors.md](household_priors.md)) | Household likelihoods per module; only read if `USE_GEO_PRIORS = True` |

Mandatory columns are checked at the start: `source_id, source_name, source_origin, source_kind, source_general_category, source_harmonized, source_class, source_class_domain, inchikey`, `Feature Name`, and `household_id` if `USE_GEO_PRIORS = True`.

## Outputs

All outputs are written to `data/analysis_out/`. Main results (folder `analysis_out/set_cover_outputs/`):

| File | Content |
|---|---|
| `cover_results_all_samples_beam.csv` | **Main result table** (input of Part 3): one row per sample × cover × source × compound (only compounds present in that sample) |
| `<sample>_beam.csv` | The same table for each sample separately |
| `unattributed_results_all_samples_beam.csv` | Compounds of each sample that are not explained by any cover (mostly compounds without any source in the database) |
| `source_posterior_all_samples_beam.csv` | Per sample × source: inclusion probability and share of the explanation |
| `compound_attribution_per_origin.csv` | Per sample: share of attributed compounds per source database (origin) in the best cover |

Validation and diagnostics (in `analysis_out/`): `alpha_tuning/`, `validation_outputs/`, `lookups/`, `geo_check/geo_mapping_check.csv`. See the [codebook](codebook.md) for every file and column.

## Runtime

About 5 hours for ~200 samples on the test laptop (INQUIRE reference run: 05:02:00). Alpha tuning and the validation blocks take more than half of this time; see "Running without validation" below.

---

## Notebook sections in run order

### A. Set-up and inputs

**A1. Title; reset environment; imports & setup.** As in Part 1; log file `inquire_csi_pt2_analysis_and_validation_log_<yymmdd>.log`; `GLOBAL_SEED = 1`.

**A2. Check columns.** Reads `config.yaml` and sets `DATA_DIR`, `PREP_OUT_DIR`, `AN_IN_DIR` and `AN_OUT_DIR` (stops if the working folder or `preprocessing_out` does not exist), the switch `USE_GEO_PRIORS` and the subfolders (`STD_DIR`, `MASK_DIR`, `GEO_DIR`, `GEO_CHECK_DIR`, `ALF_DIR`, `VAL_DIR`, `OUT_DIR`), and checks the mandatory columns.

**A3. Load inputs; load household metadata priors.** Loads the four Part 1 files. If `USE_GEO_PRIORS = True`, loads `household_metadata_priors.csv` and builds a lookup per household; otherwise the lookup stays empty and no household information is used. Sample IDs follow the pattern `LLNN[_suffix]` (`LL` = 2-letter sample code, `NN` = 2-digit sample number, `[_suffix]` is not mandatory, e.g., `FR01`, `FR01_LS2`); the function `household_key()` reduces every sample ID and `household_id` to the key `LLNN` (e.g., `FR01_LS2` → `FR01`) so that they match. IDs in another format are used unchanged (upper case). Warns if IDs in the priors file are not in the `LLNN` format or appear twice.

**A4. Lookups and inverted index.** Builds fast lookups: compound set per source (masked sources only), names and categories per source, compound names from the sample table, and the inverted index "compound → all sources containing it" (used by beam search). The optional cell *Export all source categories per origin* writes `lookups/source_categories_per_origin.csv`: every combination of origin × kind × general category with the number of sources and three example names (the basis for designing the prior tables).

### B. Priors – how plausible is each source?

**B1. Source weights and category priors.** Defines the household-independent prior of every source:

`prior = SOURCE_WEIGHT[origin] × sqrt(kind_prior × category_prior)`

- `SOURCE_WEIGHT` reflects the reliability of each database for indoor dust: own analyzed household products 1.0, literature (measured) consumer products 0.8, FooDB 0.7, SPECIEUROPE 0.6, SPECIATE 0.4, CPDat (declared ingredients, not measured) 0.2.
- `kind_prior` and `category_prior` come from tables per origin (`CONS_PRODS_*`, `PUC_*`, `FOODB_*`, `SPECIATE_*`). Scale: 1.0 = well-documented direct contributor to residential dust; ~0.5 = plausible/indirect; ≤ 0.1 = mainly industrial or remote from homes. The values are based on the literature cited in the cell. If a category is not listed, its kind prior is used; if the kind is not listed, a default per origin. SPECIATE-style hierarchical categories ("A; B; C") fall back to the longest listed prefix. **These tables were designed for indoor dust; review them for other matrices.**

**B2. Geo metadata module weights (`MODULE_WEIGHT`).** One weight (0–1) per household-prior module ([household_priors.md](household_priors.md)) that says how strongly that household information may change the prior. Weight 0 switches a module off (`vaping`, `ventilation`, `pfas`: no matching source category or no clear direction).

**B3. Map geo modules to sources (`MODULE_SOURCE_MAP`).** Links each module to source categories per origin (e.g., `wood_burning` → SPECIATE/SPECIEUROPE "Biomass Burning; Residential Wood Combustion*"; `traffic` → SPECIATE "Mobile; Onroad*", CPDat "Vehicles", literature "SBR & NR" (tire rubber)). Matching rules: a label matches a source if it equals its general category **or** its kind; a label ending with `*` also matches all sub-categories; labels are matched within one origin only. Most categories are linked to one module, at most two. The cell checks that module names agree between `MODULE_WEIGHT`, `MODULE_SOURCE_MAP` and the priors file.

**B4. Check the geo mapping.** Reports for every label whether it matches any source (all should be "OK"), the share of sources per origin that household priors can influence, and which samples have **no** household metadata (they are analyzed without household priors). Saves `geo_metadata_outputs/geo_mapping_check.csv`.

**B5. Geo multiplier (helper functions).** For a source linked to modules *m* and the household of the sample:

`geo multiplier = exp( Σ_m MODULE_WEIGHT[m] × (likelihood_m − 0.5) )`

A household at the average (0.5) gives multiplier 1; with weight 1.0 and the extreme likelihoods 0.98/0.02, one module changes the prior by a factor of up to ~1.6 or ~0.6.

**B6. Household-independent priors; source prior helper; save lookups.** Pre-computes the prior of all sources. The household-aware prior for a sample is `prior × geo multiplier`, and for own household products additionally `× household factor`: `HH_SAME_HOUSEHOLD = 2.0` (product with the same key `LLNN` as the sample), `HH_SAME_COUNTRY = 0.5` (same 2-letter code `LL`; in the INQUIRE data, the same country), `HH_OTHER_COUNTRY = 0.2` (other `LL`; equal to the CPDat weight). The key is read from the product ID `LLNN_CPnn_HHP` (`FR01_CP04_HHP` → `FR01`); the cell reports how many product IDs could be read. Lookups are saved in `lookups/`.

### C. The optimization model

**C1. Build problem.** For a set of compounds (one sample), selects all sources that contain at least one of them and keeps, per source, only the compounds within the sample.

**C2. Cost function.** Computes for every candidate source *i* the prior/coverage cost

`P_i = − PRIOR_STRENGTH × log(prior_i) − log(coverage share_i) + constant`

where the coverage share is the number of sample compounds the source explains divided by the sum over all candidates. This is computed in log space (numerically stable even for very small priors). `PRIOR_STRENGTH` starts at 2.0 and is set by the calibration in D4.

**C3. Greedy cover.** Repeatedly adds the source with the lowest cost per newly covered compound until every compound of the sample is covered. Fast and gives one cover. The cost of a source used here is `P_i + alpha × penalty_i` (penalty: see C6).

**C4. Beam search.** Explores several partial covers in parallel: at each step every partial cover is extended by its best `max_children` (5) candidate sources (best = most new compounds per unit cost, deterministic order), and only the `beam_width` most promising partial covers are kept (priority = cost + 6 × uncovered compounds + 0.05 × number of sources). Complete covers are collected (up to `max_covers`). This gives alternative explanations close to the best one.

**C5. Tiered cover (optional, off).** With `USE_TIERED_COVER = True`, databases are used in order of `SOURCE_WEIGHT` (own products first, CPDat last): the first tier covers all it can, the next tier covers what is left, and so on. Not used for the reference run; available for comparison.

**C6. Frequency-weighted penalty.** Every compound gets a penalty `1/√(number of sources containing it)`: rare compounds are expensive, common compounds cheap. For a source, the penalty is the summed penalty of its compounds that are **not** in the sample, divided by its number of compounds, scaled to 0–1. The full source cost used by the optimizers is `P_i + alpha × penalty_i`, so sources that bring many (rare) compounds absent from the sample are penalized.

### D. Tuning and calibration

**D1. Alpha tuning (greedy and beam search).** `alpha` sets how strongly compounds absent from the sample are penalized. For 10 values between 10³ and 10⁵, 50 synthetic mixtures of 50 random sources are built (seed `GLOBAL_SEED`), solved, and scored with *compound precision − 0.25 × (expansion − 1)* (rewards correct compounds, punishes explaining many extra compounds). Results go to `alpha_tuning/alpha_greedy.csv` and `alpha_beam.csv`.

**D2. Load best alphas; plots.** Re-loads the tuning results and sets `best_alpha` and `best_alpha_beam` to the alpha with the **highest score**. Two plots (log and linear axis) show the tuning curves.

**D3. Optionally set alpha by hand.** The score curve usually forms a plateau, and its maximum can lie anywhere on it. In the cell *OPTIONAL: Specify best alphas manually based on the plots* you can set `best_alpha = best_alpha_beam = <value>`, e.g., the **lowest alpha on the plateau** (reference run: 4500). Leave the lines silenced to use the automatic maximum. Set the value **here**: calibration and validation use it. A second optional cell before the per-sample analysis repeats this; if you set a value there, set the same value here.

**D4. Validation seed and prior-strength calibration.** Validation uses `VALIDATION_SEED = GLOBAL_SEED + 1000`. Then `PRIOR_STRENGTH` is calibrated on all real samples so that the spread (5th–95th percentile across candidate sources, median over samples) of the prior term equals `PRIOR_TO_PENALTY_RATIO` × the spread of the penalty term. With ratio 1.0, prior knowledge and chemical fit have equal weight. All following cells use this value. Results: `alpha_tuning/prior_strength_calibration.csv`.

### E. Validation

All synthetic validations draw "true" sources from the database, build the "sample" as the union of their compounds, solve it **without household information** (no geo priors, no household factor), and compare the result with the truth. They are best-case tests: the true sources are always in the database.

Metrics: **compound precision** = share of the compounds of the selected sources that belong to the true mixture; **compound recall** = share of the true compounds explained (≈1 by construction, because a cover explains everything); **F1** = harmonic mean of both; **Jaccard** = overlap/union of the two compound sets; **expansion factor** = compounds of the selected sources / true compounds; **source precision/recall/F1** = the same at the level of individual sources; **false discovery rate** = share of selected sources that are not true sources.

| Block (cell) | What is tested | Setting (default) | How to read it |
|---|---|---|---|
| Synthetic perturbation (`VALIDATE_REAL`) | Robustness to missed detections (dropout) and to unrelated compounds (contamination) | 50 sources; dropout 5/10/20%; contamination 0/5/10%; 100 replicates each | Compound precision should stay high; it drops with contamination (extra compounds attract extra sources) |
| Overlap sensitivity (`VALIDATE_SYNTHETIC`) | Effect of chemical similarity between true sources | 10/100/200/300 sources; max. pairwise Jaccard 0.1, 0.5 or random; 100 replicates | Source-level metrics fall when true sources overlap; `fallback_random` > 0 means the overlap constraint could not be met and a random mixture was used |
| Chemistry-based recovery (`VALIDATE_SYNTHETIC`) | Recovery of chemically distinct mixtures | 10/100/200/300 sources with pairwise Jaccard ≤ 0.25; 100 replicates; 95% CIs and plots | Main synthetic result: high compound F1, low source F1 (values: [reference run](method_and_limitations.md#2-reference-run)) |
| Cost-consistent | Mixtures drawn in proportion to the prior (plausible sources more often) | 10/100/200/300 sources; 100 replicates | `cost_ratio` < 1: the optimizer finds a cheaper explanation than the true one – expected because many sources are near-identical |
| Noise robustness | Missing detections | 10/100/200/300 sources; 10/30/50% compounds removed; 100 replicates | Jaccard of compound sets should decrease gradually, not collapse |
| Greedy stability | Effect of removing 5% of compounds | 10/100/200/300 sources; 100 replicates | Source-level Jaccard clearly lower than compound-level Jaccard: different but chemically equivalent sources are chosen |
| Beam search diagnostics | Runtime and cover posterior for beam widths 5–50 | 50 sources; widths 5/10/30/50; 20 replicates per width | Basis for `beam_width = 5` in the real analysis. Note: this block uses temperature 1, so its posterior is almost one-hot |
| Database redundancy (LOSO) | For each source with ≥ 5 compounds: how similar is its closest other source? | all eligible sources | A high best Jaccard means many near-duplicates, which explains weak source-level recovery |
| LOSO reconstruction | Remove one source; can the others reconstruct its compounds? | all sources with ≥ 5 compounds (`MIN_COMPOUNDS`) | Compound F1, recall (≈ 1) and number of substitute sources per removed source |

**Validation interpretation engine and master summary.** Each metric is classified (Excellent/Good/Moderate/Weak) with the thresholds in `METRIC_INFO` and a short text; all results are collected in `validation_outputs/master_validation_summary.csv`.

### F. Identification for the real samples

**F1. Per-sample cover analysis.** For every sample:
1. the sample key `LLNN` is identified (`household_key()`); if it has no household metadata, household priors are not applied (logged);
2. the sample universe is reduced to compounds present in the source database; the number and share of **unattributed** compounds is logged (about 50% in the INQUIRE dust data);
3. candidate sources and their household-aware costs are computed;
4. the **greedy cover** and the **beam search covers** (`beam_width = 5`, `max_covers = 50`) are computed, duplicates removed, and all covers **ranked by total cost**. `cover_id = 1` is the best (cheapest) cover.

**F2. Post-processing and source-level values.** Total cost, number of sources, compounds, harmonized categories, source classes and class domains per cover. For every source in a cover: its prior (`source_prior`), the share of the sample's attributable compounds it contains (`source_coverage`), its probability among all candidates on a log10 scale (`source_log10P`; the probability itself is too small to store) and the same value relative to the most likely source of the cover (`source_log10P_rel`; 0 = most likely source of the cover, −2 = 100 times less likely).

**F3. Cover probabilities.** Cover probability `P(cover) = exp(−(cost − min cost) / T)`, normalized per sample, with `T = POSTERIOR_TEMPERATURE`. With the default `"auto"`, T is the median over samples of each sample's median cost gap between the alternative covers and the best cover; a typical alternative cover then gets exp(−1) ≈ 37% of the weight of the best cover. The cell logs the cost-gap quantiles, the T used, and how many samples have a best-cover P > 0.99. **These probabilities rank the covers relative to a typical gap; they are not a calibrated uncertainty estimate.**

**F4. Source probabilities and posterior diagnostics.** Per source: `marginal_P` and `posterior_P` (sum of the probabilities of the covers containing it = inclusion probability; both are computed the same way), `posterior_share` (renormalized to 1 per sample), `solution_frequency` (share of covers containing it) with a 95% Beta interval (`ci_low`, `ci_high`). Per sample: entropy, effective sample size, top-1/top-5 mass and Gini of the source shares. Saved to `source_posterior_all_samples_beam.csv`, `validation_outputs/posterior_summary.csv` and `robustness_summary.csv`.

**F5. Priors versus penalty (diagnostic).** Compares the spread of the prior cost and of the penalty cost across candidate sources and shows the origins of the sources in the best covers. Both spreads should be similar (ratio 1.0).

**F6. Compound attribution per origin.** For the best cover, each attributed compound is assigned to the highest-priority origin (by `SOURCE_WEIGHT`) among the selected sources that contain it; gives the share of compounds per database per sample (`compound_attribution_per_origin.csv`).

**F7. Final checks.** Writes `analysis_out/validation_outputs/final_checks_per_sample.csv` and logs: whether all own-product IDs are readable; for samples from households with analyzed products, how many own products were candidates and how many are in the best cover; how often the best cover equals the greedy cover; number of covers per sample; whether any blank/QC column was analyzed as a sample (must be none); median share of unattributed compounds.

**F8. Own household products in detail (optional).** For each sample whose household has analyzed products: how many of the sample compounds that occur in its own products are explained by those products, which origin explains the rest, and which household factors were applied (`validation_outputs/own_household_products_check.csv`).

**F9. Final table.** Expands the covers to compound level (only compounds present in the sample), adds compound names, probabilities and robustness statistics, and saves `cover_results_all_samples_beam.csv`, one `<sample>_beam.csv` per sample, and `unattributed_results_all_samples_beam.csv`.

---

## Running without validation

The validation blocks (section E) take several hours and are not needed for the source identification of the samples. To skip them: run all cells up to and including *Calibrate prior strength* (D4); then click the cell *Convert sample_universes DF to dictionary* and choose *Run → Run Selected Cell and All Below*. Do not only set `VALIDATE_REAL`/`VALIDATE_SYNTHETIC = False`: the other validation blocks would still run, and the master validation summary would fail.

---

## User-settable parameters

| Parameter | Cell | Default | Meaning | When to change |
|---|---|---|---|---|
| `config.yaml` (`data_dir`, `folders`) | Check columns | `data`; `preprocessing_out`, `analysis_in`, `analysis_out` | Working folder and folder names (shared with Parts 1 and 3) | Edit `config.yaml`, not the notebook |
| `USE_GEO_PRIORS` | Check columns | `True` | `True`: use `household_metadata_priors.csv`; `False`: no household information (geo multiplier = 1.0) | No household data available |
| `GLOBAL_SEED` | Imports & setup | 1 | Seed for alpha tuning | Robustness check with other seeds |
| `VALIDATION_SEED` | Separate random seed | `GLOBAL_SEED + 1000` | Seed for all validation blocks | Keep different from `GLOBAL_SEED` |
| `SOURCE_WEIGHT` | Define source weights & priors | HHP 1.0, LIT 0.8, FooDB 0.7, SPECIEUROPE 0.6, SPECIATE 0.4, CPDat 0.2 | Reliability of each database | Other databases or judgment (report it) |
| `*_KIND_PRIOR`, `*_CATEGORY_PRIOR`, `PRIOR_TABLES` | Define source weights & priors | see notebook | Plausibility of each kind/category as a dust source; default per origin | New categories; other matrices |
| `MODULE_WEIGHT` | Geo metadata influence weights | 0–1 per module | Strength of each household module | New modules; switching a module off (0) |
| `MODULE_SOURCE_MAP` | Map geo metadata modules to sources | see notebook | Which source categories each module affects | New source categories or modules |
| `HH_SAME_HOUSEHOLD`, `HH_SAME_COUNTRY`, `HH_OTHER_COUNTRY` | Source prior helper | 2.0, 0.5, 0.2 | Household factor for own analyzed products | Other weighting of own products |
| `BEAM_MAX_CANDIDATES` | Beam Search multiple-cover algorithm | `None` (all) | Cap on candidates scored per beam node | Speed-up for very large databases (e.g., 2000) |
| `USE_TIERED_COVER` | Tiered set cover | `False` | Databases used in order of `SOURCE_WEIGHT` | Comparison with a strict hierarchy |
| `alphas`, `alphas_beam`, `n_reps` | Alpha tuning cells | 10 values 10³–10⁵; 50 | Tuning grid and replicates | Plateau outside the grid |
| `best_alpha`, `best_alpha_beam` | OPTIONAL: Specify best alphas manually | automatic maximum (reference run: 4500 set by hand) | Penalty weight used everywhere after tuning | To use the lowest value on the plateau |
| `PRIOR_TO_PENALTY_RATIO` | Calibrate prior strength | 1.0 | Balance between priors and chemical fit | Optional check of the influence of the priors (e.g., 0.5 and 2.0) |
| `CALIBRATION_MAX_SAMPLES` | Calibrate prior strength | all samples | Samples used for calibration | – |
| `VALIDATE_REAL`, `VALIDATE_SYNTHETIC` | Validation cells | `True` | Switch the perturbation / overlap and chemistry-based blocks on/off | See "Running without validation" |
| Mixture sizes, replicates, rates | Validation cells | see table in E | Settings of each validation | More replicates for narrower CIs |
| `MIN_COMPOUNDS` | LOSO reconstruction | 5 | Minimum compounds for a source to be tested | – |
| `METRIC_INFO` | Validation interpretation engine | thresholds per metric | Interpretation categories | Other thresholds |
| `beam_width`, `max_covers` (in the `beam_search_covers(...)` call) | Per-sample cover analysis | 5, 50 | Breadth of beam search for the real samples | Larger width = more alternatives, slower |
| `POSTERIOR_TEMPERATURE_SETTING` | Convert costs to probabilities | `"auto"` | Temperature T of the cover probabilities; `"auto"` = typical cost gap; or a number | Exploration only; does not change the ranking of covers |

---

## Checks to look at

| Section | What to look for | Interpretation |
|---|---|---|
| A3 | Number of households and modules (29 in the INQUIRE data); no warnings about ID format or duplicates | Warnings → IDs are not `LLNN` |
| B3/B4 | All labels "OK"; no module name mismatches; "Samples matched to geo metadata: N / N" | Unmatched samples are analyzed without household priors |
| B6 | "Household products: N \| Household readable from ID: N" (both equal) | Unreadable IDs (not `LLNN_CPnn_HHP`) get the factor `HH_OTHER_COUNTRY` |
| D2/D3 | Alpha plots: a clear plateau; chosen alpha | No plateau → widen `alphas` |
| D4 | `PRIOR_STRENGTH` and the two median spreads | A different value after data changes is expected; report it |
| E | Tables per validation block; `fallback_random` = 0; master summary | Compare with the [reference run](method_and_limitations.md#2-reference-run) |
| F1 | Per sample: unattributed share, number of candidate sources, greedy cover size, number of covers | A sample without overlap with the database is skipped (logged) |
| F3 | Cost-gap quantiles, T used, samples with best-cover P > 0.99 | Many samples > 0.99 → alternative covers are much worse than the best |
| F5 | Prior and penalty cost ranges of similar size | If the prior range is much smaller, the priors hardly matter |
| F7 | Best cover identical to the greedy cover in most samples; **no QC/blank columns analyzed**; unattributed median | QC columns present → set `DROP_QC_COLUMNS = True` in Part 1 and re-run Parts 1–3 |
| F8 | Household factor own products = `HH_SAME_HOUSEHOLD`; others 0.2–0.5 | Own products are only chosen if they explain compounds at competitive cost |

## Common errors

| Message | Cause | Solution |
|---|---|---|
| `FileNotFoundError: Working folder not found` | `data_dir` in `config.yaml` wrong | Correct `data_dir` in `config.yaml` |
| `FileNotFoundError: Folder not found: …preprocessing_out` | Part 1 not run, or other folder name in `config.yaml` | Run Part 1; check `config.yaml` |
| `[geo_metadata_prior] … missing` / file not found | `USE_GEO_PRIORS = True` but no priors file in `<data_dir>/analysis_in/geo_metadata_outputs/` | Add the file ([household_priors.md](household_priors.md)) or set `USE_GEO_PRIORS = False` |
| `[sources_meta] missing columns: ['source_class', …]` | Part 1 outputs from an older pipeline version | Re-run Part 1 |
| Warning: modules in file but not in `MODULE_WEIGHT` (or vice versa) | Priors file and Part 2 module lists differ | Add the module to `MODULE_WEIGHT` and `MODULE_SOURCE_MAP` (weight 0 to ignore it) |
| Warning: label does not fire | A label in `MODULE_SOURCE_MAP` matches no source | Check spelling against `analysis_out/lookups/source_categories_per_origin.csv` |
| `NameError: best_alpha` / `PRIOR_STRENGTH` | Cells run out of order | Restart the kernel and run all cells from the top (or follow "Running without validation") |
| `KeyError` in *Build master validation summary* | A validation block was switched off | Run all validation blocks, or skip the whole validation section |
| `AssertionError: GREEDY failed to cover the universe` | Inconsistent inputs | Re-run Part 1 and Part 2 completely |
| `PermissionError` when saving | Output open in Excel | Close the file |
