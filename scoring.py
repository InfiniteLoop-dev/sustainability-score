DEFAULT_WEIGHTS = {
    "plastic_bottles": -1,
    "public_transport": 1,
    "recycling": 2,
    "reusable_items": 1,
}

RATING_THRESHOLDS = {
    "excellent": 20,
    "good": 10,
    "fair": 0,
}


def get_rating(score):
    """Map a numeric sustainability score to a qualitative rating."""
    if score >= RATING_THRESHOLDS["excellent"]:
        return "Excellent"
    if score >= RATING_THRESHOLDS["good"]:
        return "Good"
    if score >= RATING_THRESHOLDS["fair"]:
        return "Fair"
    return "Needs Improvement"


def calculate_score_breakdown(
    plastic_bottles,
    public_transport,
    recycling,
    weights=None,
    reusable_items=0,
):
    """Calculate per-category point contributions, total score, and rating."""
    active_weights = {**DEFAULT_WEIGHTS, **(weights or {})}

    bottles_points = plastic_bottles * active_weights["plastic_bottles"]
    transport_points = public_transport * active_weights["public_transport"]
    recycling_points = recycling * active_weights["recycling"]
    reusable_points = reusable_items * active_weights["reusable_items"]

    total = bottles_points + transport_points + recycling_points + reusable_points
    return {
        "plastic_bottles": bottles_points,
        "public_transport": transport_points,
        "recycling": recycling_points,
        "reusable_items": reusable_points,
        "total": total,
        "rating": get_rating(total),
    }


def calculate_score(
    plastic_bottles,
    public_transport,
    recycling,
    weights=None,
    reusable_items=0,
):
    """Calculate total sustainability score using default or custom habit weights."""
    return calculate_score_breakdown(
        plastic_bottles,
        public_transport,
        recycling,
        weights=weights,
        reusable_items=reusable_items,
    )["total"]
