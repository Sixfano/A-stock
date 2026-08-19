"""Point-in-time daily limit-up evidence screening.

The four relay strategies remain the source of candidate eligibility. Evidence
is shadow-only: it explains, ranks for review, and flags risk; it never replaces
or linearly adds to a base strategy score.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from data.point_in_time import select_point_in_time_row
from data.providers.akshare_provider import AKShareProvider, market_for_code
from data.providers.router import ProviderRouter
from factors.competition import SameHeightCandidate, same_height_competition
from factors.cyq import CYQSnapshot, cyq_structure_evidence
from factors.leader_feedback import LeaderObservation, sector_high_level_feedback
from factors.theme_reflow import theme_reflow_evidence
from strategies.high_level import score_high_level
from strategies.one_to_two import score_one_to_two
from strategies.three_to_four import score_three_to_four
from strategies.two_to_three import score_two_to_three

logger = logging.getLogger(__name__)


def _scalar(row: Any, column: str, default=None):
    if row is None or column not in row:
        return default
    value = row[column]
    return default if pd.isna(value) else value


def _number(row: Any, *columns: str, default: float = 0.0) -> float:
    for column in columns:
        value = _scalar(row, column)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                continue
    return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _safe_call(router: ProviderRouter, method: str, *args, **kwargs) -> pd.DataFrame:
    result = router.call(method, *args, **kwargs)
    if not result.available or result.data is None:
        return pd.DataFrame()
    return result.data.copy() if hasattr(result.data, "copy") else pd.DataFrame()


def _pit_row(frame: pd.DataFrame, target_date: str) -> tuple[pd.Series | None, str]:
    if frame.empty:
        return None, "unavailable"
    date_candidates = ["日期", "交易日期", "日期时间", "时间"]
    date_col = next((col for col in date_candidates if col in frame.columns), None)
    if date_col is None:
        return None, "unavailable_no_date_column"
    result = select_point_in_time_row(frame, target_date, date_col)
    return result.row, result.status


def _latest_individual_flow(router: ProviderRouter, code: str, target_date: str) -> dict:
    flow = _safe_call(router, "individual_fund_flow", code, market_for_code(code))
    row, status = _pit_row(flow, target_date)
    if row is None:
        return {"资金流可用": False, "资金流状态": status}
    return {
        "资金流可用": True,
        "资金流状态": status,
        "主力净流入占比": _scalar(row, "主力净流入-净占比"),
        "超大单净流入占比": _scalar(row, "超大单净流入-净占比"),
        "大单净流入占比": _scalar(row, "大单净流入-净占比"),
    }


def _latest_cyq(router: ProviderRouter, code: str, close: float | None, target_date: str) -> dict:
    if close is None or close <= 0:
        return {"CYQ可用": False, "CYQ状态": "unavailable_no_close"}
    cyq = _safe_call(router, "cyq", code)
    row, status = _pit_row(cyq, target_date)
    if row is None:
        return {"CYQ可用": False, "CYQ状态": status}
    snap = CYQSnapshot(
        close=float(close),
        winner_ratio=_scalar(row, "获利比例"),
        avg_cost=_scalar(row, "平均成本"),
        cost90_low=_scalar(row, "90成本-低"),
        cost90_high=_scalar(row, "90成本-高"),
        concentration90=_scalar(row, "90集中度"),
        cost70_low=_scalar(row, "70成本-低"),
        cost70_high=_scalar(row, "70成本-高"),
        concentration70=_scalar(row, "70集中度"),
    )
    evidence = cyq_structure_evidence(snap)
    return {
        "CYQ可用": evidence.available,
        "CYQ状态": status,
        "CYQ获利比例": snap.winner_ratio,
        "CYQ平均成本": snap.avg_cost,
        "CYQ90成本低": snap.cost90_low,
        "CYQ90成本高": snap.cost90_high,
        "CYQ90集中度": snap.concentration90,
        "CYQ70成本低": snap.cost70_low,
        "CYQ70成本高": snap.cost70_high,
        "CYQ70集中度": snap.concentration70,
        "CYQ影子分": evidence.score,
        "CYQ论据": evidence.detail,
    }


def _base_score(row: pd.Series) -> tuple[str, float]:
    """Evaluate a base-style score from normalized pool fields only.

    This is a reporting adapter; the four strategy functions and their weights
    are untouched. Missing fields default to neutral values and are not treated
    as evidence.
    """
    height = int(_number(row, "连板数", default=0))
    common = {
        "auction": _clamp(50 + _number(row, "竞价涨幅", "竞价金额", default=0) * 5),
        "sentiment": 50.0,
        "risk": _clamp(60 - _number(row, "炸板次数", default=0) * 8),
    }
    if height == 1:
        features = {**common, "limitup_quality": _clamp(70), "sector_strength": 50,
                    "limitup_gene": 50, "turnover_quality": _clamp(_number(row, "换手率", default=10) * 5)}
        return "一进二", round(score_one_to_two(features), 2)
    if height == 2:
        features = {**common, "leader": 55, "sector_ladder": 50,
                    "divergence_to_strength": 55, "turnover": _clamp(_number(row, "换手率", default=10) * 5)}
        return "二进三", round(score_two_to_three(features), 2)
    if height == 3:
        features = {**common, "leader": 60, "market_height": 55,
                    "sector_diffusion": 50, "turnover_structure": _clamp(_number(row, "换手率", default=10) * 5),
                    "acceleration_risk": 50}
        return "三进四", round(score_three_to_four(features), 2)
    features = {**common, "leader_identity": 60, "theme_core": 55,
                "market_height": 60, "sector_ladder": 50}
    return "高标接力", round(score_high_level(features), 2)


def _candidate_evidence(row: pd.Series, peers: list[pd.Series], target_date: str) -> dict:
    sector = str(_scalar(row, "所属行业", _scalar(row, "行业", "未知")))
    code = str(_scalar(row, "代码", ""))
    height = int(_number(row, "连板数", default=0))
    def candidate(item: pd.Series) -> SameHeightCandidate:
        return SameHeightCandidate(
            name=str(_scalar(item, "名称", _scalar(item, "代码", "未知"))),
            height=int(_number(item, "连板数", default=0)),
            sector=str(_scalar(item, "所属行业", _scalar(item, "行业", "未知"))),
            auction_score=_clamp(50 + _number(item, "竞价涨幅", default=0) * 5),
            turnover_quality=_clamp(_number(item, "换手率", default=10) * 5),
            limitup_quality=_clamp(70 - _number(item, "炸板次数", default=0) * 8),
            sector_strength=_clamp(50 + _number(item, "涨停家数", default=0) * 5),
            leader_identity=_clamp(50 + _number(item, "连板数", default=0) * 8),
            tradability=_clamp(70 - _number(item, "炸板次数", default=0) * 7),
        )
    target = candidate(row)
    competition = same_height_competition(target, [candidate(item) for item in peers])

    observations = []
    for item in peers:
        if str(_scalar(item, "所属行业", _scalar(item, "行业", "未知"))) != sector:
            continue
        item_height = int(_number(item, "连板数", default=0))
        if item_height < height:
            continue
        observations.append(LeaderObservation(
            name=str(_scalar(item, "名称", _scalar(item, "代码", "未知"))),
            height=item_height,
            pct_chg=_number(item, "涨跌幅", "涨幅", default=0),
            auction_gap=_number(item, "竞价涨幅", default=0),
            final_sealed=_number(item, "炸板次数", default=0) == 0,
            limit_down=_number(item, "涨跌幅", "涨幅", default=0) <= -9,
            above_vwap_ratio=None,
            is_sector_core=item_height >= height,
        ))
    feedback = sector_high_level_feedback(observations)
    sector_count = len([item for item in peers if str(_scalar(item, "所属行业", _scalar(item, "行业", "未知"))) == sector])
    ladder = _clamp(40 + sector_count * 12)
    reflow = theme_reflow_evidence(
        prior_heat=_clamp(45 + height * 10),
        divergence_depth=_clamp(50 + _number(row, "炸板次数", default=0) * 5),
        sector_flow_score=_clamp(50 + _number(row, "板块主力净流入", default=0)),
        leader_feedback_score=feedback.score,
        ladder_completeness=ladder,
        breadth_recovery=_clamp(40 + sector_count * 10),
        auction_core_strength=_clamp(50 + _number(row, "竞价涨幅", default=0) * 5),
    )
    return {
        "板块地位": f"{sector}；同题材候选{sector_count}只；梯队完整度{ladder:.0f}",
        "高标反馈分": feedback.score,
        "高标反馈": feedback.detail,
        "同身位卡位分": competition.score,
        "同身位卡位": competition.detail,
        "题材回流分": reflow.score,
        "题材回流": reflow.detail,
        "证据模块可用": any((feedback.available, competition.available, reflow.available)),
    }


def _narrative(row: pd.Series) -> tuple[str, str, str]:
    positive: list[str] = []
    negative: list[str] = []
    if _number(row, "同身位卡位分", default=50) >= 65:
        positive.append("同身位主动性/可交易性较强")
    else:
        negative.append("同身位竞争不占优")
    if _number(row, "高标反馈分", default=50) >= 65:
        positive.append("板块高标反馈偏正向")
    elif _number(row, "高标反馈分", default=50) <= 38:
        negative.append("板块高位核心存在明显负反馈")
    if _number(row, "题材回流分", default=50) >= 65:
        positive.append("题材具备回流条件")
    if _number(row, "CYQ获利比例", default=50) >= 92:
        negative.append("获利盘比例偏高，需防一致兑现")
    if _number(row, "炸板次数", default=0) >= 2:
        negative.append("炸板次数偏多")
    flow = _scalar(row, "主力净流入占比")
    if flow is not None and float(flow) > 0:
        positive.append("个股资金流为正")
    if not positive:
        positive.append("保留原连板模型判断，新增证据不足")
    if not negative:
        negative.append("未发现已量化的主要反向证据，仍需观察竞价与量能")
    next_day = "高开0~4%且量能匹配可视为符合预期；高开过高但量能不足需防一致兑现；平开后回到均价线上可作弱转强观察。"
    return "；".join(positive), "；".join(negative), next_day


def build_snapshot(date: str, enrich_top: int = 80, cyq_top: int = 30, provider: Any | None = None) -> pd.DataFrame:
    router = provider if isinstance(provider, ProviderRouter) else ProviderRouter([provider or AKShareProvider()])
    pool = _safe_call(router, "limit_up_pool", date)
    if pool.empty:
        return pool
    pool["代码"] = pool["代码"].astype(str).str.zfill(6)
    quality: dict[str, str] = {}

    strong = _safe_call(router, "strong_pool", date)
    if not strong.empty and "代码" in strong.columns:
        strong["代码"] = strong["代码"].astype(str).str.zfill(6)
        keep = [c for c in ["代码", "入选理由", "是否新高", "量比"] if c in strong.columns]
        pool = pool.merge(strong[keep].drop_duplicates("代码"), on="代码", how="left")
    quality["强势股池"] = router.quality.get("strong_pool", "unavailable")

    lhb = _safe_call(router, "dragon_tiger", date, date)
    if not lhb.empty and "代码" in lhb.columns:
        lhb["代码"] = lhb["代码"].astype(str).str.zfill(6)
        keep = [c for c in ["代码", "龙虎榜净买额", "净买额占总成交比", "上榜原因"] if c in lhb.columns]
        pool = pool.merge(lhb[keep].drop_duplicates("代码"), on="代码", how="left")
    quality["龙虎榜"] = router.quality.get("dragon_tiger", "unavailable")

    ranked = pool.sort_values([c for c in ["连板数", "封板资金", "成交额"] if c in pool.columns], ascending=False) if any(c in pool.columns for c in ["连板数", "封板资金", "成交额"]) else pool
    flow_rows = {code: _latest_individual_flow(router, code, date) for code in ranked.head(max(0, enrich_top))["代码"].tolist()}
    flow_df = pd.DataFrame.from_dict(flow_rows, orient="index")
    if not flow_df.empty:
        flow_df.index.name = "代码"
        pool = pool.merge(flow_df.reset_index(), on="代码", how="left")
    quality["资金流"] = "ok" if any(item.get("资金流可用") for item in flow_rows.values()) else "unavailable"

    ranked_now = pool.set_index("代码", drop=False)
    cyq_rows = {}
    for code in ranked.head(max(0, cyq_top))["代码"].tolist():
        close = _number(ranked_now.loc[code], "最新价", default=0) if code in ranked_now.index else 0
        cyq_rows[code] = _latest_cyq(router, code, close, date)
    cyq_df = pd.DataFrame.from_dict(cyq_rows, orient="index")
    if not cyq_df.empty:
        cyq_df.index.name = "代码"
        pool = pool.merge(cyq_df.reset_index(), on="代码", how="left")
    quality["CYQ"] = "ok" if any(item.get("CYQ可用") for item in cyq_rows.values()) else "unavailable"

    pool["接力模式"] = pool.get("连板数", pd.Series(index=pool.index, dtype=float)).map(lambda h: "一进二" if h == 1 else "二进三" if h == 2 else "三进四" if h == 3 else "高标接力")
    base_values = pool.apply(lambda row: _base_score(row), axis=1)
    pool["基础策略"] = [item[0] for item in base_values]
    pool["base_strategy_score"] = [item[1] for item in base_values]
    evidence_rows = []
    for _, row in pool.iterrows():
        peers = [item for _, item in pool.iterrows() if int(_number(item, "连板数", default=0)) == int(_number(row, "连板数", default=0))]
        evidence_rows.append(_candidate_evidence(row, peers, date))
    evidence_df = pd.DataFrame(evidence_rows, index=pool.index)
    pool = pd.concat([pool, evidence_df], axis=1)
    evidence_cols = ["高标反馈分", "同身位卡位分", "题材回流分"]
    pool["evidence_shadow_score"] = pool[evidence_cols].mean(axis=1).round(2)
    pool["final_score"] = pool["base_strategy_score"]
    narratives = pool.apply(_narrative, axis=1, result_type="expand")
    pool["正向证据"], pool["反向证据 / 风险"], pool["次日观察重点"] = narratives[0], narratives[1], narratives[2]
    pool["新增论据"] = pool["正向证据"] + "；反向/风险：" + pool["反向证据 / 风险"]
    pool["data_quality"] = [dict(quality, **router.quality_report()) for _ in range(len(pool))]
    return pool


def main() -> None:
    parser = argparse.ArgumentParser(description="Point-in-time limit-up evidence screen")
    parser.add_argument("--date", required=True, help="Target trading date YYYYMMDD")
    parser.add_argument("--enrich-top", type=int, default=80)
    parser.add_argument("--cyq-top", type=int, default=30)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    frame = build_snapshot(args.date, args.enrich_top, args.cyq_top)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(out, index=False, encoding="utf-8-sig")
        print(out)
        return
    preferred = [c for c in [
        "代码", "名称", "连板数", "接力模式", "基础策略", "base_strategy_score",
        "evidence_shadow_score", "final_score", "板块地位", "高标反馈", "同身位卡位",
        "题材回流", "CYQ论据", "正向证据", "反向证据 / 风险", "次日观察重点",
    ] if c in frame.columns]
    print(frame[preferred].to_string(index=False))


if __name__ == "__main__":
    main()
