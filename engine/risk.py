import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

def ledoit_wolf_cov(returns: pd.DataFrame):
    returns = returns.dropna(how="any", axis=1).dropna(how="any", axis=0)
    lw = LedoitWolf().fit(returns.values)
    cov = pd.DataFrame(lw.covariance_, index=returns.columns, columns=returns.columns)
    return cov

def risk_contrib(weights: pd.Series, cov: pd.DataFrame):
    port_var = float(weights.T @ cov @ weights)
    mrc = cov @ weights
    rc = weights * mrc
    return rc / port_var if port_var > 0 else rc*0
