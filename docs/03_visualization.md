# Part 3 – INQUIRE_CSI_Pt3_Visualization (Optional)

## Purpose

Part 3 visualizes the **best cover** (`cover_id = 1`) of every sample:
- interactive **3D network** figures linking samples, compounds and sources (one for all samples, one per sample group);
- **sample-group × source-category heatmaps** (portrait and landscape);
- a **sample-group × source-category Sankey diagram**.

Part 3 is optional: the source identification itself is complete after Part 2.

All shares are expressed as **percentages of the unique attributable compounds of a sample group** (compounds for which a source exists in the database; all samples of a group pooled). They are **non-exclusive**: a compound found in sources of two categories counts for both categories, so the percentages of a group do not add up to 100%.

**Category level.** By default, sources are grouped by `source_class_domain` (the broadest reporting level). The notebook also contains silenced lines for `source_general_category`, `source_harmonized` and `source_class`; to switch, silence the `source_class_domain` line and un-silence the wanted one, consistently in each figure cell (look for the comments `# source_class_domain`, `# source_class`, …).

## Inputs

| File | From | Mandatory columns |
|---|---|---|
| `analysis_out/set_cover_outputs/cover_results_all_samples_beam.csv` | Part 2 | `sample`, `source_name`, `source_general_category`, `source_harmonized`, `source_class`, `source_class_domain`, `P`, `marginal_P`, `inchikey`, `feature_name`, `n_unique_chemicals`, `n_unique_sources`, `n_unique_source_harmonized` (plus `cover_id`) |

The **sample group** is the 2-letter sample code `LL`, i.e., the first two letters of the sample ID (pattern `LLNN[_suffix]`, e.g., `FR01_LS2` → `FR`). In the INQUIRE data, `LL` is the country; with other data it can be any grouping (e.g., site, campaign, matrix). The notebook and the output file names still use the word "country" for this group (e.g., column `country`, `country_name_map`, `inquire_csi_country-source_sankey.html`).

## Outputs

Written directly into the folder `data/visualization_out/` (created automatically; name set in `config.yaml`):

| File | Content |
|---|---|
| `inquire_csi_figure.html` | Interactive 3D network, all samples |
| `inquire_csi_figure_<LL>.html` | Interactive 3D network per sample group (`LL` = 2-letter sample code) |
| `inquire_csi_country-source_category_heatmap.png` | Heatmap, portrait (categories as rows, sample groups as columns), 600 dpi |
| `inquire_csi_country-source_category_heatmap_land.png` | Heatmap, landscape (sample groups as rows), 600 dpi |
| `inquire_csi_country-source_sankey.html` | Sankey diagram, simple version |
| `inquire_csi_country-source_category_sankey.html` | Sankey diagram with leader lines from each category box to its label (final version) |

Open the HTML files in a web browser (internet connection needed; Plotly is loaded from the internet). They can be rotated, zoomed and hovered for details. Static images can be exported with the camera icon in the figure toolbar.

## Runtime

About 12 minutes on the test laptop (INQUIRE reference run: 00:12:13); building and saving the 3D networks takes most of the time. The HTML file of the full network can be tens of MB.

---

## Notebook sections in run order

**1. Title; reset environment; imports & setup.** Log file `inquire_csi_pt3_visualization_log_<yymmdd>.log`.

**2. Check columns and load input.** Reads `config.yaml` and sets `DATA_DIR`, the input folder `IN_DIR = <analysis_out>/set_cover_outputs` and the figure folder `FIG_DIR = <visualization_out>`, checks the mandatory columns and loads the main result table of Part 2.

**3. Clean labels, sample groups and cover 1.** Strips spaces from labels, creates the 2-letter sample code (`LL`, stored in the column `country`), optionally removes all samples of one group (`DROP_LL_SAMPLES`), and keeps only rows with `cover_id = 1`.

**4. 3D network – all samples.**
- *Build graph:* a network with three node types – samples, compounds and sources – and links sample–compound (compound detected in the sample) and compound–source (compound explained by the source in the best cover of that sample).
- *Connection counts:* number of links per node, shown when hovering.
- *Earth-layer spherical layout:* a 3D arrangement like the layers of the Earth: **samples on the outer "crust"**, grouped in one sector per sample group; **compounds in the "mantle"**; **sources in the "core"**.
- *Color maps:* one color per sample group (samples) and per source category (sources); compounds are gray.
- *Figure and legends:* Plotly 3D figure with links and nodes; sample-group legend on the left (titled "Country"), source-category legend on the right; saved as `inquire_csi_figure.html`.

**5. 3D networks per sample group.** The same construction for each sample group separately (samples evenly distributed around the full circle; only categories present in that group in the legend), saved as `inquire_csi_figure_<LL>.html`. The log reports, per group, the number of rows, samples, compounds, sources, nodes and links.

**6. Statistics.** Prints the number of sample groups, samples, compounds, sources, and of the four category levels in the best covers, overall and per sample group.

**7. Sample-group × source-category heatmaps.** For each sample group and source category: number of unique compounds (by compound name) explained by sources of that category, divided by the number of unique attributed compounds of the group. Categories that reach ≥ 1% in at least one group are shown, ordered by overall importance; cells show "count (percentage)". Two orientations: portrait and landscape.

**8. Sample-group × source-category Sankey diagrams.** Sample groups on the left, source categories on the right, link width = number of unique compounds per group × category (non-exclusive). Categories below 1% in every group are merged into "Other". Hovering shows the full group name (from `country_name_map`; e.g., the country name) and the share of the group's compounds. The first Sankey cell saves a simple version. The second cell saves the final version, with gray leader lines from each category box to its label, and opens it in the default browser (`OPEN_HTML_IN_BROWSER`). The leader lines are drawn by the browser when the HTML file opens; they do not appear in the JupyterLab preview. You can skip the first Sankey cell.

---

## User-settable parameters

| Parameter | Cell | Default | Meaning | When to change |
|---|---|---|---|---|
| `config.yaml` (`data_dir`, `folders`) | Check columns | `data`; `analysis_out`, `visualization_out` | Working folder and folder names (shared with Parts 1–2) | Edit `config.yaml`, not the notebook |
| `IN_DIR`, `FIG_DIR` | Check columns | `<data_dir>/analysis_out/set_cover_outputs`, `<data_dir>/visualization_out` | Input and figure folders (derived from `config.yaml`) | – |
| `DROP_LL_SAMPLES` and the 2-letter code (e.g., `"FR"`) | Ensure labels are clean | `False` | Removes all samples of one sample group from all figures | Exclude a group |
| Category level (silenced/un-silenced lines) | Color maps, figure, loop, heatmap and Sankey cells | `source_class_domain` | Level at which sources are grouped and colored | Finer reporting (`source_class`, `source_general_category`, `source_harmonized`) |
| Minimum share for showing a category (`>= 1`) | Heatmap and Sankey cells | 1% | Categories below this share in every sample group are hidden (heatmap) or merged into "Other" (Sankey) | More or fewer categories |
| `country_name_map` | Sankey cells | example codes (FR, ES, US, SK, NZ, CA, PL, FI) with country names | Full names of the sample groups shown in the Sankey | Your own 2-letter codes (codes not listed are shown as codes) |
| `SOURCE_LABEL_OFFSET`, `LEADER_LINE_COLOR`, `LEADER_LINE_WIDTH` | Second Sankey cell | 0.04, gray, 0.8 | Position of the labels and style of the leader lines | Layout |
| `OPEN_HTML_IN_BROWSER` | Second Sankey cell | `True` | Opens the final Sankey in the default browser | `False` on a server without browser |
| Color lists | Color map cells | see notebook | Colors of sample groups and categories (repeated automatically if there are more) | Journal style |
| `figsize`, font sizes, `dpi` | Heatmap cells | see notebook, 600 dpi | Layout of the PNG figures | Number of categories; journal requirements |

---

## Checks to look at

| Section | What to look for | Interpretation |
|---|---|---|
| 3 | Number of rows before/after keeping cover 1; "All samples kept" | Expected unless `DROP_LL_SAMPLES = True` |
| 5 | Sample groups listed: only real groups | A code like `7S` means QC samples were analyzed → set `DROP_QC_COLUMNS = True` in Part 1 and re-run Parts 1–3 |
| 6 | Number of samples = number of real samples | Otherwise QC columns or missing samples |
| 7/8 | Number of categories retained (≥ 1%) | Very many categories → use a broader level (`source_class_domain`) or a higher threshold |
| Figures | Percentages per sample group do **not** sum to 100% | Expected (non-exclusive attribution) |

## Common errors

| Message | Cause | Solution |
|---|---|---|
| `FileNotFoundError` for `cover_results_all_samples_beam.csv` | Part 2 not run or `config.yaml` changed in between | Run Part 2; use the same `config.yaml` (`data_dir`, `analysis_out`) |
| `missing columns: ['source_class', …]` | Part 2 output from an older pipeline version | Re-run Parts 1 and 2 |
| `KeyError` in a color lookup | Category level changed in some cells but not in others | Use the same level in all figure cells |
| HTML figure opens blank | No internet connection (Plotly loaded from CDN) | Connect to the internet, or change `include_plotlyjs="cdn"` to `include_plotlyjs=True` in the `write_html` calls (files become ~4 MB larger but work offline) |
| Browser very slow with the full 3D network | Very many nodes/links | Use the per-group figures |
| Warning `RequestsDependencyWarning …` | Version check of the `requests` package | Harmless |
