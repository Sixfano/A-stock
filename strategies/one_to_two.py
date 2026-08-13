def score_one_to_two(f):
    return (
        f["limitup_quality"]*.20 +
        f["sector_strength"]*.20 +
        f["limitup_gene"]*.15 +
        f["turnover_quality"]*.15 +
        f["auction"]*.20 +
        f["sentiment"]*.10
    )
