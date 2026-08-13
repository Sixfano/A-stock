"""Auction provider interface."""
from abc import ABC, abstractmethod
import pandas as pd

class AuctionProvider(ABC):
    @abstractmethod
    def get_auction(self, trade_date: str) -> pd.DataFrame:
        raise NotImplementedError
