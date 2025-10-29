import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit
from engine.config import HORIZON_DAYS, SEED

def build_training_set(px, panel, horizon=HORIZON_DAYS):
    fwd = px.shift(-horizon)/px - 1.0
    fwd = fwd.stack().rename("target")
    feats = panel.stack()
    df = feats.join(fwd, how="inner").dropna()
    df = df.groupby(level=1).apply(lambda x: x.shift(1)).dropna()
    return df

def train_xgb_like(df: pd.DataFrame):
    X = df.drop(columns=["target"]).values
    y = df["target"].values
    tscv = TimeSeriesSplit(n_splits=5)
    preds = np.zeros_like(y)
    models = []
    for train_idx, test_idx in tscv.split(X):
        model = GradientBoostingRegressor(
            random_state=SEED, max_depth=3,
            n_estimators=300, learning_rate=0.05
        )
        model.fit(X[train_idx], y[train_idx])
        preds[test_idx] = model.predict(X[test_idx])
        models.append(model)
    return models, preds

def predict_latest(models, latest_row: pd.DataFrame):
    m = models[-1]
    X = latest_row.values
    return m.predict(X)
