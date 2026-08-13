def score_two_to_three(f):
    return (
        f["leader"]*.25 +
        f["sector_ladder"]*.15 +
        f["divergence_to_strength"]*.15 +
        f["auction"]*.20 +
        f["turnover"]*.10 +
        f["sentiment"]*.10 +
        f["risk"]*.05
    )
