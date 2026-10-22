def get_non_negative_int(prompt):
    while True:
        try:
            value = int(input(prompt))

            if value < 0:
                print("The number cannot be negative.")
            else:
                return value

        except ValueError:
            print("Please enter an integer.")