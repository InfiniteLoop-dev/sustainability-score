def calculate_statistics(records):
    scores = []

    for record in records:
        scores.append(record["score"])

    if len(scores) == 0:
        return None

    return {
        "count": len(scores),
        "average": sum(scores) / len(scores),
        "highest": max(scores),
        "lowest": min(scores)
    }