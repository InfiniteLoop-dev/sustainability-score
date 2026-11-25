import argparse
from pathlib import Path

from ai_advice import build_advice_prompt, generate_advice
from analysis import calculate_statistics, summarize_trend
from input_utils import get_choice, get_non_negative_int
from scoring import calculate_score, calculate_score_breakdown, get_rating
from storage import (
    delete_last_record,
    delete_record_by_week,
    load_records,
    save_record,
    update_record_by_week,
)
from visualization import plot_history

WEEKLY_SANITY_LIMIT = 50


def prompt_habits():
    """Collect the three weekly environmental habit counts from the user."""
    plastic_bottles = get_non_negative_int(
        "How many plastic bottles did you use this week? ",
        warn_above=WEEKLY_SANITY_LIMIT,
    )
    public_transport = get_non_negative_int(
        "How many times do you use public transport per week? ",
        warn_above=WEEKLY_SANITY_LIMIT,
    )
    recycling = get_non_negative_int(
        "How many times do you recycle per week? ",
        warn_above=WEEKLY_SANITY_LIMIT,
    )
    return plastic_bottles, public_transport, recycling


def format_record(record):
    """Format a single record for terminal display."""
    date_part = f" ({record['date']})" if record.get("date") else ""
    base = (
        f"Week {record['week']}{date_part}: "
        f"Score = {record['score']}, "
        f"Rating = {record['rating']}"
    )

    if (
        record.get("plastic_bottles") is not None
        and record.get("public_transport") is not None
        and record.get("recycling") is not None
    ):
        base += (
            f" [Bottles: {record['plastic_bottles']}, "
            f"Transport: {record['public_transport']}, "
            f"Recycling: {record['recycling']}]"
        )

    return base


def print_score_summary(plastic_bottles, public_transport, recycling, score, rating):
    """Print the calculated score, rating, and per-habit point breakdown."""
    breakdown = calculate_score_breakdown(plastic_bottles, public_transport, recycling)
    print(f"Your sustainability score is {score}.")
    print(
        f"Breakdown: Recycling {breakdown['recycling']:+d}, "
        f"Transport {breakdown['public_transport']:+d}, "
        f"Bottles {breakdown['plastic_bottles']:+d}"
    )
    print(f"Rating: {rating}")


def display_history_and_stats(records):
    """Print historical records and summary statistics."""
    print("\nYour history:")
    if not records:
        print("No records yet.")
    else:
        for record in records:
            print(format_record(record))

    statistics = calculate_statistics(records)
    trend = summarize_trend(records)
    if statistics is None:
        print("No statistics yet.")
    else:
        print("\nYour statistics:")
        print(f"Number of records: {statistics['count']}")
        print(f"Average score: {statistics['average']:.2f}")
        print(f"Highest score: {statistics['highest']}")
        print(f"Lowest score: {statistics['lowest']}")
        if trend and trend["delta_from_previous"] is not None:
            print(
                f"Latest change vs previous week: "
                f"{trend['delta_from_previous']:+d}"
            )


def export_report(records, output_path):
    """Export history and summary statistics to a readable text/Markdown report."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    statistics = calculate_statistics(records)

    lines = ["# Sustainability Score Report", ""]
    if statistics is None:
        lines.append("No records yet.")
    else:
        lines.extend([
            "## Summary Statistics",
            f"- Number of records: {statistics['count']}",
            f"- Average score: {statistics['average']:.2f}",
            f"- Highest score: {statistics['highest']}",
            f"- Lowest score: {statistics['lowest']}",
            "",
            "## Weekly History",
        ])
        for record in records:
            lines.append(f"- {format_record(record)}")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def handle_add_record(preset_habits=None, skip_confirm=False):
    """Collect or use preset habits, confirm before saving, and return saved habits or None."""
    while True:
        if preset_habits is not None:
            plastic_bottles, public_transport, recycling = preset_habits
        else:
            plastic_bottles, public_transport, recycling = prompt_habits()

        score = calculate_score(plastic_bottles, public_transport, recycling)
        rating = get_rating(score)
        print_score_summary(plastic_bottles, public_transport, recycling, score, rating)

        if not skip_confirm:
            choice = get_choice(
                "Save this record? [Y]es / [R]e-enter / [N]o (default: y): ",
                ["y", "r", "n"],
                default="y",
            )
            if choice == "r":
                preset_habits = None
                continue
            if choice == "n":
                print("Record not saved.")
                return None

        week = save_record(
            score,
            rating,
            plastic_bottles=plastic_bottles,
            public_transport=public_transport,
            recycling=recycling,
        )
        print(f"Week {week} record saved successfully!")
        return plastic_bottles, public_transport, recycling


def handle_edit_record():
    """Allow updating an existing week's habit inputs and score."""
    records = load_records()
    if not records:
        print("\nNo records available to edit.")
        return

    print("\nCurrent records:")
    for record in records:
        print(format_record(record))

    valid_weeks = {record["week"] for record in records}
    while True:
        target_week = get_non_negative_int(
            "\nEnter the week number to edit (0 to cancel): "
        )
        if target_week == 0:
            print("Edit cancelled.")
            return
        if target_week in valid_weeks:
            break
        print(f"Week {target_week} was not found.")

    plastic_bottles, public_transport, recycling = prompt_habits()
    score = calculate_score(plastic_bottles, public_transport, recycling)
    rating = get_rating(score)

    print(f"Updated score for Week {target_week}: {score} ({rating})")
    confirm = get_choice(
        "Confirm update? [Y]es / [N]o (default: y): ",
        ["y", "n"],
        default="y",
    )
    if confirm == "n":
        print("Update cancelled.")
        return

    updated = update_record_by_week(
        target_week,
        score,
        rating,
        plastic_bottles=plastic_bottles,
        public_transport=public_transport,
        recycling=recycling,
    )
    if updated:
        print(f"Week {target_week} record updated successfully!")


def handle_delete_record(mode=None, target_week=None, skip_confirm=False):
    """Allow undoing the last record or deleting a specific week."""
    records = load_records()
    if not records:
        print("\nNo records available to delete.")
        return

    if mode is None:
        print("\nCurrent records:")
        for record in records:
            print(format_record(record))

        mode = get_choice(
            "\nDelete [L]ast record / [W]eek number / [C]ancel (default: l): ",
            ["l", "w", "c"],
            default="l",
        )

    if mode == "c":
        print("Delete cancelled.")
        return

    if mode == "l":
        last_record = records[-1]
        if not skip_confirm:
            confirm = get_choice(
                f"Delete Week {last_record['week']}? [y/N]: ",
                ["y", "n"],
                default="n",
            )
            if confirm != "y":
                print("Delete cancelled.")
                return

        removed = delete_last_record()
        if removed:
            print(f"Week {removed['week']} record deleted.")
        return

    valid_weeks = {record["week"] for record in records}
    if target_week is None:
        while True:
            target_week = get_non_negative_int(
                "Enter the week number to delete (0 to cancel): "
            )
            if target_week == 0:
                print("Delete cancelled.")
                return
            if target_week in valid_weeks:
                break
            print(f"Week {target_week} was not found.")
    elif target_week not in valid_weeks:
        print(f"Week {target_week} was not found.")
        return

    if not skip_confirm:
        confirm = get_choice(
            f"Delete Week {target_week}? [y/N]: ",
            ["y", "n"],
            default="n",
        )
        if confirm != "y":
            print("Delete cancelled.")
            return

    removed = delete_record_by_week(target_week)
    if removed:
        print(f"Week {removed['week']} record deleted.")


def build_parser():
    """Build CLI argument parser for Sustainability Score Calculator."""
    parser = argparse.ArgumentParser(
        description="Track weekly sustainability habits, view statistics, and get AI advice."
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--history",
        action="store_true",
        help="View history, statistics, and chart without adding a new record.",
    )
    mode_group.add_argument(
        "--undo",
        action="store_true",
        help="Delete the most recent saved record.",
    )
    mode_group.add_argument(
        "--delete-week",
        type=int,
        metavar="WEEK",
        help="Delete the record for the specified week number.",
    )

    parser.add_argument("--bottles", type=int, help="Plastic bottles used this week (>= 0).")
    parser.add_argument("--transport", type=int, help="Public transport trips this week (>= 0).")
    parser.add_argument("--recycling", type=int, help="Recycling occasions this week (>= 0).")
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip generating Gemini AI advice.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip opening the Matplotlib chart window.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompts when saving or deleting.",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export history and statistics to a report file.",
    )
    parser.add_argument(
        "--save-chart",
        metavar="PATH",
        help="Save the score history chart as a PNG image.",
    )
    return parser


def _extract_preset_habits(parser, args):
    """Validate optional --bottles/--transport/--recycling CLI flags."""
    habit_flags = [args.bottles, args.transport, args.recycling]
    if all(v is None for v in habit_flags):
        return None
    if any(v is None for v in habit_flags):
        parser.error("Provide all three of --bottles, --transport, and --recycling together.")
    if any(v < 0 for v in habit_flags):
        parser.error("--bottles, --transport, and --recycling must be non-negative integers.")
    return args.bottles, args.transport, args.recycling


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    preset_habits = _extract_preset_habits(parser, args)

    if preset_habits is not None and (
        args.history or args.undo or args.delete_week is not None
    ):
        parser.error(
            "--bottles/--transport/--recycling cannot be combined with "
            "--history, --undo, or --delete-week."
        )

    habits = None
    if args.undo:
        handle_delete_record(mode="l", skip_confirm=args.yes)
    elif args.delete_week is not None:
        if args.delete_week <= 0:
            parser.error("--delete-week must be a positive integer.")
        handle_delete_record(mode="w", target_week=args.delete_week, skip_confirm=args.yes)
    elif args.history:
        pass
    elif preset_habits is not None:
        habits = handle_add_record(preset_habits=preset_habits, skip_confirm=args.yes)
    else:
        print("=== Sustainability Score Calculator ===")
        print("1. Add a new weekly record (default)")
        print("2. Edit an existing record")
        print("3. Delete / undo a record")
        print("4. View history, statistics & chart")

        action = get_choice(
            "Choose an option [1-4] (default: 1): ",
            ["1", "2", "3", "4"],
            default="1",
        )

        if action == "1":
            habits = handle_add_record(skip_confirm=args.yes)
        elif action == "2":
            handle_edit_record()
        elif action == "3":
            handle_delete_record(skip_confirm=args.yes)

    records = load_records()
    display_history_and_stats(records)

    if args.export:
        exported_path = export_report(records, args.export)
        print(f"\nReport exported to {exported_path}")

    if habits is not None and not args.no_ai:
        plastic_bottles, public_transport, recycling = habits
        score = calculate_score(plastic_bottles, public_transport, recycling)
        rating = get_rating(score)
        prompt = build_advice_prompt(
            plastic_bottles=plastic_bottles,
            public_transport=public_transport,
            recycling=recycling,
            score=score,
            rating=rating,
            history_records=records,
        )

        print("\nGenerating AI advice...")
        advice = generate_advice(prompt)

        print("\nAI advice:")
        print(advice)

    if args.save_chart or not args.no_plot:
        saved_chart = plot_history(
            records,
            save_path=args.save_chart,
            show=not args.no_plot,
        )
        if args.save_chart and saved_chart is not None:
            print(f"\nChart saved to {saved_chart}")


if __name__ == "__main__":
    main()
