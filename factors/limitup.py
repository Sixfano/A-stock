def first_seal_score(minutes_after_open):
    if minutes_after_open is None:
        return 0.0
    bands = [(5,100),(30,90),(60,80),(90,70),(240,55),(270,40),(300,20)]
    for limit, score in bands:
        if minutes_after_open <= limit:
            return score
    return 0.0

def open_board_score(count: int) -> float:
    return {0:100, 1:80, 2:55, 3:30}.get(count, 0)

def turnover_quality(turnover):
    if turnover is None: return 0.0
    if turnover < 2: return 20
    if turnover < 5: return 75
    if turnover < 10: return 100
    if turnover < 15: return 75
    if turnover < 20: return 40
    return 10

def limitup_gene_score(count_20d: int, gap_days):
    base = min(count_20d, 4) * 18
    recency = 20 if gap_days is not None and gap_days <= 3 else 10 if gap_days is not None and gap_days <= 7 else 0
    return min(100.0, base + recency)
