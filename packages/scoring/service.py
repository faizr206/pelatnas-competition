def compute_placeholder_score(submission_id: str) -> tuple[float, float]:
    metric_value = float(len(submission_id) % 10)
    score_value = 100.0 - metric_value
    return metric_value, score_value
