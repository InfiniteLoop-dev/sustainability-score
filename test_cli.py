import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import ai_advice
import input_utils
import main
from storage import load_records, save_record


class InputUtilsTests(unittest.TestCase):
    def test_get_non_negative_int_warns_and_reprompts_on_high_value(self):
        with patch("builtins.input", side_effect=["-1", "abc", "200", "n", "5"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            value = input_utils.get_non_negative_int("Enter count: ", warn_above=50)
        self.assertEqual(value, 5)

    def test_get_non_negative_int_accepts_high_value_when_confirmed(self):
        with patch("builtins.input", side_effect=["120", "y"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            value = input_utils.get_non_negative_int("Enter count: ", warn_above=50)
        self.assertEqual(value, 120)


class EnvLoadingTests(unittest.TestCase):
    def test_load_env_file_parses_values_without_overriding_existing_env(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / ".env"
            env_file.write_text(
                "# Comment line\n"
                "\n"
                "export GEMINI_API_KEY='from-dotenv'\n"
                'OTHER_VAR="hello world"\n',
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"OTHER_VAR": "already-set"}, clear=True):
                loaded = ai_advice.load_env_file(env_file)
                self.assertTrue(loaded)
                self.assertEqual(os.environ.get("GEMINI_API_KEY"), "from-dotenv")
                self.assertEqual(os.environ.get("OTHER_VAR"), "already-set")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "history.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _run_main(self, argv):
        def _load():
            return load_records(self.csv_path)

        def _save(score, rating, **kwargs):
            return save_record(score, rating, file_path=self.csv_path, **kwargs)

        def _delete_last():
            from storage import delete_last_record

            return delete_last_record(file_path=self.csv_path)

        def _delete_week(week):
            from storage import delete_record_by_week

            return delete_record_by_week(week, file_path=self.csv_path)

        with patch("main.load_records", side_effect=_load), patch(
            "main.save_record", side_effect=_save
        ), patch("main.delete_last_record", side_effect=_delete_last), patch(
            "main.delete_record_by_week", side_effect=_delete_week
        ), patch("main.plot_history") as mock_plot:
            buf = io.StringIO()
            with redirect_stdout(buf):
                main.main(argv)
            return buf.getvalue(), mock_plot

    def test_cli_add_export_history_and_undo_flags(self):
        out, mock_plot = self._run_main(
            [
                "--bottles",
                "2",
                "--transport",
                "4",
                "--recycling",
                "5",
                "--yes",
                "--no-ai",
                "--no-plot",
            ]
        )
        mock_plot.assert_not_called()
        self.assertIn("Breakdown: Recycling +10, Transport +4, Bottles -2", out)
        self.assertIn("Week 1 record saved successfully!", out)

        report_path = Path(self.temp_dir.name) / "report.md"
        out, mock_plot = self._run_main(
            ["--history", "--export", str(report_path), "--no-plot"]
        )
        mock_plot.assert_not_called()
        self.assertTrue(report_path.is_file())
        report_text = report_path.read_text(encoding="utf-8")
        self.assertIn("# Sustainability Score Report", report_text)
        self.assertIn("Week 1", report_text)

        out, _ = self._run_main(["--undo", "--yes", "--no-plot"])
        self.assertIn("Week 1 record deleted.", out)
        self.assertEqual(load_records(self.csv_path), [])

    def test_cli_delete_specific_week(self):
        save_record(10, "Good", 2, 4, 4, "2026-11-01", file_path=self.csv_path)
        save_record(20, "Excellent", 0, 6, 7, "2026-11-08", file_path=self.csv_path)

        out, _ = self._run_main(["--delete-week", "1", "--yes", "--no-plot"])
        self.assertIn("Week 1 record deleted.", out)
        remaining = load_records(self.csv_path)
        self.assertEqual([r["week"] for r in remaining], [2])

    def test_cli_rejects_partial_or_conflicting_flags(self):
        with patch("sys.stderr", new_callable=io.StringIO):
            with self.assertRaises(SystemExit):
                main.main(["--bottles", "2"])
            with self.assertRaises(SystemExit):
                main.main(
                    [
                        "--history",
                        "--bottles",
                        "2",
                        "--transport",
                        "3",
                        "--recycling",
                        "4",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
