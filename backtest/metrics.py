import numpy as np

def max_drawdown(equity):
    equity = np.asarray(equity, dtype=float)
    if len(equity) == 0:
        return 0.0
    peak = np.maximum.accumulate(equity)
    dd = equity / peak - 1
    return float(dd.min())

def summary(returns):
    r = np.asarray(returns, dtype=float)
    if len(r) == 0:
        return {"n": 0}
    return {
        "n": int(len(r)),
        "mean_return": float(r.mean()),
        "win_rate": float((r > 0).mean()),
        "max_loss": float(r.min()),
        "max_gain": float(r.max()),
    }
