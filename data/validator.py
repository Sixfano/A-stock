import pandas as pd

REQUIRED = {
    "stock_daily": ["trade_date", "ts_code", "close", "pre_close", "amount"],
    "limitup_daily": ["trade_date", "ts_code", "consecutive_limitups"],
    "auction_daily": ["trade_date", "ts_code", "auction_price"],
}

def validate_frame(name: str, df: pd.DataFrame) -> list[str]:
    errors = []
    for col in REQUIRED.get(name, []):
        if col not in df.columns:
            errors.append(f"missing column: {col}")
    return errors

def assert_point_in_time(feature_date, available_at, cutoff):
    if available_at > cutoff:
        raise ValueError("Future-data leakage detected")
