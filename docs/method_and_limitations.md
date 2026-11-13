# Method, reference run, and limitations

This page summarizes the model behind INQUIRE_CSI, the results of the reference run on the INQUIRE dust data, and the limitations to keep in mind when interpreting results. Technical details of each step are in the part documentation ([Part 1](01_preprocessing.md), [Part 2](02_analysis_and_validation.md)).

---

## 1. Model in brief

### 1.1 What is identified

For each sample, the **sample universe** is the set of InChIKeys detected in it. Only compounds that occur in at least one source of the master contaminant source database (MCSDB) can be attributed. The rest are **unattributed** and are not part of any share reported by the pipeline.

### 1.2 Weighted set cover

Each source *i* covers the set *A_i* of sample compounds it contains. A **cover** is a set of sources whose compounds together include every attributable compound of the sample. The pipeline searches for covers with the lowest total cost

  cost(cover) = Σ_{i ∈ cover} c_i,  c_i = P_i + α · penalty_i

- **Prior/coverage term:** P_i = −PRIOR_STRENGTH · log(prior_i) − log(s_i) + constant, with *s_i* = |A_i| / Σ_j |A_j| (share of sample compounds the source explains among all candidates). Plausible and chemically comprehensive sources are cheap.
- **Frequency penalty:** penalty_i = (Σ_{c ∈ source_i, c ∉ sample} 1/√f_c) / |source_i|, scaled to 0–1, where *f_c* is the number of database sources containing compound *c*. Sources that would bring many compounds **not** found in the sample (especially rare ones) are expensive.
- **α (alpha):** tuned on synthetic mixtures (score = compound precision − 0.25 × (expansion − 1)). By default the alpha with the highest score is used; because the score curve usually forms a plateau, the lowest value on the plateau can be set by hand (e.g., 4500 based on a reference run).

Two algorithms are used:
- a **greedy** algorithm, which repeatedly adds the source with the lowest cost per newly covered compound;
- a **beam search** (beam width 5, up to 50 covers), which finds alternative covers.

All covers are ranked by total cost; the cheapest is considered the **best cover** (`cover_id = 1`).

### 1.3 Priors

prior_i = SOURCE_WEIGHT[origin] × √(kind prior × category prior) × geo multiplier × household factor

| Component | Values | Meaning |
|---|---|---|
| `SOURCE_WEIGHT` | own household products 1.0; literature consumer products 0.8; FooDB 0.7; SPECIEUROPE 0.6; SPECIATE 0.4; CPDat 0.2 | Reliability of the database for indoor dust (measured > declared) |
| Kind and category priors | 0.01–1.0 per kind/category and origin | Plausibility of the source type as a residential dust source, based on the literature (see References) |
| Geo multiplier (optional) | exp(Σ_m w_m · (L_m − 0.5)) over the household modules *m* linked to the source category | Household information ([household_priors.md](household_priors.md)); L_m = household likelihood (0.02–0.98, mean 0.5), w_m = `MODULE_WEIGHT` (0–1). Neutral = 1; always 1 if `USE_GEO_PRIORS = False` |
| Household factor (own products only) | same sample key `LLNN` 2.0; same 2-letter code `LL` 0.5; other 0.2 | Products collected with a sample (same key) are preferred for that sample |

Synthetic validations use the prior **without** geo multiplier and household factor (no household).

### 1.4 Balancing priors and chemistry

`PRIOR_STRENGTH` is calibrated on all real samples so that two spreads are related by `PRIOR_TO_PENALTY_RATIO`: the spread of the prior term, and the spread of the penalty term. A spread is the 5th–95th percentile across candidate sources, taken as the median over samples. With the default ratio of 1.0, prior knowledge and chemical fit have equal weight. All costs are computed in log space to avoid numerical underflow.

### 1.5 Cover "posterior"

P(cover) = exp(−(cost − min cost) / T), normalized per sample. Source-level inclusion probabilities (`marginal_P`, `posterior_P`) are sums over the covers that contain the source. The temperature T (`POSTERIOR_TEMPERATURE`) sets the scale on which cost differences count. Cost differences between covers are large (hundreds to thousands of cost units), so with T = 1 the best cover would receive practically all probability. The default `"auto"` sets T to the typical cost gap between the best and the alternative covers (median over samples of each sample's median gap); a typical alternative cover then gets exp(−1) ≈ 37% of the weight of the best cover. The probabilities therefore show how the alternatives compare with the best cover, relative to the typical gap in the data set (see limitations).

### 1.6 Use for other matrices (e.g., indoor air)

The method only requires a list of InChIKeys per sample, so it can be applied to other matrices. However, three settings were designed and tuned for indoor dust:
- the kind and category priors (e.g., "direct contributor to residential dust");
- the links between household modules and source categories;
- alpha.

For other matrices, review the priors (e.g., combustion and outdoor sources may matter more for air), re-run the alpha tuning, choose alpha again, and report the settings used.

---

## 2. Reference run

Results of the reference run on the INQUIRE household dust data. All other documentation pages give rounded values or refer to this table. **Update this table after each final run.**

| | Value |
|---|---|
| Run date / pipeline version | 2026-10-13 / 1.0 |
| Sample data | INQUIRE household dust, 193 samples, 8 countries (data version 2026-08-12) |
| MCSDB version 1.0 | [Will be available from Zenodo after 1-year embargo]; built from SPECIEUROPE v3.0, SPECIATE v5.4, CPDat v4.0, FooDB v1.0, 7 literature studies, and own household products |
| Hardware / runtime | Microsoft Surface Laptop 5, Intel Core i7-1265U, 16 GB RAM, Windows 11; Python 3.11.14 / Part 1 00:13:39, Part 2 05:02:00, Part 3 00:12:13 (total 05:27:52) |
| **Part 1** | |
| Input rows: CPDat compositions; own household products; literature products; FooDB; SPECIEUROPE; SPECIATE | 1198080; 4198; 40778; 269900; 1735; 203839 |
| Sources after standardization → after first aggregation | 257969 → 97241 (−62%) |
| Sources with ≥ 1 sample compound → after second aggregation | 44091 → 20657 (−53%) |
| Distinct sample compounds in the masked MCSDB | 1231 |
| Samples analyzed (after removing blank/QC columns) | 193 |
| **Part 2** | |
| Households with priors; modules | 205; 29 |
| Own household products (household readable from ID) | 435 (435) |
| `best_alpha` (automatic maximum or set by hand) | e.g., 4500 |
| `PRIOR_STRENGTH` (`PRIOR_TO_PENALTY_RATIO` = 1.0) | ≈ 567.9 |
| Unattributed compounds per sample, median (IQR) | 0.51 (0.48-0.52) |
| Best cover = greedy cover | 100% of samples |
| `POSTERIOR_TEMPERATURE` ("auto"); median best-cover `P`; samples with best-cover `P` > 0.99 | 25413; 0.666; 1 |
| Synthetic recovery (chemistry-based): compound F1 | 0.87 (10 sources) … 0.96 (300 sources); mean ≈ 0.88 |
| Synthetic recovery: source F1 | ≈ 0.14 (range 0.08–0.18 across settings) |
| Greedy stability (5% compounds removed): source / compound Jaccard | 0.64–0.77 / 0.93-0.96 |
| Database redundancy: median best Jaccard to the closest other source | ≈ 0.83 |
| Leave-one-source-out (LOSO) reconstruction: compound F1 (precision, recall); substitutes per source | ≈ 0.82 (0.72, 1.0); ≈ 2.5 |

---

## 3. Limitations and how results should be reported

1. **Incomplete source coverage.** Many compounds have no source in the MCSDB (about half in the INQUIRE dust data). All shares (per category, origin, or sample group) refer to **attributable compounds only** and must not be read as shares of all compounds in the sample.

2. **Category level, not product level.** Compound-level recovery is good, but individual sources are poorly identified (low source F1), because many MCSDB sources are nearly identical (high median best Jaccard). The optimizer then picks one of several equivalent sources. **Results are therefore reported at source-category level** (`source_general_category`, or the cross-database reporting levels `source_class` / `source_class_domain`). Named products in a cover should be read as *representatives* of a group of chemically similar sources.

3. **Cover probabilities are not an uncertainty estimate.** `P`, `marginal_P`, and `posterior_P` are derived from cost differences scaled by the temperature T. With T = 1 they would be almost one-hot (the best cover ≈ 100%); with the default "auto" T they show how close the alternative covers are to the best one, relative to the typical gap in the data set. Their absolute values depend on this convention and on the covers that beam search happens to find. They are not calibrated probabilities and do not reflect measurement or identification uncertainty. Robustness is assessed with the validation blocks instead. POSTERIOR_TEMPERATURE used: 25,413.13 (setting: auto).

4. **Results depend on the priors.** When several databases contain a compound, which one explains it depends on three settings: `SOURCE_WEIGHT`, the category priors, and `PRIOR_STRENGTH`. The prior values are expert judgments based on the literature, not fitted parameters. The influence of the priors on the origin shares was not quantified for the reference run. Users can test it by re-running Part 2 with other values of `PRIOR_TO_PENALTY_RATIO` (e.g., 0.5 and 2.0).

5. **Synthetic validations are best-case checks.** Synthetic mixtures are assembled from database sources, so the true sources are always present and their compound profiles are complete and exact. Real samples contain compounds from sources not in the database, transformation products and unidentified features. Real-world performance is therefore expected to be lower.

6. **Non-exclusive percentages.** A compound can be explained by sources of several categories in the best cover; it then counts for each of them. Category percentages per sample group do not sum to 100%.

7. **Presence/absence only.** Neither sample concentrations nor source compositions (concentrations, weight fractions, etc.) are used; the master source database is presence/absence only. A compound detected at trace level counts as much as a major constituent. Quantitative intermediate databases can be rebuilt with the cleanup pipelines ([input_data.md, section 2.7](input_data.md#27-how-the-source-database-inputs-were-prepared)).

8. **Identification by InChIKey.** Compounds are matched only by InChIKey (retrieved for all source data with PubChem_Retriever with subsequent manual review and gap filling). The identification confidence of the non-target screening, stereoisomers, and different InChIKeys for the same substance (e.g., salts) all affect matching.

9. **Database properties.** CPDat lists manufacturer-declared ingredients (not measurements) and is US-oriented, SPECIATE profiles are US emission profiles, and literature data are heterogeneous. Their lower `SOURCE_WEIGHT` reflects this but cannot remove it.

10. **Relative household information.** Household likelihoods are ranks within the study population, not absolute probabilities. Modules with few observations are neutral (0.5) for most households.

11. **Dust-specific settings.** Priors and alpha were designed and tuned for indoor dust (see "Use for other matrices" in section 1).

---

## 4. Optional checks for users

| Check | Change | Purpose |
|---|---|---|
| Prior/penalty balance | `PRIOR_TO_PENALTY_RATIO` = 0.5 and 2.0 (Part 2) | Dependence of origin and category shares on the priors |
| Penalty weight | `best_alpha` at both ends of the plateau | Dependence on the penalty |
| Without household priors | `USE_GEO_PRIORS = False` | Contribution of household information |
| Own-product factor | `HH_SAME_HOUSEHOLD` = 1.0 | Effect of preferring a household's own products |
| Tiered cover | `USE_TIERED_COVER = True` | Strict database hierarchy instead of joint optimization |

Keep the outputs of each run apart so that runs are not overwritten: in `config.yaml`, point `data_dir` to a different folder or change the `analysis_out` folder name (e.g., `analysis_out_run2`) before running Part 2 (and Part 3).

---

## 5. References

- Chvátal V (1979) A greedy heuristic for the set-covering problem. *Mathematics of Operations Research* 4:233–235.
- CPDat, version 4.0. https://epa.figshare.com/articles/dataset/The_Chemical_and_Products_Database_CPDat_MySQL_Data_File/5352997?file=53538266 (accessed 2026-01-23).
- Dionisio KL, et al. (2018) The Chemical and Products Database, a resource for exposure-relevant data on chemicals in consumer products. *Scientific Data* 5(1):180125.
- Isaacs KK, et al. (2020) Establishing a system of consumer product use categories to support rapid modeling of human exposure. *J Expo Sci Environ Epidemiol* 30(1):171–182.
- Handa S, et al. (2025) The Chemical and Products Database v4.0, an updated resource supporting chemical exposure evaluations. *Scientific Data* 12:950.
- US EPA SPECIATE database, version 5.4. https://www.epa.gov/air-emissions-modeling/speciate (accessed 2026-03-13).
- Simon H, et al. (2010) The development and uses of EPA's SPECIATE database. *Atmospheric Pollution Research* 1(4):196–206.
- SPECIEUROPE, version 3.0. https://source-apportionment.jrc.ec.europa.eu/Specieurope/index.aspx (accessed 2026-03-16).
- Pernigotti D, Belis CA, Spanò L (2016) SPECIEUROPE: The European data base for PM source profiles. *Atmospheric Pollution Research* 7(2):307–314.
- FooDB, version 1.0. https://foodb.ca (accessed 2026-05-29).
- Scalbert A, et al. (2011) Databases on food phytochemicals and their health-promoting effects. *Journal of Agricultural and Food Chemistry* 59(9):4331–4348.
- Layton DW, Beamer PI (2009) Migration of contaminated soil and airborne particulates to indoor dust. *Environ Sci Technol* 43(21):8199–8205.
- Lucattini L, et al. (2018) A review of semi-volatile organic compounds (SVOCs) in the indoor environment: occurrence in consumer products, indoor air and dust. *Chemosphere* 201:466–482.
- Mitro SD, et al. (2016) Consumer product chemicals in indoor dust: a quantitative meta-analysis of U.S. studies. *Environ Sci Technol* 50(19):10661–10672.
- Weschler CJ, Nazaroff WW (2008) Semivolatile organic compounds in indoor environments. *Atmospheric Environment* 42(40):9018–9040.
- Rebryk A, et al. (2026) Evaluation of peak alignment performance of commercial and open-source tools for GC×GC–MS based non-targeted screening. *Briefings in Bioinformatics* 27(5):bbag458. (PubChem_Retriever).

References of the literature consumer product data: see [input_data.md](input_data.md#references-for-the-source-data).
