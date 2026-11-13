# Household priors (optional input of Part 2)

## Purpose

Part 2 can use information about the household in which a sample was collected to make some source categories more or less plausible for that sample. Examples: a household with a wood stove gets a higher prior for residential wood combustion profiles; a home close to a busy road gets a higher prior for traffic profiles. This information is supplied as one table, `household_metadata_priors.csv`, with one row per household and one "likelihood" per **module** (a group of related household characteristics).

The file is optional: with `USE_GEO_PRIORS = False` in Part 2 (cell *Check if necessary columns exist…*), no household information is used and all geo multipliers are 1.0.

## File format

| Column | Format | Meaning |
|---|---|---|
| `household_id` | `LLNN` | Sample key of the household or sampling site (`LL` = 2-letter sample code, `NN` = 2-digit sample number); must match the sample IDs without suffix (e.g., sample `FR01_LS2` → `FR01`) |
| `<module>_likelihood` | 0–1 | Relative likelihood that the household has **more** of the sources linked to this module than the average household in the study. 0.5 = average or no information. |

Location: `data/analysis_in/geo_metadata_outputs/household_metadata_priors.csv` (folder name set in `config.yaml`). A synthetic example is `example_data/analysis_in/geo_metadata_outputs/household_metadata_priors.csv`.

Rules checked by Part 2:
- The `<module>_likelihood` columns should match the module names in `MODULE_WEIGHT` and `MODULE_SOURCE_MAP` (Part 2). Differences are reported as warnings: modules in the file but not in `MODULE_WEIGHT` are ignored, and modules in `MODULE_WEIGHT` but not in the file have no effect.
- Samples whose household is not in the file are analyzed without household priors (multiplier 1.0) and are listed in the log.

## How the likelihoods are used

For a source whose category is linked to modules *m* (via `MODULE_SOURCE_MAP`), the prior is multiplied by

`geo multiplier = exp( Σ_m MODULE_WEIGHT[m] × (likelihood_m − 0.5) )`

A household at the average (0.5) gives multiplier 1. With weight 1.0 and likelihoods between 0.02 and 0.98, one module changes the prior by a factor between ~0.6 and ~1.6.

## How the INQUIRE file was built

The INQUIRE household priors were computed from household data that cannot be published because they contain personal data (GDPR). The processing code is therefore not part of this repository; the method is described here so that it can be reproduced with other data.

**Information used:**
- **Household questionnaire:** dwelling (building year, refurbishment, heating and cooking fuels, fireplace/stove, floor coverings, number and age of occupants, pets), sampled room (floor and wall materials, furniture, electronic devices) and outdoor surroundings.
- **Weekly logsheets:** daily reports during the sampling week (e.g., use of fireplace/stove, air fresheners, candles, insecticides, cleaning methods, window opening, people staying overnight), plus free-text activity notes.
- **Geographic information system (GIS) data around the home:** CORINE Land Cover classes in buffers of 100 m–30 km (urban, industrial, road/rail, port, airport, construction, dump sites, agriculture, forest, marine), crops, industrial facilities, road network (OpenStreetMap), modeled agricultural pesticide use, PFAS-related sites, population, and distance to airports.

**Processing steps:**
1. **Features.** Each household characteristic (feature) is converted to a 0–1 score with one of four transforms:
   - `bin` – yes/no answers (1/0);
   - `frac` – share of logsheet days with an activity (already 0–1);
   - `pos` – numeric variable where higher = more exposure, converted to its rank between 0 (lowest) and 1 (highest);
   - `neg` – the same, but lower = more exposure (e.g., distance to a road).

   Derived features include land-cover shares per buffer, number of industrial facilities, arable crop share, building age, recent refurbishment (within 10 years before sampling), adults per m², numbers of children and electronic devices, and keyword counts in the free-text notes (burning- and renovation-related).
2. **Modules.** Features are grouped into 29 modules. All features of a module point in the **same direction** (higher = more of the linked sources); counteracting items, such as electric cooking or air purifiers, are left out. Every raw variable is used in **at most one** module, to avoid double counting. Each feature has a weight that expresses how directly it indicates the sources (e.g., open fireplace 2.0, pellet stove 0.5).
3. **Module score.** The weighted mean of the **observed** features of a module (missing features are skipped, not set to 0). If less than 40% of the module's feature weight is observed, the module is set to "no information".
4. **Likelihood.** The module scores are converted to mid-rank likelihoods within the study population, `(rank − 0.5) / n`, clipped to [0.02, 0.98]. Households without information get 0.5. Each module therefore has a mean of 0.5. A value of 0.9 means "among the ~10% of households of this study with the strongest evidence for these sources". It is a **relative** value, not an absolute probability. Households with tied scores (e.g., all households that never burn wood) share the same value.
5. **Quality control.** Three checks were run:
   - correlation of each feature with its own module (should not be negative);
   - negative correlations between features of one module (acceptable only for substitutes, e.g., babies vs. children);
   - module pairs with |Spearman ρ| ≥ 0.70. Such pairs were accepted only if they are linked to different source categories in Part 2 (e.g., agriculture vs. agricultural pesticides), or if one of them has weight 0 (smoking vs. vaping).

## Modules, weights and linked source categories

The weights (`MODULE_WEIGHT`) and links (`MODULE_SOURCE_MAP`) are set in Part 2; the table summarizes the defaults.

| Module | Main household information | Weight | Linked source categories (examples) |
|---|---|---|---|
| `wood_burning` | Fireplace, wood/pellet stove, use frequency | 1.0 | SPECIATE/SPECIEUROPE residential wood combustion, biofuel |
| `gas_oil_combustion` | Gas/oil heating and cooking, boilers | 0.8 | SPECIATE/SPECIEUROPE residential combustion |
| `smoking` | Smokers, smoking indoors | 1.0 | SPECIATE cigarette |
| `vaping` | E-cigarette/vape use | 0.0 | none (no e-cigarette/vape source in the database) |
| `fresheners_candles` | Air fresheners, candles, incense | 0.9 | Literature air fresheners/deodorizers; own household air fresheners |
| `pesticides_household` | Indoor insecticide/biocide use | 0.9 | CPDat pesticides; literature mosquito/mite products |
| `cleaning_products` | Cleaning frequency and methods | 0.7 | CPDat household cleaning; literature cleaning products; SPECIATE/SPECIEUROPE consumer products |
| `pets` | Pets | 0.7 | CPDat animal care |
| `children` | Babies and children | 0.6 | CPDat/literature/own children's products; FooDB baby foods |
| `occupancy` | Number of occupants, occupants per m² | 0.3 | Personal care products; cooking; common foods |
| `electronics` | Electronic devices in the sampled room | 0.6 | CPDat electronics, batteries; own household electronics |
| `floor_textile` | Carpets and rugs | 0.6 | Literature/own carpets; CPDat furniture & furnishings |
| `floor_resilient` | Vinyl and other resilient flooring | 0.6 | Literature vinyl flooring; own flooring; CPDat construction materials |
| `wood_surfaces` | Wooden floors and furniture, varnish | 0.4 | SPECIATE wood coatings; literature polish; CPDat home maintenance; own furniture |
| `building_age` | Building year (higher = older) | 0.5 | Literature/own construction materials; SPECIATE architectural coatings |
| `renovation` | Recent refurbishment, DIY/renovation notes | 0.7 | CPDat construction & home maintenance; literature vinyl flooring; SPECIATE architectural coatings, solvents |
| `ventilation` | Window opening | 0.0 | none (not directional) |
| `airport` | Distance to airports, airport land cover | 0.8 | SPECIATE aircraft/airport profiles |
| `traffic` | Roads around the home, road/rail land cover | 1.0 | SPECIATE/SPECIEUROPE on-road mobile and road profiles; CPDat vehicles; literature tire rubber |
| `industry` | Industrial facilities and land cover | 0.8 | SPECIATE industrial, chemical, petrochemical, energy and manufacturing profiles |
| `agriculture` | Agricultural land cover, crops | 0.6 | SPECIATE agriculture; FooDB crop food groups |
| `agri_pesticides` | Modeled agricultural pesticide use | 0.6 | SPECIATE and CPDat pesticides |
| `pfas` | PFAS-related sites | 0.0 | none (no PFAS-specific source category) |
| `urban` | Urban land cover, population | 0.4 | SPECIATE/SPECIEUROPE urban profiles |
| `green` | Forest and green land cover | 0.4 | SPECIEUROPE biogenic and mineral; SPECIATE geological; CPDat landscape & yard |
| `marine` | Marine and port land cover | 0.4 | SPECIEUROPE/SPECIATE marine and port profiles |
| `waste` | Dump sites | 0.4 | SPECIATE landfill, wastewater, composting, incineration |
| `commercial` | Commercial premises nearby | 0.5 | SPECIATE dry cleaning, graphic arts, commercial, cooking |
| `outdoor_burning` | Outdoor burning activities, bonfires | 0.5 | SPECIATE/SPECIEUROPE open burning, wildfire, agricultural burning |

## Creating your own file

1. Collect household information that indicates the presence or intensity of the source groups above.
2. For each module, compute a score per household with the steps above (or any monotonic score where higher = more of the linked sources).
3. Convert each module to mid-rank likelihoods (0.02–0.98, mean 0.5) and save the table with `household_id` and `<module>_likelihood` columns.
4. You can use a subset of modules. Modules not in your file have no effect. New modules must be added to `MODULE_WEIGHT` and `MODULE_SOURCE_MAP` in Part 2.

**NB!** Household-level data are personal data. Do not publish `household_metadata_priors.csv` or its inputs without checking data-protection rules.
