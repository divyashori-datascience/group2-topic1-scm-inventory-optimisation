"""Part 1 · Data analysis helpers: data-quality audit, stock valuation, recency, lead time."""
import numpy as np
import pandas as pd

SCALE = 1.110749516768691   # anonymisation factor applied to every quantity field
ENTRY_TYPES = {0: "Procurement", 1: "Sale", 2: "In adjustment", 3: "Out adjustment",
               4: "Internal", 5: "Usage for production", 6: "In from production"}


def quality_audit(tx):
    """Checks that shape the whole analysis. Returns a tidy table of findings."""
    g = tx.groupby("article_nr")
    reported_before = tx.inventory_level
    rebuilt_before = tx.inv_after - tx.quantity
    mismatch = ~np.isclose(reported_before, rebuilt_before, rtol=1e-5, atol=1e-2)
    snap = ["safety_stock", "lead_time", "moq", "last_direct_cost", "vendor_nr", "eshop"]
    varying = {c: int((g[c].nunique() > 1).sum()) for c in snap}
    r = tx.quantity / SCALE
    rows = [
        ("Rows / articles", f"{len(tx):,} / {tx.article_nr.nunique():,}"),
        ("Period", f"{tx.date.min():%d.%m.%Y} – {tx.date.max():%d.%m.%Y}"),
        ("Missing values", int(tx.isna().sum().sum())),
        ("inventory_level = stock BEFORE the movement", f"{100 * (~mismatch).mean():.4f}% of rows"),
        ("Rows inconsistent with cumulative movements", int(mismatch.sum())),
        ("Max reported inventory_level", f"{tx.inventory_level.max():,.0f}"),
        ("Quantities = integer × anonymisation factor", f"{100 * (np.abs(r - r.round()) < 1e-6).mean():.1f}%"),
        ("Master-data fields varying within an article", sum(varying.values())),
        ("Negative stock rows (back-orders)", f"{100 * (tx.inventory_level < -1e-6).mean():.1f}%"),
    ]
    return pd.DataFrame(rows, columns=["Check", "Result"])


def entry_type_table(tx):
    q = tx.groupby("entry_type").quantity.agg(rows="size", median="median",
                                              share_positive=lambda s: (s > 0).mean())
    q.index = q.index.map(lambda i: f"{i} {ENTRY_TYPES[i]}")
    return q


def stock_value(eod, price):
    """Daily stock value from an end-of-day stock table (days × articles)."""
    return eod.fillna(0).mul(price.reindex(eod.columns), axis=1).sum(axis=1)


def recency_buckets(months_since, labels=("< 1 yr", "1–2 yrs", "2–3 yrs", "3–5 yrs", "> 5 yrs / never")):
    return pd.cut(months_since.fillna(1e4), [-1, 12, 24, 36, 60, 1e5], labels=list(labels))
