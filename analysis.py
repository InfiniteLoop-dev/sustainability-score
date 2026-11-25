def calculate_statistics(records):
    """Compute count, average, highest, and lowest scores from history records."""
    if not records:
        return None

    scores = [record["score"] for record in records]
    return {
        "count": len(scores),
        "average": sum(scores) / len(scores),
        "highest": max(scores),
        "lowest": min(scores),
    }


def summarize_trend(records):
    """Summarize recent score and habit changes across saved history records."""
    stats = calculate_statistics(records)
    if stats is None:
        return None

    latest = records[-1]
    previous = records[-2] if len(records) >= 2 else None
    delta_from_previous = (
        latest["score"] - previous["score"] if previous is not None else None
    )
    delta_from_average = latest["score"] - stats["average"]

    habit_deltas = {}
    if previous is not None:
        for field in ("plastic_bottles", "public_transport", "recycling"):
            curr_val = latest.get(field)
            prev_val = previous.get(field)
            if curr_val is not None and prev_val is not None:
                habit_deltas[field] = curr_val - prev_val

    return {
        "count": stats["count"],
        "average": stats["average"],
        "latest_week": latest["week"],
        "latest_score": latest["score"],
        "latest_rating": latest["rating"],
        "previous_score": previous["score"] if previous is not None else None,
        "delta_from_previous": delta_from_previous,
        "delta_from_average": delta_from_average,
        "habit_deltas": habit_deltas,
    }
