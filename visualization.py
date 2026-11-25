from pathlib import Path
import matplotlib.pyplot as plt

from scoring import RATING_THRESHOLDS


def _select_xticks(weeks, max_ticks=12):
    """Select evenly spaced x-axis ticks when many weeks are recorded."""
    if len(weeks) <= max_ticks:
        return weeks

    step = max(1, (len(weeks) - 1) // (max_ticks - 1))
    ticks = weeks[::step]
    if ticks[-1] != weeks[-1]:
        ticks.append(weeks[-1])
    return ticks


def plot_history(records, save_path=None, show=True):
    """Plot score history with rating reference lines, labels, and optional PNG export."""
    if len(records) == 0:
        print("No records to plot.")
        return None

    weeks = [record["week"] for record in records]
    scores = [record["score"] for record in records]

    fig, ax = plt.subplots()
    ax.plot(weeks, scores, marker="o", linewidth=2, color="#15803d", label="Score")

    # Rating threshold reference lines
    ax.axhline(
        RATING_THRESHOLDS["excellent"],
        color="#16a34a",
        linestyle="--",
        linewidth=1,
        alpha=0.65,
        label=f"Excellent ({RATING_THRESHOLDS['excellent']})",
    )
    ax.axhline(
        RATING_THRESHOLDS["good"],
        color="#2563eb",
        linestyle="--",
        linewidth=1,
        alpha=0.65,
        label=f"Good ({RATING_THRESHOLDS['good']})",
    )
    ax.axhline(
        RATING_THRESHOLDS["fair"],
        color="#d97706",
        linestyle="--",
        linewidth=1,
        alpha=0.65,
        label=f"Fair ({RATING_THRESHOLDS['fair']})",
    )

    for week, score in zip(weeks, scores):
        ax.annotate(
            str(score),
            (week, score),
            textcoords="offset points",
            xytext=(0, 8),
            ha="center",
            fontsize=8,
        )

    ax.set_title("Sustainability Score History")
    ax.set_xlabel("Week")
    ax.set_ylabel("Score")
    ax.set_xticks(_select_xticks(weeks))
    ax.margins(y=0.15)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()

    saved_file = None
    if save_path:
        saved_file = Path(save_path)
        saved_file.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(saved_file, dpi=150)

    if show:
        plt.show()

    plt.close(fig)
    return saved_file
