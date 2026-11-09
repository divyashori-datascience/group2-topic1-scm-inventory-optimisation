# Part 2 · Article classification
**Deliverables (case slide 13):** find relevant features for inventory article classification · apply a data science approach to classify the articles · recommend strategies per class and define which classes should be taken on stock.

## Result: four classes (20,890 active articles)
| Class | Articles | Usage value | Stock value | Profile | Strategy | On stock? |
|---|---:|---:|---:|---|---|---|
| **Runners** | 2,031 (10%) | 74% | 79% | ~17 orders/yr, used in the last weeks | Stock · demand-driven reorder point (Part 3) | **Yes** |
| **Repeaters** | 3,530 (17%) | 14% | 14% | ~2 orders/yr, lumpy | Stock only where lead time > customer tolerance | Selective |
| **One-offs** | 7,849 (38%) | 4% | 5% | single order, low value | Procure / produce to order, no safety stock | No |
| **Dormant** | 7,480 (36%) | 8% | 2% | no demand for 14+ months | Phase out, sell off stock | No |

- **De-list 427** stocked articles (175 One-offs/Dormant + 252 without any demand in 36 months)
- **Review 1,052** Runners that have no reorder point today

## Method
1. **Population**: all articles with ≥ 1 sale or production use in the last 36 months (not only today's stock articles).
2. **Candidate features (12)**: usage value, weeks with demand, demand lines, order-size variability (cv²), weekly CV, trend, recency, price, lead time, production share, e-shop, age.
3. **Feature selection**
   - Redundancy filter: Spearman |ρ| > 0.85 → drop weekly CV and demand lines (12 → 10). cv² is protected: its ρ = 0.90 with frequency is an artefact of cv² = 0 for one-time demand (ρ = 0.49 for articles with ≥ 3 demand weeks).
   - Domain screen (10 → 4): price is inside usage value; lead time leaks today's stocking decision; production share, e-shop and age profile the classes; trend is noisy.
   - Set comparison: the final set beats + price and all-10; pure silhouette maximisation was rejected (it keeps the binary e-shop flag and drops usage value).
4. **Algorithm and k**: K-means vs Gaussian mixture vs agglomerative (Ward) for k = 3–5, scored with silhouette, Davies–Bouldin and Calinski–Harabasz. **K-means k = 4**: silhouette 0.34, DB 1.13 (GMM 0.06 / 2.40, Ward 0.27 / 1.33).
5. **Stability**: bootstrap adjusted Rand index 0.98 (min 0.96) over 20 refits.
6. **Benchmark**: classic XYZ on weekly CV puts ~98% of articles into Z, so ABC-XYZ cannot separate this range. Most A-articles are Runners, but Runners also contain cheap, frequent B/C items.
7. **Feature relevance** (random forest predicting the class, permutation importance): recency > cv² > usage value > frequency.

## Run
```bash
cd part2_article_classification/notebooks
jupyter nbconvert --to notebook --execute --inplace 01_article_classification.ipynb
```

## Files
| Path | Content |
|---|---|
| `src/classify.py` | features, redundancy filter, evaluation, algorithm comparison, stability, naming |
| `notebooks/01_article_classification.ipynb` | full pipeline |
| `outputs/article_classes.csv` | **per article:** class, stock decision, strategy, features (hand-off to Part 3) |
| `outputs/class_profiles.csv`, `outputs/algorithm_comparison.csv` | summary tables |
| `outputs/figures/` | correlation, algorithms, class shares, feature relevance |
