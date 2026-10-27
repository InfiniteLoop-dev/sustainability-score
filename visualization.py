import matplotlib.pyplot as plt


def plot_history(records):
    if len(records) == 0:
        print("No records to plot.")
        return

    weeks = []
    scores = []

    for record in records:
        weeks.append(record["week"])
        scores.append(record["score"])

    plt.figure()
    plt.plot(weeks, scores, marker="o")

    plt.title("Sustainability Score History")
    plt.xlabel("Week")
    plt.ylabel("Score")

    plt.xticks(weeks)
    plt.grid(True)
    plt.tight_layout()

    plt.show()