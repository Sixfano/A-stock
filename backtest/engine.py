from dataclasses import dataclass
from typing import Callable

@dataclass
class BacktestConfig:
    commission: float = 0.0003
    slippage: float = 0.001
    stamp_duty_sell: float = 0.0005

class BacktestEngine:
    def __init__(self, config: BacktestConfig | None = None):
        self.config = config or BacktestConfig()

    def run(self, dates, selector: Callable):
        return [selector(d) for d in dates]
