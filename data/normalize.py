import pandas as pd

def normalize_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    return df.rename(columns=mapping).copy()

def safe_ratio(numerator, denominator):
    if denominator in (None, 0):
        return None
    return numerator / denominator
