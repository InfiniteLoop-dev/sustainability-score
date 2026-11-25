import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import ai_advice
import main
from analysis import summarize_trend
from scoring import calculate_score, calculate_score_breakdown, get_rating
from storage import load_records, save_record
from visualization import _select_xticks, plot_history


class ScoringUpgradeTests(unittest.TestCase):
    def test_breakdown_and_custom_weights_and_reusable_items(self):
        breakdown = calculate_score_breakdown(3, 4, 5, reusable_items=2)
        self.assertEqual(breakdown["plastic_bottles"], -3)
        self.assertEqual(breakdown["public_transport"], 4)
        self.assertEqual(breakdown["recycling"], 10)
        self.assertEqual(breakdown["reusable_items"], 2)
        self.assertEqual(breakdown["total"], 13)
        self.assertEqual(breakdown["rating"], "Good")

        custom_score = calculate_score(
            2, 3, 4, weights={"recycling": 3, "plastic_bottles": -2}
        )
        self.assertEqual(custom_score, 4 * 3 + 3 - 2 * 2)
        self.assertEqual(get_rating(20), "Excellent")
        self.assertEqual(get_rating(10), "Good")
        self.assertEqual(get_rating(0), "Fair")
        self.assertEqual(get_rating(-1), "Needs Improvement")


class AnalysisTrendTests(unittest.TestCase):
    def test_summarize_trend_empty_and_multi_week(self):
        self.assertIsNone(summarize_trend([]))

        records = [
            {
                "week": 1,
                "plastic_bottles": 5,
                "public_transport": 3,
                "recycling": 2,
                "score": 2,
                "rating": "Fair",
            },
            {
                "week": 2,
                "plastic_bottles": 2,
                "public_transport": 6,
                "recycling": 6,
                "score": 16,
                "rating": "Good",
            },
        ]
        trend = summarize_trend(records)
        self.assertEqual(trend["delta_from_previous"], 14)
        self.assertEqual(trend["habit_deltas"]["plastic_bottles"], -3)
        self.assertEqual(trend["habit_deltas"]["public_transport"], 3)
        self.assertEqual(trend["habit_deltas"]["recycling"], 4)


class AiAdviceUpgradeTests(unittest.TestCase):
    def test_build_prompt_includes_score_rating_and_history_context(self):
        history = [
            {
                "week": 1,
                "plastic_bottles": 6,
                "public_transport": 2,
                "recycling": 2,
                "score": 0,
                "rating": "Fair",
            },
            {
                "week": 2,
                "plastic_bottles": 2,
                "public_transport": 5,
                "recycling": 6,
                "score": 15,
                "rating": "Good",
            },
        ]
        prompt = ai_advice.build_advice_prompt(
            plastic_bottles=2,
            public_transport=5,
            recycling=6,
            score=15,
            rating="Good",
            history_records=history,
        )
        self.assertIn("Calculated sustainability score: 15 (Rating: Good)", prompt)
        self.assertIn("Recent history context:", prompt)
        self.assertIn("change vs previous week: +15", prompt)
        self.assertIn("Plastic bottles change vs previous week: -4", prompt)

    def test_generate_advice_handles_unexpected_exception_gracefully(self):
        with patch("ai_advice.os.getenv", return_value="fake-key"), patch(
            "ai_advice.genai.Client", side_effect=RuntimeError("boom")
        ):
            msg = ai_advice.generate_advice("test prompt")
        self.assertIn("unexpected error", msg)


class VisualizationUpgradeTests(unittest.TestCase):
    def test_select_xticks_caps_dense_labels_and_keeps_last_week(self):
        weeks = list(range(1, 31))
        ticks = _select_xticks(weeks, max_ticks=10)
        self.assertLessEqual(len(ticks), 11)
        self.assertEqual(ticks[0], 1)
        self.assertEqual(ticks[-1], 30)

    def test_plot_history_saves_png_without_showing_window(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "history.csv"
            chart_path = Path(tmp_dir) / "charts" / "trend.png"
            save_record(10, "Good", 2, 4, 4, "2026-11-01", file_path=csv_path)
            save_record(20, "Excellent", 0, 6, 7, "2026-11-08", file_path=csv_path)

            records = load_records(csv_path)
            saved = plot_history(records, save_path=chart_path, show=False)
            self.assertEqual(saved, chart_path)
            self.assertTrue(chart_path.is_file())
            self.assertGreater(chart_path.stat().st_size, 0)

    def test_cli_save_chart_flag_saves_image_with_no_plot(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "history.csv"
            chart_path = Path(tmp_dir) / "cli_chart.png"
            save_record(12, "Good", 4, 6, 5, "2026-11-01", file_path=csv_path)

            with patch("main.load_records", return_value=load_records(csv_path)):
                buf = io.StringIO()
                with redirect_stdout(buf):
                    main.main(
                        ["--history", "--no-plot", "--save-chart", str(chart_path)]
                    )
            self.assertTrue(chart_path.is_file())
            self.assertIn("Chart saved to", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
