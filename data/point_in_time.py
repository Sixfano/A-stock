"""Point-in-time helpers used by historical screening and evidence providers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class PITResult:
    row: pd.Series | None
    available: bool
    matched_date: str | None
    status: str


def normalize_date(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        return digits[:8] if len(digits) >= 8 else None
    return parsed.strftime("%Y%m%d")


def select_point_in_time_row(
    frame: pd.DataFrame | None,
    target_date: str,
    date_col: str = "日期",
) -> PITResult:
    """Return exact target date or latest prior row, never a future row."""
    if frame is None or frame.empty or date_col not in frame.columns:
        return PITResult(None, False, None, "unavailable")
    target = normalize_date(target_date)
    if target is None:
        return PITResult(None, False, None, "invalid_target_date")
    work = frame.copy()
    work["__pit_date"] = work[date_col].map(normalize_date)
    work = work[work["__pit_date"].notna() & (work["__pit_date"] <= target)]
    if work.empty:
        return PITResult(None, False, None, "no_prior_record")
    work = work.sort_values("__pit_date")
    row = work.iloc[-1].drop(labels=["__pit_date"])
    matched = normalize_date(row.get(date_col))
    status = "exact" if matched == target else "fallback_prior"
    return PITResult(row, True, matched, status)


def trim_point_in_time(
    frame: pd.DataFrame | None,
    target_date: str,
    date_col: str = "日期",
) -> pd.DataFrame:
    """Keep only records visible at target_date for downstream aggregation."""
    if frame is None or frame.empty or date_col not in frame.columns:
        return frame if frame is not None else pd.DataFrame()
    target = normalize_date(target_date)
    if target is None:
        return frame.iloc[0:0].copy()
    dates = frame[date_col].map(normalize_date)
    return frame[dates.notna() & (dates <= target)].copy()
