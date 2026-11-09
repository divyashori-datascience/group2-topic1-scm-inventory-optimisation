"""Part 2 · Article classification: features, selection, clustering, evaluation, profiling."""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (silhouette_score, davies_bouldin_score,
                             calinski_harabasz_score, adjusted_rand_score)

FINAL_FEATURES = ["log_usage_value", "weeks_with_demand", "cv2_size", "recency_days"]
CLASS_ORDER = ["Runners", "Repeaters", "One-offs", "Dormant"]
STRATEGY = {
    "Runners": "Stock · demand-driven reorder point (Part 3), high service",
    "Repeaters": "Stock selectively (only where lead time > customer tolerance), else to order",
    "One-offs": "Procure / produce to order · no safety stock",
    "Dormant": "Phase out · run down or sell remaining stock",
}


def article_features(tx, art, start, end, n_weeks=157):
    """Per-article features from demand (sales + production use) in (start, end]."""
    d = tx[tx.is_demand & (tx.date > start) & (tx.date <= end)]
    active = d[d.demand > 0].article_nr.unique()
    d = d[d.article_nr.isin(active)].copy()
    d["wk"] = ((d.date - start).dt.days - 1) // 7
    wk = (d.groupby(["article_nr", "wk"]).demand.sum().clip(lower=0)
            .unstack(fill_value=0).reindex(columns=range(n_weeks), fill_value=0))
    years = (end - start).days / 365.25
    F = pd.DataFrame(index=wk.index)
    price = art.last_direct_cost.reindex(F.index)
    F["annual_usage_value"] = wk.sum(1) / years * price
    F["weeks_with_demand_share"] = (wk > 0).mean(1)
    F["n_demand_lines"] = d[d.demand > 0].groupby("article_nr").size() / years
    sz = wk.where(wk > 0)
    F["cv2_size"] = ((sz.std(1) / sz.mean(1)) ** 2).fillna(0)
    F["cv_weekly"] = (wk.std(1) / wk.mean(1).replace(0, np.nan)).fillna(0)
    F["trend"] = np.log1p(wk.iloc[:, -52:].sum(1)) - np.log1p(wk.iloc[:, -104:-52].sum(1))
    F["days_since_last_demand"] = (end - d[d.demand > 0].groupby("article_nr").date.max()).dt.days
    F["price"] = price
    F["lead_time"] = art.lead_time.reindex(F.index)
    prod = d[d.entry_type == 5].groupby("article_nr").demand.sum().clip(lower=0)
    tot = d.groupby("article_nr").demand.sum().clip(lower=0)
    F["production_share"] = (prod.reindex(F.index).fillna(0) / tot.replace(0, np.nan)).fillna(0).clip(0, 1)
    F["eshop"] = art.eshop.reindex(F.index).astype(int)
    F["age_years"] = (end - tx.groupby("article_nr").date.min().reindex(F.index)).dt.days / 365
    F["stocked_now"] = (art.safety_stock.reindex(F.index) > 0).astype(int)
    return F


def model_matrix(F):
    """Candidate features, transformed for distance-based clustering."""
    return pd.DataFrame({
        "log_usage_value": np.log1p(F.annual_usage_value),
        "weeks_with_demand": np.log1p(F.weeks_with_demand_share * 157),
        "cv2_size": np.log1p(F.cv2_size),
        "recency_days": F.days_since_last_demand,
        "log_demand_lines": np.log1p(F.n_demand_lines),
        "cv_weekly": F.cv_weekly,
        "trend": F.trend.clip(-3, 3),
        "log_price": np.log1p(F.price),
        "lead_time": F.lead_time,
        "production_share": F.production_share,
        "eshop": F.eshop,
        "age_years": F.age_years,
    }, index=F.index)


def redundancy_filter(X, threshold=0.85, protected=("weeks_with_demand", "cv2_size")):
    """Drop the later feature of every pair with |Spearman rho| > threshold.
    `protected` features are kept on domain grounds (cv2_size: its correlation with
    frequency is an artefact of one-time demand, where cv2 = 0 by definition)."""
    C = X.corr(method="spearman").abs()
    drop = set()
    cols = list(X.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            if a not in drop and b not in drop and C.loc[a, b] > threshold:
                if a in protected and b in protected:
                    continue
                drop.add(a if b in protected else b)
    return [c for c in cols if c not in drop], sorted(drop), C


def evaluate(Z, labels, sample=6000, seed=0):
    s = np.random.RandomState(seed).choice(len(Z), min(sample, len(Z)), replace=False)
    return dict(silhouette=silhouette_score(Z[s], labels[s]),
                davies_bouldin=davies_bouldin_score(Z, labels),
                calinski_harabasz=calinski_harabasz_score(Z, labels),
                min_cluster_share=np.bincount(labels).min() / len(labels))


def compare_algorithms(Z, ks=(3, 4, 5), agglo_n=8000, seed=0):
    rng = np.random.RandomState(seed)
    sub = rng.choice(len(Z), min(agglo_n, len(Z)), replace=False)
    rows = []
    for k in ks:
        fits = {"K-means": (KMeans(k, n_init=10, random_state=seed).fit(Z).labels_, Z),
                "Gaussian mixture": (GaussianMixture(k, random_state=seed, n_init=3).fit(Z).predict(Z), Z),
                "Agglomerative (Ward, 8k sample)": (AgglomerativeClustering(k, linkage="ward").fit(Z[sub]).labels_, Z[sub])}
        for name, (lab, ZZ) in fits.items():
            rows.append(dict(algorithm=name, k=k, **evaluate(ZZ, lab)))
    return pd.DataFrame(rows)


def bootstrap_stability(Z, k=4, n_boot=20, seed=0):
    """Adjusted Rand index between the full-data K-means and models refit on bootstrap samples."""
    base = KMeans(k, n_init=10, random_state=seed).fit(Z)
    aris = []
    for b in range(n_boot):
        idx = np.random.RandomState(100 + b).choice(len(Z), len(Z), replace=True)
        aris.append(adjusted_rand_score(base.labels_, KMeans(k, n_init=5, random_state=b).fit(Z[idx]).predict(Z)))
    return np.array(aris)


def name_clusters(F, labels):
    """Map K-means ids to business names by their profile (frequency, recency)."""
    prof = F.assign(c=labels).groupby("c").agg(freq=("n_demand_lines", "median"),
                                                rec=("days_since_last_demand", "median"))
    runners = prof.freq.idxmax()
    dormant = prof.drop(runners).rec.idxmax()
    rest = prof.drop([runners, dormant])
    repeaters = rest.freq.idxmax()
    oneoffs = rest.drop(repeaters).index[0]
    return {runners: "Runners", repeaters: "Repeaters", oneoffs: "One-offs", dormant: "Dormant"}


def fit_final(X, k=4, seed=0):
    Z = StandardScaler().fit_transform(X[FINAL_FEATURES])
    km = KMeans(k, n_init=10, random_state=seed).fit(Z)
    return Z, km
