# Parameters reference

All parameters a user may need to set, in one place. The **cell** column gives the heading comment of the notebook cell where the parameter is defined (use *Edit → Find* in JupyterLab). Defaults are the values in the published notebooks. After changing a parameter, restart the kernel and run the notebook from the top, then re-run all later parts.

Explanations are in the part documentation; the "Change when" column is a short reminder.

## Shared configuration – `config.yaml` (repository root)

Read by all three notebooks (PyYAML). Paths are relative to the location of `config.yaml`, or absolute. Change the working folder here, not in the notebooks.

| Key | Default | Change when |
|---|---|---|
| `data_dir` | `data` | Working folder elsewhere |
| `folders: preprocessing_in` | `preprocessing_in` | Other input folder name (Part 1 input; must exist) |
| `folders: preprocessing_out` | `preprocessing_out` | Part 1 output (read by Part 2) |
| `folders: analysis_in` | `analysis_in` | Part 2 extra input (household priors) |
| `folders: analysis_out` | `analysis_out` | Part 2 output (read by Part 3); use another name to keep runs separate |
| `folders: visualization_out` | `visualization_out` | Part 3 output (figures) |

The notebooks derive `DATA_DIR` (resolved `data_dir`) from this file; the old hard-coded `DATA_DIR = Path("../data")` no longer exists.

## Part 1 – INQUIRE_CSI_Pt1_Preprocessing

| Parameter | Cell | Default | Change when |
|---|---|---|---|
| `PREP_IN_DIR`, `PREP_OUT_DIR`, `LOOKUP_IN_DIR` | Configuration | `<data_dir>/preprocessing_in`, `<data_dir>/preprocessing_out`, `PREP_IN_DIR/lookups` | Set via `config.yaml`, not in the notebook |
| Input file names | Check columns / Load raw input data | see [input_data.md](input_data.md) | Other files |
| `GLOBAL_SEED` | Imports & setup | 1 | – |
| `ENCODINGS` | Imports & setup | utf-8, utf-8-sig, cp1252, cp1250, latin1 | Unusual file encodings |
| `STRIP_COLUMNS` | Whitespace cleanup | ID/name/category/InChIKey columns | New databases |
| `INCHIKEY_DFS`, `INCHIKEY_COL_NAMES` | InChIKey cleanup (all source DBs & dust) | all six source databases + both dust tables; `inchikey`, `InChIKey`, `InChiKey` | New databases; InChIKey column with another name |
| `INCHIKEY_MISSING` | same | "", "nan", "none", "na", "n/a", "null", "<na>", "-", "--" | Other placeholders in your files |
| `INCHIKEY_STANDARD` | same | `[A-Z]{14}-[A-Z]{10}-[A-Z]` (only used to report odd keys) | – |
| `SOURCE_CLASS_FILE`, `SOURCE_CLASS_SHEET` | Add the two-level reporting categories… | `LOOKUP_IN_DIR / "source_class_mapping.xlsx"` (`preprocessing_in/lookups/`), sheet `source_class_mapping` | Other mapping file |
| `DROP_EMPTY_COLS_STD` | same | `False` | Drop empty columns from separate standardized databases |
| `DROP_COLS_STD` | same | `["ID", "#"]` | Other uninformative columns |
| `COMPOUND_COLS` | Save all compounds (inchikey, names, CAS, DTXSID)… | name, CAS and DTXSID columns per database | Other column names in your source files |
| `FEATURE_NAME_PRIORITY` | same | CPDat, SPECIATE, SPECIEUROPE, FooDB, literature products, own household products | Prefer names from another database |
| `MULTI_SEP` | same | `"; "` | Other separator for several values in one cell |
| `GROUP_META_COLS` | Aggregate equivalent products/sources | kind, general category, harmonized label | Not recommended |
| `dust_cols_drop` | Reshape sample data | `7S_CS_01`–`7S_CS_04`, `Blank_NIST` (example) | **Always**: your own blank/QC columns |
| `DROP_QC_COLUMNS` | Reshape sample data | `True` | `False` only to inspect blanks |
| `REAGGREGATE_AFTER_MASKING` | Mask products/sources | `True` | Check only |

## Part 2 – INQUIRE_CSI_Pt2_Analysis_and_Validation

| Parameter | Cell | Default | Change when |
|---|---|---|---|
| `PREP_OUT_DIR`, `AN_IN_DIR`, `AN_OUT_DIR` | Configuration | `<data_dir>/preprocessing_out`, `…/analysis_in`, `…/analysis_out` | Set via `config.yaml`, not in the notebook |
| `USE_GEO_PRIORS` | Check if necessary columns exist… | `True` | `False` if no household priors file is available |
| `GLOBAL_SEED` | Imports & setup | 1 | Seed robustness check |
| `VALIDATION_SEED` | Separate random seed for validation | `GLOBAL_SEED + 1000` | Keep ≠ `GLOBAL_SEED` |
| `SOURCE_WEIGHT` | Define source weights & priors | 1.0 / 0.8 / 0.7 / 0.6 / 0.4 / 0.2 | Other databases or judgment |
| `CONS_PRODS_*`, `PUC_*`, `FOODB_*`, `SPECIATE_*` `_KIND_PRIOR` / `_CATEGORY_PRIOR` | Define source weights & priors | see notebook | New categories; other matrices |
| `PRIOR_TABLES` (default kind prior per origin) | Define source weights & priors | 0.5 (HHP, LIT), 0.2 (CPDat, FooDB), 0.3 (SPECIATE, SPECIEUROPE) | New origins |
| `MODULE_WEIGHT` | Geo metadata influence weights | 0–1 per module (0 for vaping, ventilation, pfas) | New/disabled modules |
| `MODULE_SOURCE_MAP` | Map geo metadata modules to sources | see notebook | New categories/modules |
| `HH_SAME_HOUSEHOLD` / `HH_SAME_COUNTRY` / `HH_OTHER_COUNTRY` | Source prior helper | 2.0 / 0.5 / 0.2 (same `LLNN` / same `LL` / other) | Other weighting of own products |
| `BEAM_MAX_CANDIDATES` | Beam Search multiple-cover algorithm | `None` | Speed-up (e.g., 2000) |
| `USE_TIERED_COVER` | OPTIONAL: Tiered set cover by source origin | `False` | Comparison with a strict database hierarchy |
| `alphas`, `alphas_beam`, `n_reps` | Alpha tuning cells | 10 values 10³–10⁵, 50 reps | Plateau outside the grid |
| `best_alpha`, `best_alpha_beam` | OPTIONAL: Specify best alphas manually based on the plots | automatic (highest score); reference run: 4500 | Use the lowest value on the plateau |
| `PRIOR_TO_PENALTY_RATIO` | Calibrate prior strength | 1.0 | Optional check of the influence of the priors (e.g., 0.5 / 2.0) |
| `CALIBRATION_MAX_SAMPLES` | Calibrate prior strength | all samples | – |
| `VALIDATE_REAL` | Synthetic perturbation validation | `True` | See "Running without validation" in Part 2 doc |
| `VALIDATE_SYNTHETIC` | Synthetic recovery validation cells | `True` | same |
| `dropout_rates`, `contam_rates` | Synthetic perturbation validation | [0.05, 0.1, 0.2], [0, 0.05, 0.1] | – |
| `mixture_sizes`, `replicates` | Validation cells | [10, 100, 200, 300], 100 | More replicates for narrower CIs |
| `overlap_thresholds` | Synthetic recovery validation with overlap sensitivity | [0.10, 0.50, "random"] | – |
| `missing_rates` | Noise robustness validation | [0.1, 0.3, 0.5] | – |
| `drop_fraction` | GREEDY stability validation | 0.05 | – |
| `beam_widths` | Beam Search validation | [5, 10, 30, 50] | – |
| `MIN_COMPOUNDS` | LOSO reconstruction validation | 5 | – |
| `METRIC_INFO` | Validation interpretation engine | thresholds per metric | Other interpretation thresholds |
| `beam_width`, `max_covers` | Per-sample cover analysis (`beam_search_covers(...)` call) | 5, 50 | More alternatives (slower) |
| `POSTERIOR_TEMPERATURE_SETTING` | Convert costs to probabilities | `"auto"` | A fixed number (e.g., 500.0) for comparisons between runs |

Fixed inside functions (change only if you know why): `lambda_cover = 6.0`, `lambda_depth = 0.05` (beam priority), `max_children = 5` (beam search), compound penalty `1/√frequency`, alpha-tuning score `precision − 0.25 × (expansion − 1)`.

## Part 3 – INQUIRE_CSI_Pt3_Visualization

| Parameter | Cell | Default | Change when |
|---|---|---|---|
| `IN_DIR`, `FIG_DIR` | Configuration | `<data_dir>/analysis_out/set_cover_outputs`, `<data_dir>/visualization_out` | Set via `config.yaml`, not in the notebook |
| `DROP_LL_SAMPLES` (+ 2-letter code) | Ensure labels are clean | `False` | Exclude one sample group |
| Category level (silenced lines) | Color maps, figure, loop, heatmap and Sankey cells | `source_class_domain` | Finer reporting level |
| Category threshold (`>= 1`) | Heatmap and Sankey cells | 1% in at least one sample group | More/fewer categories shown |
| `country_name_map` | Sankey cells | example codes | Your 2-letter codes and group names |
| `SOURCE_LABEL_OFFSET`, `LEADER_LINE_COLOR`, `LEADER_LINE_WIDTH`, `OPEN_HTML_IN_BROWSER` | Second Sankey cell | 0.04, gray, 0.8, `True` | Layout; no browser available |
| Color lists | Color maps | see notebook | Journal style |
| `figsize`, font sizes, `dpi` | Heatmap cells | see notebook, 600 dpi | Journal requirements |
