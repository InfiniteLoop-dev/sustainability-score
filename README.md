# 🌱 Sustainability Score Calculator

A Python application (CLI + lightweight Web Dashboard) that helps users track their weekly environmental habits, calculate a sustainability score, manage historical records, visualize progress, and receive trend-aware AI suggestions.

This project is part of my Python learning journey and preparation for a sustainability hackathon. The scoring formula is designed for learning and demonstration, rather than measuring real environmental impact.

## Features

- **Habit Tracking & Validation**: Collect weekly plastic bottle usage, public transport trips, and recycling occasions with non-negative integer checks and confirmation prompts for unusually high values (`> 50`).
- **Interactive CLI & Command-Line Flags**: Add, edit, undo/delete, or inspect records through an interactive menu, or automate workflows via `argparse` flags (`--bottles`, `--transport`, `--recycling`, `--history`, `--undo`, `--delete-week`, `--export`, `--save-chart`, `--no-ai`, `--no-plot`, `-y`/`--yes`).
- **Lightweight Web Dashboard**: Run `web_app.py` for a zero-extra-dependency browser UI with live score preview, KPI summary cards, interactive SVG trend chart, inline record editing/deletion, and AI advice.
- **Scoring Breakdown & Custom Weights**: Calculate total score, per-habit point breakdown, and qualitative rating (`Excellent`, `Good`, `Fair`, `Needs Improvement`), with extensible weights in `scoring.py`.
- **Resilient CSV Storage**: Save `week`, ISO `date`, habit inputs, `score`, and `rating` to `history.csv` (anchored to the project directory), with automatic migration of legacy 3-column CSVs, `max(week) + 1` numbering, UTF-8 BOM support, atomic writes, and graceful skipping of blank or malformed rows.
- **Statistics, Trend Analysis & Export**: Compute record count, average, highest, and lowest scores, track week-over-week score/habit changes, and export Markdown reports (`--export`).
- **Enhanced Visualization**: Plot score history with Matplotlib including `0` / `10` / `20` rating threshold reference lines, point value labels, smart x-axis ticks for long histories, and PNG export (`--save-chart`).
- **Trend-Aware Gemini AI Advice**: Generate two practical suggestions using the Gemini API based on current habits, score/rating, and recent history context, with `.env` support (`.env.example`) and graceful fallback when the API key is missing or a request fails.

## Scoring System

```text
score = recycling × 2 + public_transport − plastic_bottles
```

| Score | Rating |
|---|---|
| 20 or above | Excellent |
| 10–19 | Good |
| 0–9 | Fair |
| Below 0 | Needs Improvement |

All habit inputs must be non-negative integers. The calculated score can be negative. `scoring.py` also supports custom `weights` and an optional `reusable_items` parameter via `calculate_score` and `calculate_score_breakdown`.

## How to Run

1. Install Python (3.10+ recommended).
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. (Optional) Configure your Gemini API key as described below.

### Option 1: Command-Line Application

Run the interactive menu:

```bash
python main.py
```

Or use CLI flags directly:

```bash
# View history, statistics, and chart without adding a record
python main.py --history

# Log a week non-interactively without AI or GUI popup
python main.py --bottles 2 --transport 6 --recycling 5 --yes --no-ai --no-plot

# Export a Markdown report and save a PNG trend chart
python main.py --history --export report.md --save-chart trend.png --no-plot

# Undo the latest record or delete a specific week
python main.py --undo --yes --no-plot
python main.py --delete-week 3 --yes --no-plot
```

### Option 2: Lightweight Web Dashboard

Start the built-in web server and open the dashboard in your browser:

```bash
python web_app.py --open
```

By default, the dashboard runs at `http://127.0.0.1:8000` (customize with `--host` and `--port`).

### Configure the Gemini API Key

The AI advice feature is optional. Without an API key, both the CLI and Web Dashboard still calculate scores, manage records, show statistics, and draw charts; the AI advice section shows a message saying it is unavailable.

1. Create an API key in Google AI Studio.
2. Choose one of the following ways to provide `GEMINI_API_KEY`:
   - **Using `.env` (recommended for terminal/web usage)**: Copy `.env.example` to `.env` in the project root and set `GEMINI_API_KEY=your_key_here`. Existing terminal or IDE environment variables take precedence over `.env`.
   - **In PyCharm**: Open `Run → Edit Configurations → select main → Environment variables` and add `GEMINI_API_KEY`.
   - **In a terminal**: Export `GEMINI_API_KEY` in your shell environment before running `main.py` or `web_app.py`.

Do not put the key in source code or commit `.env` to Git (`.env` is listed in `.gitignore`).

API availability and usage limits depend on your account and selected model. When AI advice is requested, the application sends the weekly habit numbers, calculated score/rating, and aggregated recent trend context (without personal identifiers) to Google's Gemini API.

## Example (CLI)

```text
=== Sustainability Score Calculator ===
1. Add a new weekly record (default)
2. Edit an existing record
3. Delete / undo a record
4. View history, statistics & chart
Choose an option [1-4] (default: 1): 1
How many plastic bottles did you use this week? 4
How many times do you use public transport per week? 6
How many times do you recycle per week? 5
Your sustainability score is 12.
Breakdown: Recycling +10, Transport +6, Bottles -4
Rating: Good
Save this record? [Y]es / [R]e-enter / [N]o (default: y): y
Week 1 record saved successfully!

Your history:
Week 1 (2026-11-25): Score = 12, Rating = Good [Bottles: 4, Transport: 6, Recycling: 5]

Your statistics:
Number of records: 1
Average score: 12.00
Highest score: 12
Lowest score: 12
```

## AI Advice Design

The prompt in `ai_advice.py` provides the model with current habit counts, calculated score/rating, and (when available) recent history trend context, and enforces safety constraints:

- Do not invent carbon reduction figures.
- Do not assume public transport, campus facilities, or local recycling services are available; use conditional wording when unsure.
- Do not guarantee cost savings or environmental outcomes.

## Project Structure

```text
sustainability-score/
├── main.py              # CLI workflow, menu, argparse flags, and report export
├── web_app.py           # Built-in HTTP server and JSON REST API for the dashboard
├── web/
│   └── index.html       # Responsive Web Dashboard UI with SVG trend chart
├── input_utils.py       # Integer validation, high-value confirmation, and choice prompts
├── scoring.py           # Score calculation, per-habit breakdown, weights, and ratings
├── storage.py           # Resilient CSV storage, legacy migration, and edit/delete helpers
├── analysis.py          # Summary statistics and week-over-week trend analysis
├── visualization.py     # Matplotlib chart with thresholds, labels, and PNG export
├── ai_advice.py         # .env loader, trend-aware prompt building, and Gemini API client
├── test_storage.py      # Unit tests for CSV storage, migration, and main flow
├── test_cli.py          # Unit tests for CLI flags, input checks, and .env loading
├── test_upgrades.py     # Unit tests for scoring breakdown, trends, AI, and charts
├── test_web_app.py      # End-to-end HTTP API tests for the web dashboard
├── .env.example         # Example environment variable template
├── requirements.txt     # External dependencies
├── .gitignore           # Local data, secrets, and practice scripts kept out of Git
└── README.md            # Project documentation
```

## Data Storage

The application stores records in `history.csv` inside the project directory (created automatically on first save):

```csv
week,date,plastic_bottles,public_transport,recycling,score,rating
1,2026-11-25,4,6,5,12,Good
2,2026-12-02,1,7,7,20,Excellent
```

- New records increment `week` using `max(week) + 1`, preventing duplicate numbers if earlier rows are deleted.
- Existing legacy 3-column files (`week,score,rating`) are read seamlessly and automatically upgraded to the 7-column header on the next save.
- Blank or malformed CSV rows are skipped with a warning instead of crashing the program.
- Historical data is stored locally and ignored by Git (`history.csv` is listed in `.gitignore`).

## Running Tests

Run the full `unittest` suite:

```bash
python -m unittest discover -v
```

## Technologies

- Python (`csv`, `argparse`, `http.server`, `pathlib`, `unittest`)
- HTML / CSS / JavaScript / SVG (Web Dashboard)
- Matplotlib
- Gemini API (`google-genai`)
- Git and GitHub

## Future Improvements

- Support configuring custom habit weights and extra eco-habit categories directly in the CLI and Web UI.
- Add per-habit trend charts (bottles, transport, and recycling over time) alongside total score.
- Support multi-user profiles or separate tracking files.
