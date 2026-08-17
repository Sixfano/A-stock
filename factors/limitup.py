def first_seal_score(minutes_after_open):
    if minutes_after_open is None:
        return 0.0
    bands = [(5, 100), (30, 90), (60, 80), (90, 70), (240, 55), (270, 40), (300, 20)]
    for limit, score in bands:
        if minutes_after_open <= limit:
            return score
    return 0.0


def open_board_score(count: int) -> float:
    """Legacy score retained for backward compatibility.

    New screening should prefer ``board_divergence_quality`` because open-board
    count alone cannot distinguish destructive selling from healthy absorption.
    """
    return {0: 100, 1: 80, 2: 55, 3: 30}.get(count, 0)


def board_divergence_quality(
    *,
    open_count: int,
    final_sealed: bool,
    seal_amount_ratio: float,
    above_vwap_ratio: float,
    reseal_minutes: float,
) -> float:
    """Non-linear board divergence score with a hard final-seal gate."""
    if not final_sealed:
        return 0.0

    if open_count <= 1:
        count_score = 100
    elif open_count <= 3:
        count_score = 85
    elif open_count <= 10:
        count_score = 70
    elif open_count <= 32:
        count_score = 55
    else:
        count_score = 35

    seal_score = max(0.0, min(100.0, seal_amount_ratio * 500))
    vwap_score = max(0.0, min(1.0, above_vwap_ratio)) * 100
    reseal_score = max(0.0, min(100.0, reseal_minutes / 30 * 100))
    return (
        count_score * 0.25
        + seal_score * 0.25
        + vwap_score * 0.30
        + reseal_score * 0.20
    )


def strength_and_tradability(
    *,
    final_sealed: bool,
    is_one_word: bool,
    turnover: float | None,
    divergence_quality: float,
) -> dict[str, float]:
    """Report one-word strength separately from executable/tradable quality."""
    if not final_sealed:
        return {"strength": 0.0, "tradability": 0.0}

    strength = 100.0 if is_one_word else max(50.0, divergence_quality)
    if is_one_word:
        tradability = 15.0
    else:
        turnover_score = turnover_quality(turnover)
        tradability = turnover_score * 0.55 + divergence_quality * 0.45
    return {
        "strength": round(min(100.0, strength), 2),
        "tradability": round(min(100.0, tradability), 2),
    }


def turnover_quality(turnover):
    if turnover is None:
        return 0.0
    if turnover < 2:
        return 20
    if turnover < 5:
        return 75
    if turnover < 10:
        return 100
    if turnover < 15:
        return 75
    if turnover < 20:
        return 40
    return 10


def limitup_gene_score(count_20d: int, gap_days):
    base = min(count_20d, 4) * 18
    recency = (
        20
        if gap_days is not None and gap_days <= 3
        else 10
        if gap_days is not None and gap_days <= 7
        else 0
    )
    return min(100.0, base + recency)
