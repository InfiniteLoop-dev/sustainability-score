import os
from pathlib import Path
from google import genai
from google.genai.errors import APIError, ContinuationInterruptedError

from analysis import summarize_trend
from scoring import calculate_score, get_rating

try:
    from google.genai._interactions import (
        APIConnectionError,
        APIStatusError,
        APITimeoutError,
    )
except ImportError:
    APIConnectionError = ()
    APIStatusError = ()
    APITimeoutError = ()

DEFAULT_ENV_PATH = Path(__file__).resolve().parent / ".env"


def load_env_file(env_path=DEFAULT_ENV_PATH):
    """Load KEY=VALUE pairs from a local .env file without overriding existing env vars."""
    target = Path(env_path)
    if not target.is_file():
        return False

    try:
        content = target.read_text(encoding="utf-8-sig")
    except OSError:
        return False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        os.environ.setdefault(key, value)

    return True


def _format_history_context(history_records):
    """Build a concise trend summary block for the AI prompt."""
    trend = summarize_trend(history_records)
    if trend is None:
        return ""

    lines = [
        "",
        "Recent history context:",
        f"- Recorded weeks: {trend['count']}",
        f"- Historical average score: {trend['average']:.2f}",
    ]

    if trend["previous_score"] is not None:
        diff = trend["delta_from_previous"]
        sign = "+" if diff >= 0 else ""
        lines.append(
            f"- Previous week score: {trend['previous_score']} "
            f"(change vs previous week: {sign}{diff})"
        )

    habit_labels = {
        "plastic_bottles": "Plastic bottles change vs previous week",
        "public_transport": "Public transport trips change vs previous week",
        "recycling": "Recycling occasions change vs previous week",
    }
    for field, label in habit_labels.items():
        if field in trend["habit_deltas"]:
            diff = trend["habit_deltas"][field]
            sign = "+" if diff >= 0 else ""
            lines.append(f"- {label}: {sign}{diff}")

    return "\n".join(lines) + "\n"


def build_advice_prompt(
    plastic_bottles,
    public_transport,
    recycling,
    score=None,
    rating=None,
    history_records=None,
):
    """Build a constrained prompt including weekly habits, score, and optional history trend."""
    if score is None:
        score = calculate_score(plastic_bottles, public_transport, recycling)
    if rating is None:
        rating = get_rating(score)

    history_block = _format_history_context(history_records) if history_records else ""

    return f"""
You are helping a university student improve their environmental habits.

Their weekly habits:
- Plastic bottles used: {plastic_bottles}
- Public transport trips: {public_transport}
- Recycling occasions: {recycling}
- Calculated sustainability score: {score} (Rating: {rating})
{history_block}
Give two practical suggestions based on these habits.
Keep each suggestion within two sentences.
Do not assume public transport is always available.
Do not invent carbon reduction figures.

Do not assume campus facilities or local recycling services are available.
Use conditional wording when availability is unknown.
Do not guarantee cost savings or environmental outcomes.
"""


def generate_advice(prompt):
    """Request two habit suggestions from Gemini, degrading gracefully on errors."""
    load_env_file()
    if not os.getenv("GEMINI_API_KEY"):
        return "AI advice unavailable: API key is not configured."

    try:
        with genai.Client() as client:
            response = client.interactions.create(
                model="gemini-3.8-flash",
                input=prompt,
                timeout=15,
            )

            return response.output_text or "No advice was returned."

    except ContinuationInterruptedError:
        return "AI advice unavailable: generation was interrupted. Please try again later."

    except APITimeoutError:
        return "AI advice unavailable: the request timed out. Please try again later."

    except APIConnectionError:
        return "AI advice unavailable: could not connect to the service. Please try again later."

    except APIStatusError as error:
        if getattr(error, "status_code", None) == 429:
            return "AI advice unavailable: rate or quota limit reached. Please try again later."
        return "AI advice unavailable: the API request failed. Please try again later."

    except APIError as error:
        if getattr(error, "code", None) == 429:
            return "AI advice unavailable: rate or quota limit reached. Please try again later."
        return "AI advice unavailable: the API request failed. Please try again later."

    except Exception:
        return "AI advice unavailable: an unexpected error occurred. Please try again later."
