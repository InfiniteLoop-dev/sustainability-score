import csv


def save_record(score, rating):
    with open("history.csv", "a+", newline="", encoding="utf-8") as file:
        file.seek(0)
        reader = csv.reader(file)
        rows = list(reader)

        writer = csv.writer(file)

        if len(rows) == 0:
            writer.writerow(["week", "score", "rating"])
            next_week = 1
        else:
            next_week = len(rows)

        writer.writerow([next_week, score, rating])

    return next_week

def load_records():
        try:
            with open("history.csv", "r", newline="", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader, None)

                records = []

                for row in reader:
                    record = {
                        "week": int(row[0]),
                        "score": int(row[1]),
                        "rating": row[2]
                    }
                    records.append(record)

                return records

        except FileNotFoundError:
            return []