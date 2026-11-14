# Installation, environment and reproducibility

This page explains what you need to install, how to set up the Python environment, how the working folder is organized, and what makes the results reproducible.

---

## 1. Software to install

| Software | Version used | Required? | Where to get it | Notes |
|---|---|---|---|---|
| **Anaconda Distribution** (includes Python, the `conda` package manager, Anaconda Navigator and JupyterLab) | any recent | yes (or Miniconda) | https://www.anaconda.com/download | Free for individual/academic use; check your institution's license terms. Miniconda (https://docs.anaconda.com/miniconda/) is a smaller alternative without the Navigator. |
| **Python** | 3.11.14 | yes | installed into the environment (step 2) | The notebooks were developed and tested with Python 3.11.14 (Anaconda build, 64-bit, Windows). |
| **JupyterLab** | 4.4.7 | yes | installed into the environment (step 2) | Runs **locally** in your web browser. **No account or login is needed.** |
| **Web browser** | any modern browser | yes | Chrome, Firefox, Edge, Safari | Used to run JupyterLab and to open the interactive HTML figures of Part 3. |
| **Internet connection** | – | for installation and for viewing HTML figures | – | The Part 3 HTML figures load the Plotly JavaScript library from the internet (CDN) when they are opened. |
| Git or GitHub Desktop | any | optional | https://git-scm.com, https://desktop.github.com | Only to clone the repository; you can also download it as a ZIP file from GitHub. |
| Spreadsheet program (Excel, LibreOffice Calc) | any | optional | – | To inspect input and output CSV files. Some output files are too large for Excel (> 1 048 576 rows); open those with Python instead. |

**Tested on:** Microsoft Surface Laptop 5, Intel Core i7-1265U (12th generation, 2.7 GHz), 16 GB RAM, Windows 11 Enterprise 24H2 (64-bit).

**Runtime on this laptop** (INQUIRE reference run, ~200 samples):

| Part | Runtime (hh:mm:ss) |
|---|---|
| Part 1 – `INQUIRE_CSI_Pt1_Preprocessing` | 00:13:39 |
| Part 2 – `INQUIRE_CSI_Pt2_Analysis_and_Validation` | 05:02:00 |
| Part 3 – `INQUIRE_CSI_Pt3_Visualization` (optional) | 00:12:13 |
| Parts 1 + 2 | 05:15:39 |
| Parts 1 + 2 + 3 | 05:27:52 |

Runtimes scale with the number of samples, the number of compounds per sample and the size of the source database.

**Recommended:** 16 GB RAM or more and about 6 GB of free disk space for inputs and outputs. Part 1 handles ~1.6 million source–compound rows, and Part 2 writes a result table of ~2 million rows. No graphics card (GPU) is needed.

**Operating system:** developed and tested on Windows 11. The code uses only platform-independent paths (`pathlib`), so it should also run on macOS and Linux (not tested).

---

## 2. Set up the Python environment

An *environment* is an isolated Python installation with exactly the package versions needed for this pipeline, so it does not interfere with other Python projects on your computer.

### Option A – command line (recommended)

1. Open the **Anaconda Prompt** (Windows: Start menu → "Anaconda Prompt"; macOS/Linux: a normal terminal).
2. Go to the repository folder, e.g.
   ```
   cd C:\path\to\INQUIRE_CSI
   ```
3. Create the environment from the file `environment.yml` (takes a few minutes):
   ```
   conda env create -f environment.yml
   ```
4. Activate it:
   ```
   conda activate inquire_csi
   ```
5. Start JupyterLab from the repository folder:
   ```
   jupyter lab
   ```
   JupyterLab opens in your browser. Navigate to `notebooks/`.

Alternative to step 3 (pip only):
```
conda create -n inquire_csi python=3.11
conda activate inquire_csi
pip install -r requirements.txt
```

### Option B – Anaconda Navigator (graphical)

1. Open **Anaconda Navigator** → **Environments** → **Import** → select `environment.yml` → name it `inquire_csi` → **Import**.
2. Go to **Home**, choose `inquire_csi` in the "Applications on" drop-down, and click **Launch** under JupyterLab.

### Check the installation

In a new notebook cell run:
```python
import sys, pandas, numpy, scipy, statsmodels, matplotlib, plotly, networkx
print(sys.version, pandas.__version__, numpy.__version__)
```
It should print Python 3.11.x (tested: 3.11.14), pandas 2.3.3 and numpy 2.3.3.

---

## 3. Python packages used

Only the packages below are imported by the three notebooks. All other packages in a typical Anaconda installation are not needed.

| Package | Version | Used in part | Purpose |
|---|---|---|---|
| pandas | 2.3.3 | 1, 2, 3 | Tables (DataFrames): reading, merging, reshaping, writing CSV |
| numpy | 2.3.3 | 1, 2, 3 | Numerical arrays, logarithms, random numbers |
| scipy | 1.16.3 | 1, 2, 3 | `scipy.stats.beta`: credible intervals for solution frequencies |
| statsmodels | 0.14.5 | 1, 2, 3 | `proportion_confint` (imported in shared setup cell) |
| matplotlib | 3.10.7 | 1, 2, 3 | Static figures (alpha tuning, validation, heatmaps); `matplotlib.colormaps` in Part 3 |
| plotly | 6.5.2 | 3 | Interactive 3D networks and Sankey diagram (HTML) |
| networkx | 3.5 | 3 | Sample–compound–source network graphs |
| openpyxl | 3.1.5 | 1, 2, 3 | Reading Excel (.xlsx) input files |
| pyyaml | 6.0.3 | 1, 2, 3 | Reading the shared `config.yaml` (working folder and subfolder names) |
| tqdm | 4.67.1 | 1, 2, 3 | Progress bars |
| ipywidgets | 8.1.7 | 1, 2, 3 | Needed by `tqdm.auto` to draw progress bars in JupyterLab |
| jupyterlab | 4.4.7 | all | Notebook interface |
| ipykernel | 6.30.1 | all | Runs Python inside JupyterLab |
| ipython | 9.7.0 | all | `display()` of tables in notebooks |

Python standard-library modules (no installation needed): `pathlib`, `re`, `time`, `datetime`, `random`, `hashlib`, `logging`, `collections`, `functools`, `dataclasses`, `json`, `webbrowser`.

---

## 4. Folder structure

Keep the repository structure; then the default working folder (`data_dir: data` in `config.yaml`, i.e., the `data` folder next to `notebooks`) works without changes. The output folders are named `preprocessing_out`, `analysis_out` and `visualization_out` and are created automatically. The input folder `preprocessing_in/` and its subfolder `source_databases/` (fixed name) must exist before Part 1 is run.

```
INQUIRE_CSI/
├── config.yaml                             ← shared settings: data_dir and folder names (read by all notebooks)
├── notebooks/                              ← open and run the notebooks from here
├── example_data/                           ← synthetic test data (mirrors the input folders of data/)
│   ├── preprocessing_in/
│   └── analysis_in/
└── data/                                   ← working folder (data_dir)
    ├── preprocessing_in/                   ← Part 1 inputs (you create/copy)
    │   ├── Sample_Data.xlsx                ← your samples or example data
    │   ├── source_databases/               ← fixed name; source databases (from Zenodo)
    │   │   ├── Own_Household_Products.csv
    │   │   ├── Own_Household_Products_Metadata.csv
    │   │   ├── Literature_Products.csv
    │   │   ├── CPDat/                      ← 3 .tsv files
    │   │   ├── FooDB.csv
    │   │   ├── SPECIATE.xlsx
    │   │   └── SPECIEUROPE.xlsx
    │   └── lookups/source_class_mapping.xlsx   ← reporting classes (from Zenodo)
    ├── preprocessing_out/                  ← Part 1 outputs
    │   ├── inquire_csi_pt1.sqlite          ← SQLite database (read by Part 2)
    │   ├── inspection/                     ← CSV and Excel copies of the database tables (not read by any notebook)
    │   ├── databases_id_w_suffix/          ← optional (only if EXPORT_TRACE_TABLES = True in Part 1)
    │   ├── databases_standardized/         ← per-database files only if EXPORT_TRACE_TABLES = True
    │   ├── all_sources_aggregated/
    │   ├── masked_sources/
    │   └── lookups/                        ← unmapped source categories (QC)
    ├── analysis_in/                        ← optional Part 2 input
    │   └── geo_metadata_outputs/           ← household priors
    ├── analysis_out/                       ← Part 2 outputs (read by Part 3)
    │   ├── lookups/
    │   ├── geo_check/
    │   ├── alpha_tuning/
    │   ├── validation_outputs/
    │   └── set_cover_outputs/
    └── visualization_out/                  ← Part 3 outputs (figures)
```

If you prefer another location, change `data_dir` in `config.yaml` (relative to `config.yaml`, or an absolute path such as `D:/projects/INQUIRE_CSI/data`; use forward slashes `/` on Windows). The subfolder names can be changed under `folders:`. All three notebooks read this file, so there is nothing to change in the notebooks.

**Log files:** Parts 1–3 write a log file (copy of all printed messages) into the folder from which the notebook runs (`notebooks/`): `inquire_csi_pt1_preprocessing_log_<yymmdd>.log`, `inquire_csi_pt2_analysis_and_validation_log_<yymmdd>.log` and `inquire_csi_pt3_visualization_log_<yymmdd>.log`. A new run on the same day overwrites the log of that day. Keep them as a record of each run, but do not upload them to a public repository (they contain sample IDs and per-sample results).

---

## 5. Reproducibility

- **Fixed random seeds.** `GLOBAL_SEED = 1` is set in the setup cell of Parts 1 and 2 (Python `random` and `numpy`). Alpha tuning uses `GLOBAL_SEED`; all validation cells of Part 2 use a separate `VALIDATION_SEED = GLOBAL_SEED + 1000 = 1001`, so that validation mixtures are never identical to tuning mixtures.
- **Deterministic algorithms.** The greedy cover and beam search score all candidate sources and sort them deterministically (cheapest first, ties by index). No step depends on Python's randomized string hashing, so results are identical after a kernel restart and between runs on the same input data and package versions.
- **Part 3 layout.** The overall 3D network adds a small random vertical offset to the sample nodes (no seed is set in Part 3), so the exact node positions of that figure differ slightly between runs. All numbers, heatmaps and Sankey diagrams are deterministic.
- **Order of execution matters.** Always run each notebook top to bottom after *Kernel → Restart Kernel* (*Run All Cells*). Several cells use results of earlier cells (e.g., the prior strength is calibrated after alpha tuning and is then used by all later cells).
- **Package versions.** Use the versions in `requirements.txt`. Other pandas/numpy versions may change sorting of ties or floating-point details and hence, rarely, the choice between equally good sources.
- **Record what you ran.** Keep the log files and note any parameter changes (see [parameters.md](parameters.md)).
