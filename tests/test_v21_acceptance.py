import subprocess
import sys

import pandas as pd

from data.point_in_time import select_point_in_time_row
from scripts.run_screen import build_snapshot
from strategies.high_level import score_high_level
from strategies.one_to_two import score_one_to_two
from strategies.three_to_four import score_three_to_four
from strategies.two_to_three import score_two_to_three


class SparseProvider:
    def limit_up_pool(self, date):
        return pd.DataFrame([{
            "代码": "000001", "名称": "测试股", "连板数": 2,
            "最新价": 10.0, "换手率": 12.0, "炸板次数": 0,
            "所属行业": "测试题材", "涨跌幅": 10.0,
        }])

    def strong_pool(self, date):
        return pd.DataFrame()

    def dragon_tiger(self, start_date, end_date):
        return pd.DataFrame()

    def individual_fund_flow(self, stock, market):
        return pd.DataFrame()

    def cyq(self, symbol, adjust=""):
        return pd.DataFrame()


def test_point_in_time_never_uses_future_row():
    frame = pd.DataFrame({"日期": ["20260813", "20260814", "20260819"], "值": [13, 14, 19]})
    result = select_point_in_time_row(frame, "20260813")
    assert result.available is True
    assert result.status == "exact"
    assert result.row["值"] == 13
    fallback = select_point_in_time_row(frame, "20260815")
    assert fallback.status == "fallback_prior"
    assert fallback.row["值"] == 14


def test_missing_evidence_sources_degrade_without_crashing():
    result = build_snapshot("20260813", provider=SparseProvider())
    assert len(result) == 1
    assert bool(result.iloc[0]["CYQ可用"]) is False
    assert result.iloc[0]["基础策略"] == "二进三"
    assert "正向证据" in result.columns
    assert "反向证据 / 风险" in result.columns


def test_cli_help_smoke():
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.run_screen", "--help"],
        check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0
    assert "--date" in completed.stdout


def test_evidence_does_not_change_base_strategy_functions():
    one = {"limitup_quality": 80, "sector_strength": 70, "limitup_gene": 65,
           "turnover_quality": 75, "auction": 72, "sentiment": 60}
    two = {"leader": 80, "sector_ladder": 70, "divergence_to_strength": 65,
           "auction": 72, "turnover": 75, "sentiment": 60, "risk": 55}
    three = {"leader": 80, "market_height": 70, "sector_diffusion": 65,
             "turnover_structure": 75, "auction": 72, "sentiment": 60,
             "acceleration_risk": 55}
    high = {"leader_identity": 80, "theme_core": 70, "market_height": 65,
            "sector_ladder": 75, "sentiment": 60, "auction": 72, "risk": 55}
    before = [score_one_to_two(one), score_two_to_three(two),
              score_three_to_four(three), score_high_level(high)]
    _ = build_snapshot("20260813", provider=SparseProvider())
    after = [score_one_to_two(one), score_two_to_three(two),
             score_three_to_four(three), score_high_level(high)]
    assert after == before
