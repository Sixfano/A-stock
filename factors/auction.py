def auction_gap_score(gap_pct: float) -> float:
    if gap_pct >= 9:
        return 100
    if gap_pct >= 6:
        return 85
    if gap_pct >= 3:
        return 70
    if gap_pct >= 0:
        return 50
    if gap_pct >= -2:
        return 25
    return 0


def ratio_score(ratio):
    if ratio is None:
        return 0
    if ratio >= 0.15:
        return 100
    if ratio >= 0.10:
        return 85
    if ratio >= 0.05:
        return 70
    if ratio >= 0.02:
        return 50
    return 20


def auction_score(
    gap_score,
    amount_ratio_score,
    volume_score,
    sector_score,
    peer_rank_score,
):
    return (
        gap_score * 0.30
        + amount_ratio_score * 0.25
        + volume_score * 0.15
        + sector_score * 0.15
        + peer_rank_score * 0.15
    )


def in_weak_to_strong_soft_pool(
    gap_pct: float | None,
    lower: float = 0.0,
    upper: float = 5.0,
) -> bool:
    """Keep a 0% to +5% auction gap as a soft feature, not a hard rejection."""
    return gap_pct is not None and lower <= gap_pct <= upper


def delayed_confirmation_score(
    *,
    prior_distinctive: bool,
    sector_ladder_score: float,
    above_vwap_ratio: float,
    reseal_minutes: float,
    seal_amount_ratio: float,
) -> float:
    """Shadow score used at the 10:00 delayed weak-to-strong review.

    The score is intentionally separate from the 09:35 formal pool. A stock must
    already have prior-day identity; otherwise the delayed window would simply
    expand the pool with low-quality laggards.
    """
    if not prior_distinctive:
        return 0.0

    ladder = max(0.0, min(100.0, sector_ladder_score))
    vwap = max(0.0, min(1.0, above_vwap_ratio)) * 100
    reseal = max(0.0, min(100.0, reseal_minutes / 15 * 100))
    seal = max(0.0, min(100.0, seal_amount_ratio * 500))
    return ladder * 0.30 + vwap * 0.30 + reseal * 0.20 + seal * 0.20
