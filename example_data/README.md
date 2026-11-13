# Example data (synthetic)

Small synthetic data set for **testing** the INQUIRE_CSI pipeline without downloading the full source databases. Results obtained with these data have **no scientific meaning**.

The folder mirrors the input folders of the working folder `data/` (`preprocessing_in/` and `analysis_in/`), so both can be copied into `data/` as they are (see "How to use").

## Files

### Sample data and household priors

Paths are relative to `example_data/preprocessing_in/`, except the household priors (`example_data/analysis_in/`).

| File | Content |
|---|---|
| `Sample_Data.xlsx` | 500 compounds × 40 synthetic samples plus one blank column (`Blank_NIST`, listed in `dust_cols_drop` of Part 1). The compounds are real compounds detected in household dust in the INQUIRE project (InChIKey, name, class). About half of them (253) have at least one source in the example source databases below, and half have none, so both attributed and unattributed compounds occur, as in real samples. Presence/absence was generated at random from each compound's detection frequency, with random sample and sample-group effects. The concentrations are random numbers > 0 (column `Concentration Type` = "Randomly generated concentrations"). |
| `analysis_in/geo_metadata_outputs/household_metadata_priors.csv` | Random household likelihoods (0.02–0.98, mid-rank) for the 29 modules, for 30 of the 32 synthetic sample keys (`household_id`). Two keys are left out on purpose, to test samples without priors. |

### Example source databases

Each database contains **60 sources** (products, foods or emission profiles) in exactly the file format, and with exactly the columns, that Part 1 reads ([docs/input_data.md](../docs/input_data.md), section 2). CPDat, the literature products and SPECIATE contain one extra test source each (see "Built-in test cases"). In total there are more than 300 sources, because the validation cells of Part 2 draw synthetic mixtures of up to 300 sources.

| File | Origin in the pipeline | Sources | Content |
|---|---|---|---|
| `Own_Household_Products.csv`, `Own_Household_Products_Metadata.csv` | `HOUSEHOLD_PRODUCTS` | 60 | 58 synthetic products, up to 4 per sample key for the keys `LL01` and `LL02` of the sample groups (e.g., `AT01_CP01`–`AT01_CP04`), plus 2 real INQUIRE products (`FR01_CP04`, `FR01_CP05`). The synthetic products contain compounds detected in the samples with the same key, so they test the preference for a sample's own products. |
| `Literature_Products.csv` | `LIT_CONSUMER_PRODUCTS` | 60 (+1 test) | 59 synthetic products in 11 consumer-product categories (cleaning products, air fresheners, personal care, toys, flooring, clothing, rubber mats, mosquito repellent), plus 1 real product (`CL24`, air-conditioner cleaner) |
| `CPDat/product_compositions.tsv`, `CPDat/products.tsv`, `CPDat/product_use_categories.tsv` | `CPDAT` | 60 (+1 test) | 58 synthetic products in 15 product use categories (PUCs), plus 2 real CPDat products (1842, 1843, "Wood Cleaner") |
| `FooDB.csv` (tab-separated) | `FOODB` | 60 | 58 synthetic foods in 16 food groups, plus 2 real FooDB foods (`287_01` Alfalfa, `725_44` Snack bar) |
| `SPECIEUROPE.xlsx` | `SPECIEUROPE` | 60 | 58 synthetic profiles in 10 categories (wood burning, traffic, road and urban dust, residential heating, cooking, biogenic, consumer products), plus 2 real profiles (1 Cement, 302 Biomass burning) |
| `SPECIATE.xlsx` | `SPECIATE` | 60 (+1 test) | 57 synthetic profiles in 12 categories (wood burning, cigarette smoke, cooking, vehicle exhaust, coatings, consumer products, road and soil dust, natural gas, aircraft, refinery), plus 3 real profiles (4663, 4664, 8811) |
| `lookups/source_class_mapping.xlsx` | – | – | Example mapping of all categorizations above to the reporting levels `source_class` ("Domain \| Type") and `source_class_domain` (6 domains). The mapping for the real MCSDB is published on Zenodo together with the databases. |

**Synthetic sources** were built from the compounds of `Sample_Data.xlsx`: each source contains a random set of compounds (typically 3–20) from compound classes that fit the database (e.g., personal-care compounds and plasticizers in consumer products; fatty acids and flavors in foods; PAHs and petroleum hydrocarbons in emission profiles). Source names and categories use the vocabulary of the real databases, so the priors of Part 2 work as with the real data, but the compositions are random. Concentrations and weight fractions are random numbers; CAS numbers and DTXSIDs are only given for the real example rows.

**Real example sources.** The few real sources were copied from the processed databases (CPDat v4.0, FooDB v1.0, SPECIATE v5.4, SPECIEUROPE v3.0, INQUIRE household products, and the literature data of Park et al. 2024). They show what real entries look like. Most of their compounds do not occur in the example samples, so some of them are removed by the masking step of Part 1. The terms of use of the original databases apply to these rows (see the main README).

### Built-in test cases

| Test case | Where | Expected result in Part 1 |
|---|---|---|
| InChIKey with a digit "0" instead of the letter "O" | `Literature_Products.csv`, test product `CL99` | Corrected in the *InChIKey cleanup* cell (log: "'0' → 'O' corrected: 1 keys") |
| Junk InChIKeys ("0", "-") | `Literature_Products.csv`, test product `CL99` | Set to missing and dropped (log: "junk → missing: 1 rows"; "-" is a placeholder and is set to missing without being counted as junk) |
| Two products with identical compounds and PUC | CPDat 900001 and test product 900059 (and the real pair 1842/1843) | Merged in the first aggregation (log: "CPDAT: 61 → 59") |
| The same compound twice in one food | Every synthetic FooDB food (second entry ending in ", free", lower content) | Only the entry with the highest content is kept (log: "Deleted 58 semi-duplicates") |
| Non-specific aggregate profile | SPECIATE test profile 99999 "Overall Average" | Removed when SPECIATE is loaded |
| Blank column | `Blank_NIST` in `Sample_Data.xlsx` | Removed with `DROP_QC_COLUMNS = True` |
| Samples without household priors | 2 of 32 sample keys | Listed in the log of Part 2; analyzed with geo multiplier 1.0 |

## Sample IDs

IDs follow the pattern `LLNN[_suffix]` used by the pipeline (`LL` = 2-letter sample code, `NN` = 2-digit sample number): 8 fictitious sample groups (AT, DE, ES, FR, IE, LT, RO, UA) × 4 sample keys (`01`–`04`); key `01` of every group has two samples (`_LS1`, `_LS2`), e.g., `AT01_LS1`, `AT01_LS2`, `AT02`. The codes are artificial and not linked to real households or to the countries of the INQUIRE study.

## What the example data test

- all three notebooks end to end, without downloading the full databases;
- all six source databases, the source class mapping and the reporting levels in Part 3;
- the InChIKey cleanup, the aggregation of identical sources, the FooDB duplicate removal and the masking in Part 1;
- removal of blank columns (`DROP_QC_COLUMNS = True`);
- household priors (`USE_GEO_PRIORS = True`), including samples without priors;
- the preference for a sample's own analyzed products (household factor), including several samples per key;
- figures with several sample groups.

## How to use

1. Copy the two folders `example_data/preprocessing_in/` and `example_data/analysis_in/` (the README is not needed) into the working folder `data/`. If `data/` already contains the real databases, copy them into a second working folder instead and point `data_dir` in `config.yaml` to it.
2. Run `INQUIRE_CSI_Pt1_Preprocessing`, `INQUIRE_CSI_Pt2_Analysis_and_Validation` and (optionally) `INQUIRE_CSI_Pt3_Visualization` as described in the main README, with `DROP_QC_COLUMNS = True` in Part 1.
3. Part 1 takes a few seconds, Part 2 a few minutes (most of it alpha tuning and validation), Part 3 about a minute.

**NB!** The example source databases are far smaller than the real ones (~360 instead of ~258,000 sources). Alpha tuning, prior calibration and the validation metrics therefore give values that differ from the reference run ([docs/method_and_limitations.md](../docs/method_and_limitations.md)); they only show that the pipeline runs. Expected messages with the example data:
- Part 1: `Dust dataset: DF 'dust_strip' not found → skipped` (harmless; the sample data are cleaned as "Full dust dataset");
- Part 2, *Check the geo mapping*: many labels of `MODULE_SOURCE_MAP` "do not fire" (status NOT FOUND), because the example databases contain only a few source categories;
- Part 2, alpha tuning: the best alpha lies at the lower end of the grid (1000), because the small synthetic sources hardly overlap.

The example data were test-run through Parts 1 and 2 and the heatmap cells of Part 3 when they were created (2026-10-17).

License: CC BY-NC 4.0 (the real example rows keep the terms of their original databases).
