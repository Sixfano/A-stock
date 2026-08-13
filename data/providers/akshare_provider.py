"""AKShare provider."""
import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None

class AKShareProvider:
    def _require(self):
        if ak is None:
            raise RuntimeError("Install AKShare first: pip install akshare")

    def stock_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        self._require()
        return ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start_date, end_date=end_date, adjust=""
        )

    def limit_up_pool(self, date: str) -> pd.DataFrame:
        self._require()
        return ak.stock_zt_pool_em(date=date)

    def limit_up_pool_previous(self, date: str) -> pd.DataFrame:
        self._require()
        return ak.stock_zt_pool_previous_em(date=date)

    def broken_board_pool(self, date: str) -> pd.DataFrame:
        self._require()
        return ak.stock_zt_pool_zbgc_em(date=date)

    def limit_down_pool(self, date: str) -> pd.DataFrame:
        self._require()
        return ak.stock_zt_pool_dtgc_em(date=date)
