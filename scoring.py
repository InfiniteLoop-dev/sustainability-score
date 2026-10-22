def calculate_score(plastic_bottles, public_transport, recycling):
    return recycling * 2 + public_transport - plastic_bottles

def get_rating(score):
    if score >= 20:
        result = "Excellent"
    elif score >= 10:
        result = "Good"
    elif score >= 0:
        result = "Fair"
    else:
        result = "Needs Improvement"

    return result