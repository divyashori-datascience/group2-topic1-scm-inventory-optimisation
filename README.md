# Inventory Management & Optimisation

**Free 1.27M of tied-up capital while raising availability to 95%** by stocking only the right articles and setting every reorder point from demand.

Case study for *Data-driven Supply Chain Management & Logistics* (HSLU, MSc in Data Science & Artificial Intelligence) · Author: **Divya Shori**

---

## Read the work

| | |
| --- | --- |
| **Final report** | [REPORT.md](REPORT.md) · styled version: [REPORT.html](REPORT.html) · [REPORT.pdf](REPORT.pdf) |
| **Presentation** | [presentation/Inventory_Optimisation_Final_Presentation.pdf](presentation/Inventory_Optimisation_Final_Presentation.pdf) · [speaker notes](presentation/SPEAKER_NOTES.md) |
| **Per-article recommendations** | [Part3_ROP_SafetyStock_Recommendations.xlsx](part3_safety_stock_rop/outputs/Part3_ROP_SafetyStock_Recommendations.xlsx) |

## The case

A Swiss B2B company saw capital tied up in stock rise from **16% of revenue (2019) to 27% (2022)**. The data: 2.69M stock movements over 15 years for 58,764 articles. The question: how to reduce capital lockup without hurting availability.

## Results

| | Today | Recommended |
| --- | --- | --- |
| Average stock, inventory articles | 4.92M (2021) | **3.65M (−26%)** |
| Fill rate, value-weighted | 71% if today's reorder points were followed | **95%** (A-articles 97%) |
| Holding cost saved | – | **≈ 0.25M a year** (20% rate, assumed) |
| Robustness | – | ≥ 85% fill in all 8 stress scenarios |

**Recommended strategy:** clean the range (de-list 427 articles, clear 0.94M idle stock) → stock by class → set reorder points from demand, recalculated monthly, starting with an A-article pilot.

## Approach

| Part | Question | Method | Result |
| --- | --- | --- | --- |
| [1 · Data analysis](part1_data_analysis/) | Where does the capital sit? | data audit, stock rebuilt from movements, capital, recency, demand patterns | stock +39% since 2018; 37% of stock value has no reorder point |
| [2 · Classification](part2_article_classification/) | Which articles belong on stock? | 12 → 4 features, K-means vs Ward vs GMM, bootstrap stability 0.98 | Runners (10% of articles, 74% of usage) on stock; One-offs and Dormant off |
| [3 · Reorder points](part3_safety_stock_rop/) | At what level should they reorder? | pattern-specific reorder points, service levels by ABC, daily simulation, out-of-sample test and stress test | 95% fill at 26% less capital |

Each part has its own README, source code and notebooks.

## Repository structure

```
scm-inventory-optimisation/
├── README.md
├── REPORT.md · REPORT.html · REPORT.pdf    final report
├── report/figures/                         report figures
├── presentation/                           final slides (PDF) and speaker notes
├── shared/prep.py                          loading and cleaning: stock rebuild, demand tables
├── part1_data_analysis/                    src/ · notebooks/ · outputs/
├── part2_article_classification/           src/ · notebooks/ · outputs/article_classes.csv
└── part3_safety_stock_rop/                 src/ (simulator, policy, export) · notebooks/ · outputs/
```

## Reproduce

1. Place the raw file `anonymized_202602.csv` (632 MB, not in the repository) next to the repository folder, or set `export SCM_DATA=/path/to/anonymized_202602.csv`.
2. Install Python ≥ 3.10 and the packages:
   ```bash
   pip install pandas numpy scipy scikit-learn matplotlib openpyxl pyarrow jupyter
   ```
3. Run the notebooks in order: Part 1 → Part 2 → Part 3.

## Notes on the data

Quantities are anonymised by a constant factor (×1.1107) and values are in the dataset's currency units, so ratios and percentages are unaffected. Master data (lead time, MOQ, price, reorder point) is a 2022 snapshot. See section 8 of the report for all limitations.
