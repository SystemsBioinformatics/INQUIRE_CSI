# Input data: files, formats and mandatory columns

All Part 1 input files go into `data/preprocessing_in/` and the optional household priors into `data/analysis_in/` (folder names and location of `data/` are set in `config.yaml`; `preprocessing_in/` must exist before Part 1 is run). The source database files (section 2) go into the fixed subfolder `preprocessing_in/source_databases/`, which must also exist. Paths in this document are relative to these two folders. The three output folders are named `preprocessing_out`, `analysis_out` and `visualization_out`. File names are set in the data-loading cells of each notebook. If your files have other names, change them there (search for `safe_read_csv(`, `safe_read_excel(`, and `check_cols_before_load(`).

Each notebook first checks the **header row** of every input file for the mandatory columns (cell *Check if necessary columns exist…*). It stops with a clear error message if a column is missing. Column names are case-sensitive. Leading/trailing spaces in column names and in key text columns are removed automatically (Part 1, *Whitespace cleanup*). InChIKeys of all source databases and of the sample data are also cleaned automatically: converted to upper case, placeholders and numbers set to missing, and a digit "0" replaced by the letter "O" (Part 1, *InChIKey cleanup*).

**Terms used**
- **InChIKey** – a 27-character standard identifier of a chemical structure (e.g., `ZPUCINDJVBIVPJ-LJISPDSOSA-N`). Compounds are matched between samples and sources **only by InChIKey**; compound names are used for display only.
- **Source** – one product, food item or emission profile in a source database, described by its set of compounds.
- **Origin** – the database a source comes from (`HOUSEHOLD_PRODUCTS`, `LIT_CONSUMER_PRODUCTS`, `CPDAT`, `FOODB`, `SPECIATE`, `SPECIEUROPE`).
- **Kind / general category** – the two classification levels of a source used for the priors (for CPDat: product use category (PUC) kind and PUC general category; see below for the other databases).
- **Source class / source class domain** – two harmonized *reporting* levels across all origins (`source_class` = "Domain | Type", `source_class_domain` = "Domain"), assigned from a mapping file (section 3). They are used for tables and figures only, not for the priors or the optimization.

| File | Read by | Required? |
|---|---|---|
| `Sample_Data.xlsx` | Part 1 | yes |
| `Own_Household_Products.csv`, `Own_Household_Products_Metadata.csv` | Part 1 | yes |
| `Literature_Products.csv` | Part 1 | yes |
| `CPDat/product_compositions.tsv`, `CPDat/products.tsv`, `CPDat/product_use_categories.tsv` | Part 1 | yes |
| `FooDB.csv` | Part 1 | yes |
| `SPECIATE.xlsx` | Part 1 | yes |
| `SPECIEUROPE.xlsx` | Part 1 | yes |
| `lookups/source_class_mapping.xlsx` | Part 1 | yes |
| `analysis_in/geo_metadata_outputs/household_metadata_priors.csv` | Part 2 | only if `USE_GEO_PRIORS = True` |

For testing, `example_data/` contains a complete synthetic set of all input files (sample data, household priors, small example versions of all six source databases with 60 sources each, and an example mapping file) in the same folder structure as the input folders (`example_data/preprocessing_in/`, `example_data/analysis_in/`; copy both into `data/`) ([example_data/README.md](../example_data/README.md)).

---

## 1. Sample data (Part 1)

| | |
|---|---|
| File | `Sample_Data.xlsx` |
| Format | Excel, first sheet; one row per detected feature (compound), one column per sample |
| Mandatory columns | `inchikey`, `Feature Name`, `Class`, `Concentration Type` |
| Sample columns | **All columns to the right of `Concentration Type`** are treated as samples. A value **> 0** means "compound detected in this sample"; empty/0 = not detected. Concentrations are not used, only presence/absence. |
| Sample IDs (column names) | `LLNN` with an optional suffix: `LL` = 2-letter sample code, `NN` = 2-digit sample number, e.g., `FR01`, `FR01_LS2`. `LLNN` (the ID without suffix) is the **sample key**: it matches the sample to its household priors (`household_id`) and to the own analyzed products with the same key (`LLNN_CPnn`); several samples from the same household or site share the key and differ only in the suffix. `LL` is used as the **sample group** in Part 3 and for the own-product factor in Part 2 (same `LL` = same group); in the INQUIRE data, `LL` is the country code. IDs in another format are used unchanged as key (they still match a `household_id` written in exactly the same way, but not own products); otherwise, adjust the function `household_key()` in Part 2. |
| Blank/QC columns | Blanks and QC samples are listed in `dust_cols_drop` in Part 1 (default examples: `7S_CS_01`, `Blank_NIST`, `FR_Field_Blank_01`, etc.) and removed when `DROP_QC_COLUMNS = True`. Replace the list with your own blank/QC column names if any. |
| Rows without InChIKey | Removed/dropped (they cannot be matched to sources). |
| Example | `example_data/preprocessing_in/Sample_Data.xlsx` (synthetic sample dataset) |

---

## 2. Source databases (Part 1)

The six source data sets are combined into one master contaminant source database (MCSDB). Each data set gets an ID suffix so that IDs from different databases can never collide.

**Presence/absence only.** The MCSDB records only *which* compounds occur in a source, not how much (no concentrations or weight fractions). The intermediate, cleaned versions of the public databases contain quantitative information where the original database provides it (section 2.7), but they are not redistributed here because of license terms (e.g., non-commercial use, redistribution needs permission). Users can rebuild the databases from the official releases with the cleanup pipelines listed in section 2.7, including concentrations/weight fractions (when available) for, e.g., clustering or multivariate analysis.

**Example files.** `example_data/preprocessing_in/` contains small versions of all six source databases (60 sources each; mostly synthetic, plus a few real rows) in exactly the formats described below, with the same file names and subfolders (inside `preprocessing_in/source_databases/`). Use them to test the pipeline or as templates for adding your own sources ([example_data/README.md](../example_data/README.md)).

### 2.1 Own analyzed household products – origin `HOUSEHOLD_PRODUCTS`

| | |
|---|---|
| Files | `source_databases/Own_Household_Products.csv` (compounds per product); `Own_Household_Products_Metadata.csv` (product metadata) |
| Format | CSV, comma-separated, UTF-8 |
| Mandatory columns – products file | `MySysID`, `Brand-free Name`, `Feature_Name`, `InChIKey`; `source_kind`, `source_general_category`, `puc_harmonized` (used for priors; set to "Unknown" if absent); `Group3` (kept as source type) |
| Mandatory columns – metadata file | `MySysID`, `Group1`, `Group2`, `Group3` (the file is ID-suffixed and saved; not used further) |
| ID format | `MySysID` must be **`LLNN_CPnn`**, e.g., `FR01_CP04` (sample key FR01, consumer product 04). Part 1 adds `_HHP` → `FR01_CP04_HHP`. Part 2 reads the sample key from this ID (`FR01_CP04_HHP` → `FR01`) to prefer the products collected with that sample (household). IDs in another format get the factor for "another group" (`HH_OTHER_COUNTRY`). |
| Content | Compounds measured in products collected in INQUIRE households, e.g., plastic toys, personal care products, textile products, and analyzed using LC-MS-based non-target screening |

### 2.2 Consumer products from the literature – origin `LIT_CONSUMER_PRODUCTS`

| | |
|---|---|
| File | `source_databases/Literature_Products.csv` |
| Format | CSV, comma-separated |
| Mandatory columns | `MySysID` (→ ID, suffix `_COP`), `Brand-free Name` (→ name), `Feature_Name`, `InChIKey`, `puc_harmonized`, `Sample Concentration` (checked); `Group1` (→ kind), `Group2` (→ general category), `Group3` (→ type) |
| Content | Compounds measured in consumer products, compiled from these publications: Park et al. (2024); Yun et al. (2023); Phillips et al. (2018); Lowe et al. (2021); Stanfield et al. (2025); Sørensen et al. (2023); Wu et al. (2023) (full references below). |

### 2.3 CPDat (US EPA Chemicals and Products Database) – origin `CPDAT`

| | |
|---|---|
| Files | Folder `source_databases/CPDat/` with `product_compositions.tsv`, `products.tsv`, `product_use_categories.tsv` |
| Format | Tab-separated text |
| Mandatory columns | `product_compositions.tsv`: `cpdat_product_id`, `inchikey` · `products.tsv`: `cpdat_product_id`, `product_title` · `product_use_categories.tsv`: `cpdat_product_id`, `puc_kind`, `puc_general_category`, `puc_harmonized` |
| Mapping | ID + suffix `_CPD`; `product_title` → name; PUC kind → kind; PUC general category → general category. If a product has several PUCs, the first one (after sorting by ID) is used. |
| Source / version | CPDat v4.0, https://www.epa.gov/chemical-research/chemical-and-products-database-cpdat (MySQL data file: https://epa.figshare.com/articles/dataset/The_Chemical_and_Products_Database_CPDat_MySQL_Data_File/5352997) [downloaded on 2026-01-23]. Prepared with https://github.com/r3bryk/cpdat_v4.0_cleanup. |
| Terms | US EPA data are in the public domain unless otherwise specified. Cite Dionisio et al. (2018) and Handa et al. (2025). |
| Note | CPDat lists **manufacturer-declared ingredients**, not measurements. |

### 2.4 FooDB – origin `FOODB`

| | |
|---|---|
| File | `source_databases/FooDB.csv` |
| Format | **Tab-separated** despite the `.csv` extension |
| Mandatory columns | The column check expects the full header of the merged file (40 columns, in this order): `cont_id, food_name_cont, orig_food_id, orig_food_scientific_name, orig_food_part, orig_source_id, orig_feature_name_cont, orig_content, orig_min, orig_max, orig_unit, food_id, food_sub_id, food_name_food, orig_food_common_name, food_name_scientific, description, itis_id, legacy_id, food_group, food_subgroup, food_type, food_group_harmonized, ncbi_taxonomy_id, public_food_id, cpd_id, public_cpd_id, inchikey, orig_feature_name_cpd, feature_name_pubchem, iupac_name, iupac_name_pubchem, cpd_description, cas, smiles, inchi, mono_mass, superclass, class_classyfire, subclass` |
| Columns actually used | `food_sub_id` (→ ID, suffix `_FDB`), `orig_food_common_name` (→ name), `orig_feature_name_cpd`, `inchikey`, `food_group` (→ kind), `food_subgroup` (→ general category), `food_type`, `food_group_harmonized`, `orig_content` |
| Processing in Part 1 | If a food contains the same InChIKey several times (e.g., "Niacin" and "Niacin, from tryptophan"), only the entry with the highest `orig_content` is kept. |
| Source / version | FooDB v1.0, https://foodb.ca [downloaded on 2026-05-29]. Prepared with https://github.com/r3bryk/foodb_v1.0_cleanup. |
| Terms | Freely available; commercial use or redistribution requires explicit permission of the FooDB authors. Cite FooDB (https://foodb.ca) and Scalbert et al. (2011). Data derived from FooDB are therefore shared under CC BY-NC 4.0. |

### 2.5 SPECIATE – origin `SPECIATE`

| | |
|---|---|
| File | `source_databases/SPECIATE.xlsx` (first sheet) |
| Mandatory columns | `PROFILE_CODE` (→ ID, suffix `_SUS`), `PROFILE_NAME` (→ name), `Feature name`, `InChIKey`, `CATEGORY_LEVEL_1_Generation_Mechanism` (→ kind), `CATEGORY_LEVEL_2_Sector_Equipment` (→ general category), `CATEGORY_LEVEL_3_Fuel_Product` (→ type) |
| Processing in Part 1 | Profiles named "Overall Average" are removed (non-specific aggregates). |
| Source / version | US EPA SPECIATE v5.4, https://www.epa.gov/air-emissions-modeling/speciate [downloaded on 2026-03-13]. Prepared with https://github.com/r3bryk/speciate_v5.4_cleanup. |
| Terms | US EPA data are in the public domain unless otherwise specified. Cite the version used and Simon et al. (2010). |

### 2.6 SPECIEUROPE – origin `SPECIEUROPE`

| | |
|---|---|
| File | `source_databases/SPECIEUROPE.xlsx` (first sheet) |
| Mandatory columns | `PROFILE_CODE` (integer; → ID, suffix `_SEU`), `PROFILE_NAME`, `Feature name`, `InChIKey` (checked); `CATEGORY_LEVEL_1_Generation_Mechanism`, `CATEGORY_LEVEL_2_Sector_Equipment`, `CATEGORY_LEVEL_3_Fuel_Product` (used for kind and category; the same category vocabulary and prior tables as SPECIATE are used) |
| Source / version | European Commission JRC SPECIEUROPE v3.0, https://source-apportionment.jrc.ec.europa.eu/Specieurope/index.aspx  [downloaded on 2026-03-16]. Prepared with https://github.com/r3bryk/specieurope_v3.0_cleanup. |
| Terms | The data may be used provided the source is mentioned. Cite Pernigotti et al. (2016). |

### 2.7 How the source database inputs were prepared

The four public databases were downloaded in their official releases and cleaned, preprocessed, and harmonized with separate, published pipelines before they entered Part 1:

| Database | Version | Cleanup pipeline |
|---|---|---|
| CPDat | v4.0 | https://github.com/r3bryk/cpdat_v4.0_cleanup |
| FooDB | v1.0 | https://github.com/r3bryk/foodb_v1.0_cleanup |
| SPECIATE | v5.4 | https://github.com/r3bryk/speciate_v5.4_cleanup |
| SPECIEUROPE | v3.0 | https://github.com/r3bryk/specieurope_v3.0_cleanup |

**Compound identifiers.** InChIKeys of the compounds of all databases and literature publications were retrieved from PubChem with PubChem_Retriever (https://github.com/r3bryk/PubChem_Retriever), first described in Rebryk et al. (2026). Then, manual review and gap filling were done. This step is essential: all harmonization and all matching between samples and sources in INQUIRE_CSI use InChIKeys only.

**To rebuild the intermediate databases (e.g., with concentrations or weight fractions):**
1. Download the official release of each database (links in sections 2.3–2.6) and (if needed) convert them to appropriate formats used by the cleanup pipelines.
2. Retrieve InChIKeys with PubChem_Retriever, if the cleanup pipeline does not already do so.
3. Run the matching cleanup pipeline (table above), following its own README.
4. The resulting files have the formats that can be used by Part 1.

### 2.8 Optional columns for the all-compounds lookup

Part 1 also builds a lookup table of all compounds with their names, CAS numbers and DTXSIDs (`all_compounds_standardized.csv`; see [01_preprocessing.md](01_preprocessing.md), step 11). It uses the columns below if they exist. They are **optional**: a missing column is logged and skipped, and the identification is not affected. Column names can be changed in `COMPOUND_COLS`.

| Database (file) | Main name | Other names | CAS | DTXSID |
|---|---|---|---|---|
| Own household products (`Own_Household_Products.csv`) | `Feature_Name` | `Raw_Name`, `PubChem_Name` | `Raw_CAS` | `DTXSID` |
| Literature products (`Literature_Products.csv`) | `Feature_Name` | `Raw_Name`, `PubChem_Name` | `Raw_CAS` | `DTXSID` |
| CPDat (`product_compositions.tsv`) | `curated_chemical_name` | – | – | – |
| FooDB (`FooDB.csv`) | `orig_feature_name_cpd` | `feature_name_pubchem`, `iupac_name_pubchem` | `cas` | – |
| SPECIATE (`SPECIATE.xlsx`) | `Feature name` | `Name_Original` | `CAS#` | `DSSTox_ID` |
| SPECIEUROPE (`SPECIEUROPE.xlsx`) | `Feature name` | `Name_Original` | `CAS#` | – |

### Harmonized source schema (created by Part 1)

| Column | Meaning |
|---|---|
| `source_id` | Unique ID with database suffix (`_HHP`, `_COP`, `_CPD`, `_FDB`, `_SUS`, `_SEU`) |
| `source_name` | Human-readable name |
| `inchikey` | One compound of the source (one row per source × compound) |
| `source_origin` | Database (see above) |
| `source_kind` | Higher classification level (used for priors) |
| `source_general_category` | Lower classification level (used for priors and household-prior links) |
| `source_harmonized` | Full harmonized label (CPDat PUC style; for SPECIATE/SPECIEUROPE "level 1 \| level 2 \| level 3") |
| `source_class` | Reporting class "Domain \| Type" (from the mapping file, section 3) |
| `source_class_domain` | Reporting domain (first part of `source_class`) |

All columns of all output files are explained in the [codebook](codebook.md).

---

## 3. Source class mapping (Part 1)

| | |
|---|---|
| File | `lookups/source_class_mapping.xlsx` (inside `preprocessing_in/`), sheet `source_class_mapping` – keep it as the **first** sheet, because the column check reads the first sheet |
| Format | Excel; one row per combination of `source_origin` × `source_kind` × `source_general_category` × `source_harmonized` |
| Mandatory columns | `source_origin`, `source_kind`, `source_general_category`, `source_harmonized`, `source_class`, `source_class_domain` |
| Use | Part 1 adds `source_class` and `source_class_domain` to every source. Missing key values are treated as "Unknown" on both sides, so they match. A key that appears twice with different classes stops the notebook. |
| Unmapped sources | Sources whose key is not in the file get `source_class` = "Unmapped Sources \| <origin>" and `source_class_domain` = "Unmapped Sources". Their keys are written to `preprocessing_out/lookups/source_class_unmapped.csv` (and `source_class_unmapped_std_dbs.csv` for the separate standardized databases). Add these rows to the mapping file and re-run Part 1. |
| Where to get it | `example_data/preprocessing_in/lookups/source_class_mapping.xlsx` |

---

## 4. Household priors (optional Part 2 input)

| | |
|---|---|
| File | `analysis_in/geo_metadata_outputs/household_metadata_priors.csv` (inside `data/`) |
| Format | CSV, comma-separated |
| Columns | `household_id` (`LLNN`) + one `<module>_likelihood` column per module (29 in the INQUIRE data), values 0–1 (0.5 = average/no information) |
| Used when | `USE_GEO_PRIORS = True` in Part 2. With `False`, the file is not needed. |
| Example | `example_data/analysis_in/geo_metadata_outputs/household_metadata_priors.csv` (synthetic) |

The meaning of the modules, how they were built from the INQUIRE household data, and how to create your own file are described in [household_priors.md](household_priors.md).

---

## References for the source data

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
- Rebryk A, et al. (2026) Evaluation of peak alignment performance of commercial and open-source tools for GC×GC–MS based non-targeted screening. *Briefings in Bioinformatics* 27(5):bbag458. (PubChem_Retriever).

Literature consumer products:

- Park et al. (2024) Suspect and non-target screening of chemicals in household cleaning products, and their toxicity assessment. *Environmental Engineering Research* 29(1):230123.
- Yun et al. (2023) Non-target screening of volatile organic compounds in spray-type consumer products and their potential health risks. *Ecotoxicology and Environmental Safety* 268:115695.
- Phillips et al. (2018) Suspect Screening Analysis of Chemicals in Consumer Products. *Environmental Science & Technology* 52:3125–3135.
- Lowe et al. (2021) Chemical Characterization of Recycled Consumer Products Using Suspect Screening Analysis. *Environmental Science & Technology* 55:11375–11387.
- Stanfield et al. (2025) "Developing Chemical Signatures for Categories of Household Consumer Products Using Suspect Screening Analysis". *Environmental Science & Technology* 59:1354–1366.
- Sørensen et al. (2023) Organic chemicals associated with rubber are more toxic to marine algae and bacteria than those of thermoplastics. *Journal of Hazardous Materials* 458:1318107.
- Wu et al. (2023) Chemometrics-based Discrimination of Virgin and Recycled Acrylonitrile-Butadiene-Styrene Plastics Toys via Non-targeted Screening of Volatile Substances. *Journal of Chromatography A* 1711:464442.
