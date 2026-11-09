"""Shared data preparation for all parts (load, clean, rebuild stock, demand tables).

All quantities in the dataset are anonymised by the same factor (~1.1107),
including safety_stock and moq, so ratios between them stay valid.
"""
import os
import numpy as np
import pandas as pd

END = pd.Timestamp("2022-01-21")
DEFAULT_PATH = os.environ.get(
    "SCM_DATA",
    os.path.join(os.path.dirname(__file__), "..", "..", "anonymized_202602.csv"),
)
CATS = ["vendor_nr", "base_unit", "submarket", "item_main_group",
        "item_sub_group", "item_category", "product_category"]
DEMAND_TYPES = [1, 5]  # 1 = sale, 5 = usage for production (net of returns)


def load_transactions(path=DEFAULT_PATH):
    """Load raw CSV, order chronologically, rebuild stock levels from movements."""
    df = pd.read_csv(path, dtype={**{c: "category" for c in CATS},
                                  "article_nr": "int64", "entry_type": "int8"},
                     parse_dates=["date"]).reset_index()
    # file is newest-first within an article/day -> chronological = index desc
    df = df.sort_values(["article_nr", "date", "index"],
                        ascending=[True, True, False])
    g = df.groupby("article_nr")
    # Rebuild level as opening level + cumulative movements. This removes a
    # handful of corrupted inventory_level rows (e.g. one row at 1.1bn units).
    df["inv_after"] = g.inventory_level.transform("first") + g.quantity.cumsum()
    df["is_demand"] = df.entry_type.isin(DEMAND_TYPES)
    df["demand"] = np.where(df.is_demand, -df.quantity, 0.0)
    return df.drop(columns="index")


def article_master(tx):
    """One row per article: master data (snapshot as of 2022) + recency."""
    attrs = ["safety_stock", "lead_time", "moq", "last_direct_cost", "vendor_nr",
             "eshop", "base_unit", "submarket", "item_main_group",
             "item_sub_group", "item_category"]
    g = tx.groupby("article_nr")
    art = g[attrs].first()
    art["product_category"] = g.product_category.last()
    dm = tx[tx.is_demand & (tx.demand > 0)]
    art["last_demand_date"] = dm.groupby("article_nr").date.max()
    art["current_inv"] = g.inv_after.last().clip(lower=0)
    art["inv_article"] = art.safety_stock > 0
    # product type from movement mix
    mix = tx.groupby(["article_nr", "entry_type"]).size().unstack(fill_value=0)
    art["ptype"] = np.select(
        [mix.get(6, 0) > 0, mix.get(5, 0) >= mix.get(1, 0)],
        ["Finished (produced in-house)", "Semi-finished / component"],
        "Retail (buy & sell)")
    return art


def daily_inventory(tx, articles, start="2007-01-21", end=END):
    """End-of-day stock per article (days x articles), clipped at 0.
    NaN before an article's first transaction (not yet introduced)."""
    sub = tx[tx.article_nr.isin(articles)]
    eod = sub.groupby(["article_nr", "date"]).inv_after.last().unstack(0)
    eod = eod.reindex(pd.date_range(start, end)).ffill()
    return eod.clip(lower=0)


def period_demand(tx, articles, start, end=END, days=7):
    """Net demand (sales + production usage) per bucket of `days`, clipped at 0."""
    d = tx[tx.article_nr.isin(articles) & tx.is_demand & (tx.date > start)]
    n_weeks = int(np.ceil((end - start).days / days))
    wk = ((d.date - start).dt.days - 1) // days
    out = d.groupby([d.article_nr, wk]).demand.sum().clip(lower=0).unstack(fill_value=0)
    return out.reindex(columns=range(n_weeks), fill_value=0).reindex(articles, fill_value=0)


def sbc_class(wk, min_periods=4):
    """Syntetos-Boylan-Croston demand classes from a period x article demand table."""
    nz = (wk > 0).sum(axis=1)
    adi = wk.shape[1] / nz.replace(0, np.nan)
    sizes = wk.where(wk > 0)
    cv2 = (sizes.std(axis=1) / sizes.mean(axis=1)) ** 2
    cls = np.select(
        [nz == 0, nz < min_periods, (adi < 1.32) & (cv2 < 0.49), adi < 1.32, cv2 < 0.49],
        ["No demand", "Sporadic", "Smooth", "Erratic", "Intermittent"], "Lumpy")
    return pd.DataFrame({"ADI": adi, "CV2": cv2, "nz_periods": nz, "demand_class": cls})
