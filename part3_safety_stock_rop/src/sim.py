"""Vectorised daily inventory simulation for a continuous-review (s, Q) policy.

Policy: every day, after demand, if inventory position (on hand - backorders +
on order) <= ROP, order n*Q (smallest n that lifts the position above ROP).
Orders placed at the end of day t are available from day t+LT+1, i.e. they
cover exactly LT days of demand exposure (consistent with ROP = demand over LT).
`rop` may be a vector (static policy) or an (n, T) matrix (recomputed over time). Unmet demand is back-ordered (B2B).
All articles are simulated in parallel (numpy over the article axis).
"""
import numpy as np


def simulate(D, rop, Q, LT, start, end, warmup=90, init=None):
    """D: (n, T) daily demand. Policy vectors rop, Q, LT: (n,).
    Simulates days [start-warmup, end) and reports KPIs on [start, end).
    Returns dict of per-article arrays."""
    n, T = D.shape
    ROP = np.asarray(rop, float); Q = np.maximum(np.asarray(Q, float), 1e-9)
    LT = np.maximum(np.asarray(LT, int), 1)
    t0 = max(0, start - warmup)
    rop0 = ROP if ROP.ndim == 1 else ROP[:, t0]
    net = (rop0 + Q) if init is None else np.asarray(init, float).copy()
    pipe = np.zeros((n, T + LT.max() + 3))
    on_order = np.zeros(n)
    idx = np.arange(n)
    onhand_sum = np.zeros(n); served = np.zeros(n); dem = np.zeros(n)
    so_days = np.zeros(n); orders = np.zeros(n)
    for t in range(t0, end):
        arr = pipe[:, t]; net += arr; on_order -= arr
        d = D[:, t]
        rop = ROP if ROP.ndim == 1 else ROP[:, t]
        s = np.minimum(d, np.maximum(net, 0.0))
        net -= d
        ip = net + on_order
        trig = ip <= rop
        if trig.any():
            k = np.floor((rop[trig] - ip[trig]) / Q[trig]) + 1
            q = k * Q[trig]
            pipe[idx[trig], t + LT[trig] + 1] += q
            on_order[trig] += q
        if t >= start:
            onhand_sum += np.maximum(net, 0.0)
            served += s; dem += d
            so_days += net < -1e-9   # unmet demand / open backorders
            orders += trig
    days = end - start
    fill = np.where(dem > 0, served / np.where(dem > 0, dem, 1), 1.0)
    return {"avg_onhand": onhand_sum / days, "fill_rate": fill,
            "stockout_days": so_days, "orders": orders, "demand": dem}


def optimise_rop(D, Q, LT, target, start, end, hi, iters=18, warmup=60):
    """Smallest ROP per article reaching `target` fill rate on [start, end)
    (bisection; fill rate is monotone in ROP)."""
    lo = np.zeros(len(Q)); hi = np.asarray(hi, float).copy()
    ok_hi = simulate(D, hi, Q, LT, start, end, warmup)["fill_rate"] >= target
    for _ in range(iters):
        mid = (lo + hi) / 2
        ok = simulate(D, mid, Q, LT, start, end, warmup)["fill_rate"] >= target
        hi = np.where(ok, mid, hi); lo = np.where(ok, lo, mid)
    return hi, ok_hi
