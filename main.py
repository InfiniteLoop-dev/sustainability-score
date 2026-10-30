from scoring import calculate_score, get_rating
from input_utils import get_non_negative_int
from storage import save_record, load_records
from analysis import calculate_statistics
from visualization import plot_history
from ai_advice import build_advice_prompt, generate_advice


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

    week = save_record(score, rating)
    print(f"Week {week} record saved successfully!")
    records = load_records()

    print("\nYour history:")

    for record in records:
        print(
            f"Week {record['week']}: "
            f"Score = {record['score']}, "
            f"Rating = {record['rating']}"
        )

    statistics = calculate_statistics(records)

    if statistics is None:
        print("No records yet.")
    else:
        print("\nYour statistics:")
        print(f"Number of records: {statistics['count']}")
        print(f"Average score: {statistics['average']:.2f}")
        print(f"Highest score: {statistics['highest']}")
        print(f"Lowest score: {statistics['lowest']}")

    prompt = build_advice_prompt(
        plastic_bottles=plastic_bottles,
        public_transport=public_transport,
        recycling=recycling
    )

    print("\nGenerating AI advice...")
    advice = generate_advice(prompt)

    print("\nAI advice:")
    print(advice)

    plot_history(records)
if __name__ == "__main__":
    main()