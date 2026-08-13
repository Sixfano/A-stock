def volume_expansion(current_amount, previous_amount):
    if not previous_amount:
        return 0.0
    return current_amount / previous_amount

def liquidity_score(amount, turnover, float_mv):
    score = 0
    if amount and amount >= 2e8: score += 40
    if turnover is not None:
        score += 40 if 2 <= turnover <= 15 else 20
    if float_mv and float_mv >= 2e9: score += 20
    return min(score, 100)
