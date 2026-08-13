def auction_gap_score(gap_pct: float) -> float:
    if gap_pct >= 9: return 100
    if gap_pct >= 6: return 85
    if gap_pct >= 3: return 70
    if gap_pct >= 0: return 50
    if gap_pct >= -2: return 25
    return 0

def ratio_score(ratio):
    if ratio is None: return 0
    if ratio >= .15: return 100
    if ratio >= .10: return 85
    if ratio >= .05: return 70
    if ratio >= .02: return 50
    return 20

def auction_score(gap_score, amount_ratio_score, volume_score,
                  sector_score, peer_rank_score):
    return (gap_score*.30 + amount_ratio_score*.25 + volume_score*.15 +
            sector_score*.15 + peer_rank_score*.15)
