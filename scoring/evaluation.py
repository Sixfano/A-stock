def screening_metrics(
    predicted: set[str],
    promoted: set[str],
    tradable_promoted: set[str] | None = None,
) -> dict[str, float | int]:
    """Track precision, recall and tradable success under separate denominators."""
    true_positive = predicted & promoted
    false_negative = promoted - predicted
    precision = len(true_positive) / len(predicted) if predicted else 0.0
    recall = len(true_positive) / len(promoted) if promoted else 0.0

    tradable_promoted = tradable_promoted or set()
    tradable_hits = predicted & tradable_promoted
    tradable_success_rate = (
        len(tradable_hits) / len(predicted) if predicted else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "false_negative_count": len(false_negative),
        "tradable_success_rate": tradable_success_rate,
        "predicted_count": len(predicted),
        "promoted_count": len(promoted),
    }


def reweighting_readiness(
    trading_days: int,
    candidate_count: int,
    *,
    minimum_days: int = 5,
    minimum_candidates: int = 50,
) -> dict[str, bool | int]:
    """Prevent a single strong-repair session from rewriting model weights."""
    return {
        "ready": trading_days >= minimum_days and candidate_count >= minimum_candidates,
        "days_remaining": max(0, minimum_days - trading_days),
        "candidates_remaining": max(0, minimum_candidates - candidate_count),
    }

