from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class StockDaily:
    trade_date: date
    ts_code: str
    name: str
    open: float
    high: float
    low: float
    close: float
    pre_close: float
    pct_chg: float
    amount: float
    vol: float
    turnover: Optional[float] = None
    float_mv: Optional[float] = None

@dataclass
class LimitUpDaily:
    trade_date: date
    ts_code: str
    name: str
    consecutive_limitups: int
    first_limitup_time: Optional[str] = None
    last_limitup_time: Optional[str] = None
    open_board_count: int = 0
    reseal_count: int = 0
    seal_amount: Optional[float] = None
    limitup_type: Optional[str] = None
    limitup_reason: Optional[str] = None
    sector: Optional[str] = None

@dataclass
class AuctionDaily:
    trade_date: date
    ts_code: str
    auction_price: float
    auction_pct: float
    auction_volume: float
    auction_amount: float
