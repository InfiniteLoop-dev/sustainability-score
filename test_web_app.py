import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from storage import save_record
from web_app import create_server


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = Path(self.temp_dir.name) / "history.csv"
        self.server = create_server(host="127.0.0.1", port=0, history_path=self.csv_path)
        self.port = self.server.server_address[1]
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def _request(self, method, path, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"} if body is not None else {}
        req = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, json.loads(raw) if raw.startswith("{") else raw
        except urllib.error.HTTPError as err:
            with err:
                raw = err.read().decode("utf-8")
                return err.code, json.loads(raw)

    def test_index_page_serves_html(self):
        req = urllib.request.Request(f"{self.base_url}/")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")
            self.assertIn("Sustainability Score Dashboard", html)

    def test_crud_records_and_statistics_lifecycle(self):
        status, data = self._request("GET", "/api/records")
        self.assertEqual(status, 200)
        self.assertEqual(data["records"], [])
        self.assertIsNone(data["statistics"])

        with patch("web_app.generate_advice", return_value="Use a reusable bottle."):
            status, created = self._request(
                "POST",
                "/api/records",
                {
                    "plastic_bottles": 4,
                    "public_transport": 6,
                    "recycling": 5,
                    "date": "2026-11-25",
                    "generate_ai": True,
                },
            )
        self.assertEqual(status, 201)
        self.assertEqual(created["week"], 1)
        self.assertEqual(created["records"][0]["score"], 12)
        self.assertEqual(created["records"][0]["rating"], "Good")
        self.assertEqual(created["advice"], "Use a reusable bottle.")
        self.assertEqual(created["statistics"]["count"], 1)

        status, updated = self._request(
            "PUT",
            "/api/records/1",
            {
                "plastic_bottles": 0,
                "public_transport": 8,
                "recycling": 7,
                "date": "2026-11-26",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["updated"]["score"], 22)
        self.assertEqual(updated["updated"]["rating"], "Excellent")

        status, deleted = self._request("DELETE", "/api/records/last")
        self.assertEqual(status, 200)
        self.assertEqual(deleted["removed"]["week"], 1)
        self.assertEqual(deleted["records"], [])

    def test_validation_and_not_found_errors(self):
        status, err = self._request(
            "POST",
            "/api/records",
            {"plastic_bottles": -1, "public_transport": 2, "recycling": 3},
        )
        self.assertEqual(status, 400)
        self.assertIn("non-negative integer", err["error"])

        status, err = self._request(
            "POST",
            "/api/records",
            {
                "plastic_bottles": 1,
                "public_transport": 2,
                "recycling": 3,
                "date": "not-a-date",
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("YYYY-MM-DD", err["error"])

        status, err = self._request("DELETE", "/api/records/99")
        self.assertEqual(status, 404)

    def test_advice_endpoint_and_delete_by_week(self):
        save_record(12, "Good", 4, 6, 5, "2026-11-20", file_path=self.csv_path)
        save_record(20, "Excellent", 0, 6, 7, "2026-11-25", file_path=self.csv_path)

        with patch("web_app.generate_advice", return_value="Mocked tip"):
            status, data = self._request(
                "POST",
                "/api/advice",
                {"plastic_bottles": 3, "public_transport": 4, "recycling": 2},
            )
        self.assertEqual(status, 200)
        self.assertEqual(data["advice"], "Mocked tip")

        status, data = self._request("DELETE", "/api/records/1")
        self.assertEqual(status, 200)
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0]["week"], 2)


if __name__ == "__main__":
    unittest.main()
