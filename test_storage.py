import csv
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import main
from analysis import calculate_statistics
from storage import (
    CSV_HEADERS,
    DEFAULT_HISTORY_PATH,
    delete_last_record,
    delete_record_by_week,
    load_records,
    save_record,
    update_record_by_week,
)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "history.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_history_path_is_fixed_to_project_dir(self):
        self.assertEqual(
            DEFAULT_HISTORY_PATH,
            Path(__file__).resolve().parent / "history.csv",
        )

    def test_load_records_returns_empty_when_file_missing(self):
        self.assertEqual(load_records(self.csv_path), [])

    def test_save_and_load_record_with_habits_and_date(self):
        week = save_record(
            score=12,
            rating="Good",
            plastic_bottles=4,
            public_transport=6,
            recycling=5,
            record_date="2026-11-25",
            file_path=self.csv_path,
        )
        self.assertEqual(week, 1)

        records = load_records(self.csv_path)
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0],
            {
                "week": 1,
                "date": "2026-11-25",
                "plastic_bottles": 4,
                "public_transport": 6,
                "recycling": 5,
                "score": 12,
                "rating": "Good",
            },
        )

    def test_save_migrates_legacy_csv_and_handles_missing_trailing_newline(self):
        # Simulate legacy 3-column CSV without a trailing newline
        self.csv_path.write_text(
            "week,score,rating\n1,12,Good\n2,20,Excellent",
            encoding="utf-8",
        )

        week = save_record(
            score=14,
            rating="Good",
            plastic_bottles=2,
            public_transport=6,
            recycling=5,
            record_date="2026-11-25",
            file_path=self.csv_path,
        )
        self.assertEqual(week, 3)

        with open(self.csv_path, "r", newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))

        self.assertEqual(rows[0], CSV_HEADERS)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[1], ["1", "", "", "", "", "12", "Good"])
        self.assertEqual(rows[3], ["3", "2026-11-25", "2", "6", "5", "14", "Good"])

        records = load_records(self.csv_path)
        self.assertEqual(len(records), 3)
        self.assertIsNone(records[0]["date"])
        self.assertIsNone(records[0]["plastic_bottles"])
        self.assertEqual(records[2]["plastic_bottles"], 2)

    def test_load_records_skips_blank_and_malformed_rows_and_reads_bom(self):
        content = (
            "\ufeffweek,score,rating\n"
            "\n"
            "1,12,Good\n"
            "bad,15,Good\n"
            "2,not_an_int,Fair\n"
            "3,10,\n"
            "4,18\n"
            "5,22,Excellent\n"
        )
        self.csv_path.write_text(content, encoding="utf-8")

        buf = io.StringIO()
        with redirect_stdout(buf):
            records = load_records(self.csv_path)

        self.assertEqual(len(records), 2)
        self.assertEqual([r["week"] for r in records], [1, 5])
        self.assertIn("Warning: skipped malformed record", buf.getvalue())

        # Next week should be max(week) + 1 = 6, not len(rows)
        next_week = save_record(
            score=8,
            rating="Fair",
            plastic_bottles=5,
            public_transport=3,
            recycling=5,
            record_date="2026-11-25",
            file_path=self.csv_path,
        )
        self.assertEqual(next_week, 6)

    def test_next_week_uses_max_after_deletion(self):
        save_record(10, "Good", 1, 3, 4, "2026-11-01", file_path=self.csv_path)
        save_record(15, "Good", 1, 5, 5, "2026-11-08", file_path=self.csv_path)
        save_record(20, "Excellent", 0, 6, 7, "2026-11-15", file_path=self.csv_path)

        removed = delete_record_by_week(2, file_path=self.csv_path)
        self.assertIsNotNone(removed)
        self.assertEqual(removed["week"], 2)

        # Remaining weeks are 1 and 3, so next week must be 4 (not 3!)
        next_week = save_record(
            12, "Good", 2, 4, 5, "2026-11-25", file_path=self.csv_path
        )
        self.assertEqual(next_week, 4)

    def test_delete_last_record_and_update_record_by_week(self):
        save_record(10, "Good", 2, 4, 4, "2026-11-01", file_path=self.csv_path)
        save_record(2, "Fair", 8, 2, 4, "2026-11-08", file_path=self.csv_path)

        updated = update_record_by_week(
            week=1,
            score=21,
            rating="Excellent",
            plastic_bottles=1,
            public_transport=8,
            recycling=7,
            record_date="2026-11-02",
            file_path=self.csv_path,
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated["score"], 21)
        self.assertEqual(updated["rating"], "Excellent")
        self.assertEqual(updated["date"], "2026-11-02")

        removed = delete_last_record(file_path=self.csv_path)
        self.assertEqual(removed["week"], 2)

        remaining = load_records(self.csv_path)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["score"], 21)

        stats = calculate_statistics(remaining)
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["average"], 21.0)

    def test_delete_and_update_missing_week_return_none(self):
        self.assertIsNone(delete_last_record(file_path=self.csv_path))
        self.assertIsNone(delete_record_by_week(99, file_path=self.csv_path))
        self.assertIsNone(
            update_record_by_week(99, 10, "Good", file_path=self.csv_path)
        )


class MainFlowTests(unittest.TestCase):
    def test_add_record_reenter_then_save(self):
        with patch("main.get_choice", side_effect=["1", "r", "y"]), patch(
            "main.get_non_negative_int", side_effect=[99, 1, 1, 2, 4, 5]
        ), patch("main.save_record", return_value=8) as mock_save, patch(
            "main.load_records",
            return_value=[
                {
                    "week": 8,
                    "date": "2026-11-25",
                    "plastic_bottles": 2,
                    "public_transport": 4,
                    "recycling": 5,
                    "score": 12,
                    "rating": "Good",
                }
            ],
        ), patch(
            "main.generate_advice", return_value="Mock advice"
        ), patch(
            "main.plot_history"
        ) as mock_plot:
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.main([])

            mock_save.assert_called_once_with(
                12,
                "Good",
                plastic_bottles=2,
                public_transport=4,
                recycling=5,
            )
            mock_plot.assert_called_once()
            self.assertIn("Week 8 (2026-11-25)", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
