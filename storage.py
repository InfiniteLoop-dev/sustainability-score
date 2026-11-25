import csv
import os
import tempfile
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_HISTORY_PATH = BASE_DIR / "history.csv"

CSV_HEADERS = [
    "week",
    "date",
    "plastic_bottles",
    "public_transport",
    "recycling",
    "score",
    "rating",
]
LEGACY_HEADERS = ["week", "score", "rating"]


def _parse_optional_non_negative_int(value, field_name):
    """Parse an optional non-negative integer field from CSV."""
    text = value.strip()
    if text == "":
        return None

    parsed = int(text)
    if parsed < 0:
        raise ValueError(f"{field_name} cannot be negative")
    return parsed


def _is_header_row(row):
    """Return True if the CSV row looks like a header row."""
    cleaned = [cell.strip().lower() for cell in row]
    return (
        len(cleaned) == len(set(cleaned))
        and {"week", "score", "rating"}.issubset(cleaned)
    )


def _parse_row(row, header_map=None):
    """Parse a single CSV data row into a normalized record dict."""
    if header_map is not None:
        if len(row) != len(header_map):
            raise ValueError("column count does not match header")

        by_name = {col: row[idx] for col, idx in header_map.items()}
        week = int(by_name["week"].strip())
        if week <= 0:
            raise ValueError("week must be positive")

        score = int(by_name["score"].strip())
        rating = by_name["rating"].strip()
        if not rating:
            raise ValueError("rating cannot be empty")

        raw_date = by_name.get("date", "").strip()
        record_date = raw_date if raw_date else None

        plastic_bottles = _parse_optional_non_negative_int(
            by_name.get("plastic_bottles", ""), "plastic_bottles"
        )
        public_transport = _parse_optional_non_negative_int(
            by_name.get("public_transport", ""), "public_transport"
        )
        recycling = _parse_optional_non_negative_int(
            by_name.get("recycling", ""), "recycling"
        )
    elif len(row) == len(LEGACY_HEADERS):
        week = int(row[0].strip())
        if week <= 0:
            raise ValueError("week must be positive")
        score = int(row[1].strip())
        rating = row[2].strip()
        if not rating:
            raise ValueError("rating cannot be empty")

        record_date = None
        plastic_bottles = None
        public_transport = None
        recycling = None
    elif len(row) == len(CSV_HEADERS):
        week = int(row[0].strip())
        if week <= 0:
            raise ValueError("week must be positive")
        raw_date = row[1].strip()
        record_date = raw_date if raw_date else None
        plastic_bottles = _parse_optional_non_negative_int(row[2], "plastic_bottles")
        public_transport = _parse_optional_non_negative_int(row[3], "public_transport")
        recycling = _parse_optional_non_negative_int(row[4], "recycling")
        score = int(row[5].strip())
        rating = row[6].strip()
        if not rating:
            raise ValueError("rating cannot be empty")
    else:
        raise ValueError(f"unexpected column count ({len(row)})")

    return {
        "week": week,
        "date": record_date,
        "plastic_bottles": plastic_bottles,
        "public_transport": public_transport,
        "recycling": recycling,
        "score": score,
        "rating": rating,
    }


def _record_to_row(record):
    """Convert a record dict into a CSV row aligned with CSV_HEADERS."""
    return [
        record["week"],
        "" if record.get("date") is None else record["date"],
        "" if record.get("plastic_bottles") is None else record["plastic_bottles"],
        "" if record.get("public_transport") is None else record["public_transport"],
        "" if record.get("recycling") is None else record["recycling"],
        record["score"],
        record["rating"],
    ]


def _write_records(records, file_path=DEFAULT_HISTORY_PATH):
    """Atomically write all records to CSV with the standard header."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        dir=str(target.parent),
        prefix=f".{target.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(CSV_HEADERS)
            for record in records:
                writer.writerow(_record_to_row(record))
        os.replace(temp_name, target)
    except Exception:
        if os.path.exists(temp_name):
            os.remove(temp_name)
        raise


def _read_header(file_path):
    """Return the first non-empty row of a CSV file, or None if empty/missing."""
    target = Path(file_path)
    if not target.exists():
        return None

    with open(target, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        for row in reader:
            if row and any(cell.strip() for cell in row):
                return [cell.strip().lower() for cell in row]
    return None


def _ensure_trailing_newline(file_path):
    """Ensure an existing non-empty file ends with a newline before appending."""
    target = Path(file_path)
    if not target.exists() or target.stat().st_size == 0:
        return

    with open(target, "rb+") as file:
        file.seek(-1, os.SEEK_END)
        last_byte = file.read(1)
        if last_byte not in (b"\n", b"\r"):
            file.write(b"\n")


def load_records(file_path=DEFAULT_HISTORY_PATH):
    """Load valid historical records from CSV, skipping blank or malformed rows."""
    target = Path(file_path)

    try:
        with open(target, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            records = []
            header_map = None
            checked_first_row = False

            for line_number, row in enumerate(reader, start=1):
                if not row or all(not cell.strip() for cell in row):
                    continue

                if not checked_first_row:
                    checked_first_row = True
                    if _is_header_row(row):
                        header_map = {
                            cell.strip().lower(): idx for idx, cell in enumerate(row)
                        }
                        continue

                try:
                    records.append(_parse_row(row, header_map=header_map))
                except ValueError as error:
                    print(
                        f"Warning: skipped malformed record at line {line_number} "
                        f"({error})."
                    )

            return records
    except FileNotFoundError:
        return []
    except (UnicodeDecodeError, OSError) as error:
        print(f"Warning: could not read {target} ({error}).")
        return []


def save_record(
    score,
    rating,
    plastic_bottles=None,
    public_transport=None,
    recycling=None,
    record_date=None,
    file_path=DEFAULT_HISTORY_PATH,
):
    """Save a new record to CSV and return its assigned week number."""
    target = Path(file_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    existing_records = load_records(target)
    next_week = max((record["week"] for record in existing_records), default=0) + 1

    new_record = {
        "week": next_week,
        "date": date.today().isoformat() if record_date is None else record_date,
        "plastic_bottles": plastic_bottles,
        "public_transport": public_transport,
        "recycling": recycling,
        "score": score,
        "rating": rating,
    }

    current_header = None
    try:
        current_header = _read_header(target)
    except (UnicodeDecodeError, OSError):
        current_header = None

    if current_header is None:
        _write_records([new_record], target)
    elif current_header != CSV_HEADERS:
        # Upgrade legacy or headerless CSV files so all rows share CSV_HEADERS.
        _write_records(existing_records + [new_record], target)
    else:
        _ensure_trailing_newline(target)
        with open(target, "a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(_record_to_row(new_record))

    return next_week


def delete_last_record(file_path=DEFAULT_HISTORY_PATH):
    """Remove and return the last saved record, or None if no records exist."""
    target = Path(file_path)
    records = load_records(target)
    if not records:
        return None

    removed = records.pop()
    _write_records(records, target)
    return removed


def delete_record_by_week(week, file_path=DEFAULT_HISTORY_PATH):
    """Remove and return the record matching week, or None if not found."""
    target = Path(file_path)
    records = load_records(target)

    for idx, record in enumerate(records):
        if record["week"] == week:
            removed = records.pop(idx)
            _write_records(records, target)
            return removed

    return None


def update_record_by_week(
    week,
    score,
    rating,
    plastic_bottles=None,
    public_transport=None,
    recycling=None,
    record_date=None,
    file_path=DEFAULT_HISTORY_PATH,
):
    """Update an existing record matching week and return it, or None if not found."""
    target = Path(file_path)
    records = load_records(target)

    for record in records:
        if record["week"] == week:
            record["score"] = score
            record["rating"] = rating
            record["plastic_bottles"] = plastic_bottles
            record["public_transport"] = public_transport
            record["recycling"] = recycling
            if record_date is not None:
                record["date"] = record_date
            elif record.get("date") is None:
                record["date"] = date.today().isoformat()

            _write_records(records, target)
            return record

    return None
