import numpy as np
import pandas as pd
import cvxpy as cp
from engine.config import MAX_WEIGHT, TOP3_MAX, TRANSACTION_COST_BPS

def mean_variance_opt(mu: pd.Series, cov: pd.DataFrame, long_only=True):
    assets = mu.index.tolist()
    n = len(assets)
    w = cp.Variable(n)
    lam = cp.Parameter(nonneg=True, value=1.0)
    obj = cp.Maximize(mu.values @ w - lam * cp.quad_form(w, cov.values))
    cons = [cp.sum(w) == 1.0,
            w >= 0 if long_only else w >= -0.10,
            w <= MAX_WEIGHT]
    prob = cp.Problem(obj, cons)
    prob.solve(solver=cp.SCS, verbose=False)
    out = pd.Series(np.array(w.value).ravel(), index=assets)
    # Top-3 cap
    top3 = out.sort_values(ascending=False).head(3).sum()
    if top3 > TOP3_MAX:
        sorted_idx = out.sort_values(ascending=False).index
        scale = TOP3_MAX / top3
        for i in range(3):
            out[sorted_idx[i]] *= scale
        out = out.clip(upper=MAX_WEIGHT)
        out /= out.sum()
    return out.clip(lower=0) if long_only else out

def apply_tc_and_turnover(w_old: pd.Series, w_new: pd.Series):
    tc = (w_new.sub(w_old, fill_value=0.0).abs().sum()) * (TRANSACTION_COST_BPS/10000)
    return w_new, tc
