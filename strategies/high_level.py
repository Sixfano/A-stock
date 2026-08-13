def score_high_level(f):
    return (
        f["leader_identity"]*.25 +
        f["theme_core"]*.20 +
        f["market_height"]*.15 +
        f["sector_ladder"]*.10 +
        f["sentiment"]*.15 +
        f["auction"]*.10 +
        f["risk"]*.05
    )
