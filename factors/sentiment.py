def broken_board_rate(broken: int, total_limitup: int) -> float:
    return broken / total_limitup if total_limitup else 0.0


def promotion_rate_yesterday(promoted: int, candidates: int) -> float:
    return promoted / candidates if candidates else 0.0


def sentiment_state(
    limitup_count,
    limitdown_count,
    broken_rate,
    max_height,
    promotion_rate,
    yesterday_premium,
) -> str:
    score = 50
    score += min(limitup_count * 1.5, 20)
    score -= min(limitdown_count * 2, 20)
    score -= min(broken_rate * 30, 20)
    score += min(max_height * 2, 12)
    score += min(promotion_rate * 20, 12)
    score += max(-10, min(10, yesterday_premium * 2))
    if score >= 75:
        return "主升/高潮"
    if score >= 60:
        return "修复"
    if score >= 45:
        return "震荡/分歧"
    if score >= 30:
        return "退潮"
    return "冰点"


def regime_multipliers(state: str) -> dict[str, float]:
    """Shadow multipliers; they do not rewrite the four strategy base weights."""
    regimes = {
        "主升/高潮": {
            "theme_width": 1.10,
            "reseal_tolerance": 1.15,
            "high_level_gate": 0.95,
        },
        "修复": {
            "theme_width": 1.08,
            "reseal_tolerance": 1.10,
            "high_level_gate": 1.00,
        },
        "震荡/分歧": {
            "theme_width": 1.00,
            "reseal_tolerance": 1.00,
            "high_level_gate": 1.05,
        },
        "退潮": {
            "theme_width": 0.90,
            "reseal_tolerance": 0.80,
            "high_level_gate": 1.25,
        },
        "冰点": {
            "theme_width": 0.85,
            "reseal_tolerance": 0.75,
            "high_level_gate": 1.35,
        },
    }
    return regimes.get(state, regimes["震荡/分歧"]).copy()
