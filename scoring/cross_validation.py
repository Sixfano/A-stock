def cross_model_score(results: dict[str, float]) -> dict:
    present = {k: v for k, v in results.items() if v is not None}
    count = len(present)
    stars = {4: "★★★★★", 3: "★★★★☆", 2: "★★★☆☆", 1: "★★☆☆☆", 0: "★☆☆☆☆"}[count]
    return {"model_count": count, "cross_stars": stars, "scores": present}
