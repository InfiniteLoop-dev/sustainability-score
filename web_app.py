import argparse
import json
import re
import webbrowser
from datetime import date
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ai_advice import build_advice_prompt, generate_advice
from analysis import calculate_statistics
from scoring import calculate_score, calculate_score_breakdown, get_rating
from storage import (
    DEFAULT_HISTORY_PATH,
    delete_last_record,
    delete_record_by_week,
    load_records,
    save_record,
    update_record_by_week,
)

INDEX_HTML_PATH = Path(__file__).resolve().parent / "web" / "index.html"
MAX_BODY_BYTES = 64 * 1024
WEEK_ROUTE_RE = re.compile(r"^/api/records/(\d+)$")


def _parse_non_negative_int(payload, field_name):
    """Validate and return a non-negative integer field from JSON payload."""
    if field_name not in payload:
        raise ValueError(f"Missing required field: {field_name}")

    value = payload[field_name]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"'{field_name}' must be a non-negative integer.")
    return value


def _parse_optional_date(payload):
    """Validate optional ISO date string (YYYY-MM-DD)."""
    raw = payload.get("date")
    if raw is None or raw == "":
        return None
    if not isinstance(raw, str):
        raise ValueError("'date' must be a string in YYYY-MM-DD format.")
    try:
        return date.fromisoformat(raw.strip()).isoformat()
    except ValueError as exc:
        raise ValueError("'date' must be a valid YYYY-MM-DD date.") from exc


def _parse_habit_payload(payload):
    """Extract and validate the three weekly habit counts."""
    if not isinstance(payload, dict):
        raise ValueError("JSON body must be an object.")
    return (
        _parse_non_negative_int(payload, "plastic_bottles"),
        _parse_non_negative_int(payload, "public_transport"),
        _parse_non_negative_int(payload, "recycling"),
    )


class SustainabilityHandler(BaseHTTPRequestHandler):
    """HTTP request handler serving the dashboard UI and JSON API."""

    @property
    def history_path(self):
        return getattr(self.server, "history_path", DEFAULT_HISTORY_PATH)

    def log_message(self, format, *args):
        # Keep console output concise; errors still print via log_error.
        return

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status, html_bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header.") from exc

        if length <= 0:
            raise ValueError("Request body cannot be empty.")
        if length > MAX_BODY_BYTES:
            raise ValueError("Request body is too large.")

        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Request body must be valid JSON.") from exc

    def _state_payload(self, extra=None):
        records = load_records(self.history_path)
        data = {
            "records": records,
            "statistics": calculate_statistics(records),
        }
        if extra:
            data.update(extra)
        return data

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/" or path == "/index.html":
            try:
                html_bytes = INDEX_HTML_PATH.read_bytes()
            except OSError:
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "Web UI template could not be loaded."},
                )
                return
            self._send_html(HTTPStatus.OK, html_bytes)
            return

        if path == "/api/records":
            self._send_json(HTTPStatus.OK, self._state_payload())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def do_POST(self):
        path = self.path.split("?", 1)[0]

        try:
            payload = self._read_json_body()
            plastic_bottles, public_transport, recycling = _parse_habit_payload(payload)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        if path == "/api/advice":
            score = calculate_score(plastic_bottles, public_transport, recycling)
            rating = get_rating(score)
            history_records = load_records(self.history_path)
            prompt = build_advice_prompt(
                plastic_bottles=plastic_bottles,
                public_transport=public_transport,
                recycling=recycling,
                score=score,
                rating=rating,
                history_records=history_records,
            )
            advice = generate_advice(prompt)
            self._send_json(HTTPStatus.OK, {"advice": advice})
            return

        if path == "/api/records":
            try:
                record_date = _parse_optional_date(payload)
            except ValueError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return

            breakdown = calculate_score_breakdown(
                plastic_bottles, public_transport, recycling
            )
            score = breakdown["total"]
            rating = breakdown["rating"]
            week = save_record(
                score,
                rating,
                plastic_bottles=plastic_bottles,
                public_transport=public_transport,
                recycling=recycling,
                record_date=record_date,
                file_path=self.history_path,
            )

            extra = {"week": week, "breakdown": breakdown}
            if payload.get("generate_ai", False):
                history_records = load_records(self.history_path)
                prompt = build_advice_prompt(
                    plastic_bottles=plastic_bottles,
                    public_transport=public_transport,
                    recycling=recycling,
                    score=score,
                    rating=rating,
                    history_records=history_records,
                )
                extra["advice"] = generate_advice(prompt)

            self._send_json(HTTPStatus.CREATED, self._state_payload(extra))
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def do_PUT(self):
        path = self.path.split("?", 1)[0]
        match = WEEK_ROUTE_RE.match(path)
        if not match:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})
            return

        week = int(match.group(1))
        if week <= 0:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "Week number must be positive."},
            )
            return

        try:
            payload = self._read_json_body()
            plastic_bottles, public_transport, recycling = _parse_habit_payload(payload)
            record_date = _parse_optional_date(payload)
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            return

        score = calculate_score(plastic_bottles, public_transport, recycling)
        rating = get_rating(score)
        updated = update_record_by_week(
            week,
            score,
            rating,
            plastic_bottles=plastic_bottles,
            public_transport=public_transport,
            recycling=recycling,
            record_date=record_date,
            file_path=self.history_path,
        )

        if updated is None:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {"error": f"Week {week} record not found."},
            )
            return

        self._send_json(HTTPStatus.OK, self._state_payload({"updated": updated}))

    def do_DELETE(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/records/last":
            removed = delete_last_record(file_path=self.history_path)
            if removed is None:
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "No records available to delete."},
                )
                return
            self._send_json(HTTPStatus.OK, self._state_payload({"removed": removed}))
            return

        match = WEEK_ROUTE_RE.match(path)
        if match:
            week = int(match.group(1))
            removed = delete_record_by_week(week, file_path=self.history_path)
            if removed is None:
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": f"Week {week} record not found."},
                )
                return
            self._send_json(HTTPStatus.OK, self._state_payload({"removed": removed}))
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})


def create_server(host="127.0.0.1", port=8000, history_path=DEFAULT_HISTORY_PATH):
    """Create and configure a ThreadingHTTPServer for the web app."""
    server = ThreadingHTTPServer((host, port), SustainabilityHandler)
    server.history_path = Path(history_path)
    return server


def main():
    parser = argparse.ArgumentParser(
        description="Run the Sustainability Score Calculator web dashboard."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically open the dashboard in your default browser.",
    )
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port)
    actual_host, actual_port = server.server_address
    url = f"http://{actual_host}:{actual_port}"
    print(f"Sustainability Score web dashboard running at {url}")
    print("Press Ctrl+C to stop.")

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
