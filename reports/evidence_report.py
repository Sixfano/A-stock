"""Daily evidence narrative helpers."""
from __future__ import annotations

from factors.evidence import EvidenceBundle


def relay_evidence_narrative(
    *,
    stock_name: str,
    height: int,
    base_strategy: str,
    bundle: EvidenceBundle,
    base_strategy_score: float | None = None,
    positive: list[str] | None = None,
    negative: list[str] | None = None,
    next_day_focus: str | None = None,
) -> str:
    """Render explicit base/shadow scores without pretending they are additive."""
    args = bundle.arguments()
    positive_text = "；".join(positive or args) or "暂无新增正向证据"
    negative_text = "；".join(negative or []) or "暂无已量化反向证据，仍需观察"
    base_text = "不可用" if base_strategy_score is None else f"{base_strategy_score:.2f}"
    next_day = next_day_focus or "结合竞价、量能和均价线承接复核"
    return (
        f"{stock_name}（{height}板，{base_strategy}）"
        f"基础策略分 {base_text}；影子证据分 {bundle.shadow_score:.2f}。"
        f"核心入选逻辑：原连板策略候选。"
        f"正向证据：{positive_text}。"
        f"反向证据/风险：{negative_text}。"
        f"次日观察重点：{next_day}。"
        "影子证据不覆盖原策略分数，也不与基础分线性相加。"
    )
