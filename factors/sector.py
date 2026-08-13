def sector_strength(limitup_count, stock_count, consecutive_count,
                    max_height, sector_pct, amount_change) -> float:
    density = 100 * limitup_count / stock_count if stock_count else 0
    density_score = min(density * 8, 100)
    height_score = min(max_height * 15, 100)
    ladder_score = min(consecutive_count * 20, 100)
    pct_score = max(0, min(100, 50 + sector_pct * 10))
    amount_score = max(0, min(100, 50 + amount_change * 2))
    return (density_score*0.25 + height_score*0.2 +
            ladder_score*0.2 + pct_score*0.2 + amount_score*0.15)

def ladder_completeness(heights: list[int]) -> float:
    if not heights:
        return 0.0
    max_h = max(heights)
    present = sum(1 for h in range(1, max_h + 1) if h in heights)
    return 100 * present / max_h
