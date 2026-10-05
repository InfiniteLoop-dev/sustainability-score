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


plastic_bottles = int(input("How many bottles do you use per week? "))
public_transport = int(input("How many times do you use public transport per week? "))
recycling = int(input("How many times do you recycle per week? "))

score = calculate_score(
    plastic_bottles,
    public_transport,
    recycling
)

rating = get_rating(score)

print(f"Your sustainability score is {score}.")
print(f"Rating: {rating}")