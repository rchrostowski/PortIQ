import numpy as np, pandas as pd
from engine.optimizer import apply_tc_and_turnover

def backtest(px: pd.DataFrame, weights_ts: pd.DataFrame):
    px = px.reindex(weights_ts.index.union(px.index)).ffill()
    rets = px.pct_change().fillna(0)
    w = weights_ts.reindex(rets.index).ffill().fillna(0)
    port_ret = (w.shift(1) * rets).sum(axis=1)
    cum = (1 + port_ret).cumprod()
    stats = {
        "ann_return": (cum.iloc[-1]) ** (252/len(cum)) - 1,
        "ann_vol": port_ret.std() * np.sqrt(252),
        "sharpe": (port_ret.mean()/port_ret.std())*np.sqrt(252) if port_ret.std()>0 else 0,
        "max_dd": ((cum/cum.cummax())-1).min(),
        "turnover": w.diff().abs().sum(axis=1).mean()
    }
    return port_ret, cum, stats
