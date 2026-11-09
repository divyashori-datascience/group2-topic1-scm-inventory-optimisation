# Part 3 · Demand-driven reorder points & safety stock
Author: Divya Shori

**Deliverables (case slide 13)**
1. Find relevant features for defining reorder point / safety stock levels → `02_solution.ipynb` §6
2. Apply a data science approach to optimise the levels → §1–5
3. Give a recommendation for each article → `outputs/Part3_ROP_SafetyStock_Recommendations.xlsx`

## Headline results (test year 2021, out-of-sample)
| | Avg stock value | Fill rate | Fill A-articles |
|---|---:|---:|---:|
| Actual 2021 (observed stock) | 4.92M | – | – |
| Current ROPs, followed strictly (simulated) | 2.79M | 71% | 68% |
| Rule: usage 12m ÷ 4 (simulated) | 3.08M | 83% | 83% |
| Slide-11 formula (simulated) | 2.43M | 85% | 86% |
| **Demand-driven, monthly update (recommended)** | **3.65M** | **95%** | **97%** |

- **−1.27M capital (−26%) vs actual 2021**, about 0.25M p.a. holding cost at 20% (0.19–0.32M at 15–25%)
- At the **same service as today's ROPs, 34% less capital**; vs the ÷4 rule, 23% less
- Actions: 794 reduce ROP · 459 increase · 321 set to 0 (no demand) · 146 keep · 31 fallback (no lead time)

Values are in the dataset's currency units at current purchase price.

## Method
1. **Demand** = net sales (type 1) + usage for production (type 5), daily, per article.
2. **Searched-demand peaks** (daily demand > Q3 + 3·IQR, ~5% of demand days, ~29% of volume) are procured to order. The ROP covers base demand.
3. **Policy, recomputed monthly on the last 365 days** (from first demand for new articles):
   - smooth / erratic → `ROP = μ·LT + z(p)·σ_week·√(LT/7)`
   - intermittent / lumpy / sporadic → `ROP = p-quantile of historical lead-time demand`
   - no demand → `ROP = 0` · no lead time → company fallback `usage 12m / 4`
   - `safety stock = ROP − μ·LT`
   - baseline from the case (slide 11), simulated for comparison: `SS = σ(demand)`, `ROP = Quantity/360 · LT + SS`
4. **Service parameter p per ABC class, calibrated by simulation** on 2020 (smallest p reaching A 98% / B 95% / C 90% fill).
5. **Backtest** on 2021 with a daily (s, Q) simulator: master-data lead time, today's typical order size, back-orders. All policies are compared on the same simulator.
6. **Feature relevance**: simulation-optimal ROP per article (days of demand) is explained with a random forest (CV R² 0.61), permutation importance, mutual information and Spearman ρ. Drivers: order size in days of demand ≫ demand variability > lead time > trend / article age > value.

## Stress tests
| Scenario | Fill rate |
|---|---:|
| Base case | 95% |
| Actual lead time +50% | 87% → maintain measured lead times |
| Peaks served from stock instead of to order | 85% → plan searched demand via orders |

## Data findings that shaped the method (01_eda)
- `inventory_level` is the stock **before** each transaction; ~160 corrupted rows (one at 1.1bn units) → stock rebuilt from cumulative movements.
- Master data is a 2022 snapshot. All quantities incl. safety stock and MOQ are scaled by ≈1.1107 (anonymisation), so ratios are valid.
- Inventory articles are 3% of articles but hold 62% of stock value (+39% 2018→2021).
- Current ROP median = 3.8× lead-time demand, not linked to demand; only 14% follow the ÷4 rule.
- 385 articles stocked out in 2021 while 16–24% of value was excess cover.

## How to run
```bash
cd part3_safety_stock_rop/notebooks
jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb       # writes outputs/eda_article_features.parquet
jupyter nbconvert --to notebook --execute --inplace 02_solution.ipynb  # writes the Excel + figures
```
Data path: see the root README (`SCM_DATA`).

## Files
| Path | Content |
|---|---|
| `src/prep.py` | load & clean transactions, stock rebuild, demand tables, demand-pattern classes |
| `src/sim.py` | vectorised daily (s, Q) inventory simulator + ROP optimiser (bisection) |
| `src/policy.py` | demand-driven ROP/SS policy, peak threshold |
| `src/report.py` | Excel export |
| `notebooks/01_eda.ipynb` | EDA for Part 3 |
| `notebooks/02_solution.ipynb` | optimisation, backtest, feature relevance, recommendations, business case |
| `outputs/Part3_ROP_SafetyStock_Recommendations.xlsx` | Summary · per-article recommendations · policy comparison · trade-off curve · feature relevance · method |
| `outputs/figures/` | charts for the report/presentation |

## Limitations
- No order dates → lead-time variability is not measurable (covered by the stress test).
- Recorded actual service (~99.6%) is likely censored (usage is only booked when stock exists), so service is compared inside the simulation.
- Order quantities are kept as today, so the effect isolated here is the ROP / safety stock.
- Holding cost rate (20%) is an assumption.
- Hand-off from Part 2: the ABC class can be swapped for Part 2's clusters as the service-level segment.
