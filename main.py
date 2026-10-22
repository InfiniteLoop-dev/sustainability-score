from scoring import calculate_score, get_rating
from input_utils import get_non_negative_int


def main():
    plastic_bottles = get_non_negative_int(
        "How many plastic bottles did you use this week? "
    )
    public_transport = get_non_negative_int(
        "How many times do you use public transport per week? "
    )
    recycling = get_non_negative_int(
        "How many times do you recycle per week? "
    )

    score = calculate_score(
        plastic_bottles,
        public_transport,
        recycling
    )

    rating = get_rating(score)

    print(f"Your sustainability score is {score}.")
    print(f"Rating: {rating}")

    with open("records.txt", "a+", encoding="utf-8") as file:
        file.seek(0)
        records = file.readlines()

        next_week = len(records) + 1

        file.write(f"Week {next_week}: Score = {score}\n")

    print(f"Week {next_week} record saved successfully!")


if __name__ == "__main__":
    main()