# Inventory Management & Optimisation

How a Swiss B2B company can free **1.27M of tied-up capital (−26%)** while keeping **95% of demand served from stock**, by stocking only the right articles and setting every reorder point from demand.

*HSLU · Data-driven Supply Chain Management & Logistics · MSc in Data Science & Artificial Intelligence · Group 2, Topic 1 · Divya Shori*

---

## Start here

| | |
| --- | --- |
| **Report** | [report/REPORT.md](report/REPORT.md) · styled version: [report/REPORT.html](report/REPORT.html) |
| **Presentation** | [PDF](presentation/Inventory_Optimisation_Final_Presentation.pdf) · [PowerPoint with speaker notes](presentation/Inventory_Optimisation_Final_Presentation.pptx) |
| **Recommendation per article** | [Part3_ROP_SafetyStock_Recommendations.xlsx](part3_safety_stock_rop/outputs/Part3_ROP_SafetyStock_Recommendations.xlsx) |

## The problem

Capital tied up in stock rose from **16% of revenue (2019) to 27% (2022)**. We analysed 2.69M stock movements for 58,764 articles (2007–2022) to find out where the capital sits, which articles belong on stock, and at what level they should be reordered.

## Key results

Simulated on 2021, a year the method never saw, for the 1,751 articles stocked today:

| | Today | Recommended |
| --- | --- | --- |
| Average stock | 4.92M | **3.65M (−26%)** |
| Fill rate (value-weighted) | 71% if today's reorder points were followed | **95%** (A-articles 97%) |
| Holding cost saved per year | – | **≈ 0.25M** (at an assumed 20% rate) |
| Under 8 stress scenarios | – | **≥ 85%** fill in every one |

**Recommendation:** clean the range (de-list 427 articles, clear 0.94M of idle stock) → stock by class → set reorder points from demand, recalculated monthly, starting with an A-article pilot.

## How the work is organised

| Part | Question | What we did | Folder |
| --- | --- | --- | --- |
| 1 · Data analysis | Where does the capital sit? | data audit, stock rebuilt from movements, capital and demand analysis | [part1_data_analysis](part1_data_analysis/) |
| 2 · Classification | Which articles belong on stock? | 4 demand features, K-means into Runners, Repeaters, One-offs, Dormant | [part2_article_classification](part2_article_classification/) |
| 3 · Reorder points | At what level should they reorder? | demand-driven reorder points, service levels by ABC, daily simulation and stress test | [part3_safety_stock_rop](part3_safety_stock_rop/) |

Each part folder has its own README with the method, results and how to run it.

## Repository structure

```
├── README.md
├── report/                 final report (Markdown and HTML) and its figures
├── presentation/           final slides (PDF, and PowerPoint with speaker notes)
├── shared/                 data loading and cleaning used by all parts
├── part1_data_analysis/    src/ · notebooks/ · outputs/
├── part2_article_classification/
└── part3_safety_stock_rop/
```

## Run it yourself

1. Put the raw data file `anonymized_202602.csv` (632 MB, not included) in the folder that contains this repository, or set `export SCM_DATA=/path/to/anonymized_202602.csv`.
2. Install Python 3.10 or newer and the packages:
   ```bash
   pip install pandas numpy scipy scikit-learn matplotlib openpyxl pyarrow jupyter
   ```
3. Run the notebooks in order: Part 1 → Part 2 → Part 3.

Quantities in the data are anonymised by a constant factor and values are in the dataset's currency units, so ratios and percentages are unaffected. Master data is a 2022 snapshot; see the report for all limitations.
