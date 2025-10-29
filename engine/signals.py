import pandas as pd
import numpy as np

def momentum_signals(px: pd.DataFrame):
    r_1m = px.pct_change(21)
    r_3m = px.pct_change(63)
    r_12m = px.pct_change(252)
    combo = 0.3*r_1m + 0.3*r_3m + 0.4*r_12m
    return pd.DataFrame({
        "1m": r_1m.stack(),
        "3m": r_3m.stack(),
        "12m": r_12m.stack(),
        "combo": combo.stack()
    }).unstack()

def volatility(px: pd.DataFrame):
    vol20 = px.pct_change().rolling(20).std() * np.sqrt(252)
    vol60 = px.pct_change().rolling(60).std() * np.sqrt(252)
    return pd.DataFrame({
        "vol20": vol20.stack(),
        "vol60": vol60.stack()
    }).unstack()

def value_proxy(px: pd.DataFrame):
    r_12m = px.pct_change(252)
    val = -r_12m
    return pd.DataFrame({"value": val.stack()}).unstack()

def quality_proxy(px: pd.DataFrame):
    vol20 = px.pct_change().rolling(20).std()
    qual = -vol20
    return pd.DataFrame({"quality": qual.stack()}).unstack()

def size_proxy(px: pd.DataFrame):
    inv_price = -np.log(px)
    return pd.DataFrame({"size": inv_price.stack()}).unstack()

def build_signal_panel(px: pd.DataFrame):
    moms = momentum_signals(px)
    vols = volatility(px)
    vals = value_proxy(px)
    quals = quality_proxy(px)
    sizes = size_proxy(px)
    panel = moms.join(vols, how="outer").join(vals, how="outer").join(quals, how="outer").join(sizes, how="outer")

    # Winsorize + z-score normalize
    panel = panel.groupby(level=0).apply(
        lambda df: df.clip(lower=df.quantile(0.01), upper=df.quantile(0.99))
    ).droplevel(0)
    panel = panel.groupby(level=0).apply(
        lambda df: (df - df.mean()) / df.std(ddof=0)
    ).droplevel(0)
    return panel.sort_index()
