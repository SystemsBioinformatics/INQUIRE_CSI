# Source weights & priors (Pt2)

Read by `notebooks/INQUIRE_CSI_Pt2_Analysis_and_Validation.ipynb` (cells "Define source weights & priors" and
"Geo metadata influence weights"). Values are for **indoor dust**; adjust them for other matrices.
Folder location: `folders.priors` in `config.yaml` (relative to `data_dir`); this folder is tracked in git.

| File | Columns | Notebook object |
|---|---|---|
| `source_weights.csv` | source_origin, weight, rationale | `SOURCE_WEIGHT` |
| `prior_tables.csv` | source_origin, kind_table, category_table, default_kind_prior | `PRIOR_TABLES` |
| `kind_priors.csv` | table, source_kind, prior, group, rationale | `<table>_KIND_PRIOR` |
| `category_priors.csv` | table, source_general_category, prior, group, rationale | `<table>_CATEGORY_PRIOR` |
| `module_weights.csv` | module, weight, group, rationale | `MODULE_WEIGHT` |
| `module_source_map.csv` | module, source_origin, label, group, rationale | `MODULE_SOURCE_MAP` (one row per label; trailing `*` = also all sub-categories) |

`group` holds the section heading of the original notebook; `rationale` the per-value comment.
Tables are shared between origins via `prior_tables.csv` (CONS_PRODS: HOUSEHOLD_PRODUCTS and LIT_CONSUMER_PRODUCTS;
SPECIATE: SPECIATE and SPECIEUROPE). SPECIATE/SPECIEUROPE categories are hierarchical ("A; B; C" → longest listed prefix).
All values are in [0, 1]. Edit with a tool that does not reinterpret text (e.g. "NoID") or re-quote fields.

## Scale
1.0 = well-documented, direct contributor to residential indoor dust; ~0.5 = plausible/indirect; <=0.1 = mainly
industrial/occupational or remote from homes.
Prior per source = `SOURCE_WEIGHT[origin] * sqrt(kind_prior * category_prior)`.

## Evidence for the relative values (dust)
- Mitro et al. 2016, Environ Sci Technol 50(19):10661-10672 (meta-analysis of consumer-product chemicals in house dust)
- Weschler & Nazaroff 2008, Atmos Environ 42(40):9018-9040 (SVOC partitioning from products/materials into dust)
- Lucattini et al. 2018, Chemosphere 201:466-482 (SVOCs in consumer products, indoor air and dust)
- Layton & Beamer 2009, Environ Sci Technol 43(21):8199-8205 (track-in of outdoor soil/road dust)
- Indoor combustion (wood stoves, cooking, tobacco smoke) and indoor pesticide/pet-treatment use are well-known dust sources.

## Databases
- FooDB: https://foodb.ca/
- SPECIEUROPE: https://source-apportionment.jrc.ec.europa.eu/Specieurope/index.aspx
- SPECIATE: https://www.epa.gov/air-emissions-modeling/speciate
- CPDat: https://epa.figshare.com/articles/dataset/The_Chemical_and_Products_Database_CPDat_MySQL_Data_File/5352997?file=53538266

## Literature consumer-product references
Park et al. 2024, Environ Eng Res 29(1):230123; Yun et al. 2023, Ecotoxicol Environ Saf 268:115695;
Phillips et al. 2018, Environ Sci Technol 52:3125-3135; Lowe et al. 2021, Environ Sci Technol 55:11375-11387;
Stanfield et al. 2025, Environ Sci Technol 59:1354-1366; Sørensen et al. 2023, J Haz Mat 458:1318107;
Wu et al. 2023, J Chrom A 1711:464442.
