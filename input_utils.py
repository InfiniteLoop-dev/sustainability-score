def get_non_negative_int(prompt, warn_above=None):
    """Prompt until the user enters a non-negative integer, confirming unusually high values."""
    while True:
        try:
            value = int(input(prompt))

            if value < 0:
                print("The number cannot be negative.")
                continue

            if warn_above is not None and value > warn_above:
                confirm = get_choice(
                    f"You entered {value}, which seems unusually high for one week. "
                    "Keep this value? [y/N]: ",
                    ["y", "n"],
                    default="n",
                )
                if confirm != "y":
                    continue

            return value

        except ValueError:
            print("Please enter an integer.")


def get_choice(prompt, valid_choices, default=None):
    """Prompt until the user picks one of valid_choices (case-insensitive)."""
    normalized = {choice.lower() for choice in valid_choices}

    while True:
        raw = input(prompt).strip().lower()

        if raw == "" and default is not None:
            return default.lower()

        if raw in normalized:
            return raw

        choices_display = "/".join(valid_choices)
        print(f"Please enter one of: {choices_display}.")