"""Demand-driven reorder point (ROP) / safety stock (SS) policy.

Method per article, recomputed on a rolling window (default: monthly, last 365 days):
  * smooth / erratic demand        -> ROP = mu_d * LT + z(p) * sigma_week * sqrt(LT/7)
  * intermittent / lumpy / sporadic -> ROP = empirical p-quantile of historical
                                       lead-time demand (rolling LT-day windows)
  * no demand in the window         -> ROP = 0  (run down / procure to order)
  * no lead time maintained         -> company fallback: usage last 12 months / 4
Peak orders ("searched demand", daily demand above Q3 + 3*IQR) are excluded from
the base demand and procured to order.
p (the service parameter) is set per ABC class and calibrated by simulation.
"""
import numpy as np
from scipy.stats import norm

GRID = np.round(np.r_[np.arange(0.50, 0.95, 0.05), np.arange(0.95, 0.996, 0.005)], 3)
NORMAL_CLASSES = ("Smooth", "Erratic")


def peak_threshold(train, min_days=8):
    """Per-article peak threshold on non-zero daily demand: Q3 + 3*IQR."""
    thr = np.full(train.shape[0], np.inf)
    for i, row in enumerate(train):
        nz = row[row > 0]
        if len(nz) >= min_days:
            q1, q3 = np.percentile(nz, [25, 75])
            thr[i] = q3 + 3 * (q3 - q1)
    return thr


def rop_table(D, t_end, LT, demand_class, window=365, grid=GRID, first=None):
    """ROP for every article and every service level in `grid`, using demand
    of the `window` days before day index t_end (but not before the article's
    first demand, so new articles are not diluted by pre-launch zeros).
    Returns (n, len(grid)) table and daily mean demand."""
    n = D.shape[0]
    L = np.maximum(LT, 1).astype(int)
    if first is None:
        first = np.zeros(n, int)
    z = norm.ppf(grid)
    use_normal = np.isin(demand_class, NORMAL_CLASSES)
    tab = np.zeros((n, len(grid))); mu = np.zeros(n)
    for i in range(n):
        s0 = max(t_end - window, int(first[i]))
        w = D[i, s0:t_end]
        if len(w) < 28 or w.sum() <= 0:
            continue                                     # no demand -> ROP 0
        mu[i] = w.mean()
        if LT[i] <= 0:                                   # company fallback rule
            tab[i] = w.sum() * 365 / len(w) / 4
            continue
        if use_normal[i]:
            wk = w[len(w) % 7:].reshape(-1, 7).sum(axis=1)
            tab[i] = mu[i] * L[i] + z * wk.std() * np.sqrt(L[i] / 7)
        else:
            Lw = min(L[i], len(w) - 1)
            cs = np.r_[0, w.cumsum()]
            lw = (cs[Lw:] - cs[:-Lw]) * L[i] / Lw
            tab[i] = np.quantile(lw, grid)
    return tab.clip(min=0), mu


def rolling_rop(D, start, end, LT, demand_class, p_idx, every=30, window=365, first=None):
    """(n, T) ROP matrix recomputed every `every` days on [start-90, end).
    p_idx: per-article index into GRID."""
    n, T = D.shape
    R = np.zeros((n, T))
    t = max(0, start - 90)
    rows = np.arange(n)
    while t < end:
        tab, _ = rop_table(D, t, LT, demand_class, window, first=first)
        R[:, t:min(t + every, T)] = tab[rows, p_idx][:, None]
        t += every
    return R
