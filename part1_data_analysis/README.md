# Part 1 · Data analysis
**Deliverable (case slide 13):** general recommendation to optimise inventory management, based on data analysis (stock articles, lead time, …).

## Headline findings
| Finding | Number |
|---|---|
| Stock value in inventory articles (safety stock > 0), 2018 → 2021 | 3.5M → 4.9M (**+39%**) |
| Stock as share of yearly usage (inventory articles), 2019 → 2021 | 29% → 37% |
| Stock value in articles **without** a reorder point | 2.9M (**37%** of 7.9M) |
| Stock in articles idle > 1 year / > 3 years | **0.94M** / 0.42M |
| Inventory articles idle > 1 year, still with a reorder point | 318 (18%) |
| Lead time maintained (inventory articles) | 98%, mostly 15 / 30 days (manual) |
| Inventory articles with irregular demand | ~75% |

## Method
1. **Data-quality audit** (`src/analysis.py · quality_audit`): `inventory_level` is the stock *before* each movement; 160 rows inconsistent with the movement history (max 1.1 bn units) → stock rebuilt as opening level + cumulative movements; all quantities scaled by 1.1107 (anonymisation, ratios valid); master data is a 2022 snapshot.
2. **Capital lockup**: daily end-of-day stock per article × current purchase price (case definition: average stock level × purchase price).
3. **Stock-article health**: time since last sale / production use (replicates case slide 9).
4. **Lead time**: coverage and distribution of master-data lead times.
5. **Demand patterns**: Syntetos–Boylan classes on monthly demand, last 36 months.

## Run
```bash
cd part1_data_analysis/notebooks
jupyter nbconvert --to notebook --execute --inplace 01_data_analysis.ipynb
```
Uses `shared/prep.py` (repo root) for loading and cleaning. Data path: see the root README.

## Files
| Path | Content |
|---|---|
| `src/analysis.py` | quality audit, entry-type table, stock valuation, recency buckets |
| `notebooks/01_data_analysis.ipynb` | full analysis with findings |
| `outputs/figures/` | lockup trend, recency, lead time |
