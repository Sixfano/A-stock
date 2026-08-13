def score_three_to_four(f):
    return (
        f["leader"]*.25 +
        f["market_height"]*.15 +
        f["sector_diffusion"]*.15 +
        f["turnover_structure"]*.15 +
        f["auction"]*.10 +
        f["sentiment"]*.10 +
        f["acceleration_risk"]*.10
    )
