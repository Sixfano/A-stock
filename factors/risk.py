def acceleration_risk(turnover_today, turnover_prev, amount_today,
                     amount_prev, board_height) -> float:
    risk = 0.0
    if turnover_today is not None and turnover_prev is not None:
        if turnover_today < turnover_prev * 0.6:
            risk += 25
    if amount_today and amount_prev and amount_today < amount_prev * 0.6:
        risk += 25
    if board_height >= 4:
        risk += 10
    return min(risk, 100)

def risk_adjust(score: float, risk_score: float) -> float:
    return max(0.0, score - risk_score * 0.10)
