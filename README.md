# 🌱 Sustainability Score Calculator

A Python application that helps users track their environmental habits, calculate a sustainability score, and visualize their progress.

This project is part of my Python learning journey and preparation for a sustainability hackathon. The scoring formula is designed for learning and demonstration, rather than measuring real environmental impact.

## Features

- Collect weekly plastic bottle usage, public transport usage, and recycling frequency.
- Validate input and prompt users to retry invalid or negative values.
- Calculate a sustainability score and assign a rating.
- Save scores and ratings to a CSV file with automatic record numbering.
- Display historical records.
- Calculate the average, highest, and lowest scores.
- Display a line chart of score history using Matplotlib.
- Generate personalized environmental advice using the Gemini API.
- Show a helpful message when the API key is missing or an API error occurs.

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

All three inputs must be non-negative integers. The calculated score can be negative.

## How to Run

1. Install Python.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Configure your Gemini API key as described below.
6. Run the application:

   ```bash
   python main.py
   ```

A chart window will open after the results are displayed.
Close the chart window to finish the program.

### Configure the Gemini API key

Create an API key in Google AI Studio.

In PyCharm, open:
Run → Edit Configurations → select main → Environment variables.

Add an environment variable named `GEMINI_API_KEY` and paste your
key into its value field. Save the configuration and run main
using that configuration.

The PyCharm setting applies to that run configuration.
To run `python main.py` from a terminal, configure
`GEMINI_API_KEY` in the terminal environment separately.

Do not put the key in source code or commit it to Git.

API availability and usage limits depend on your account and selected model.
The application sends the environmental habit inputs to Google's Gemini API.

## Example

```text
How many plastic bottles did you use this week? 4
How many times do you use public transport per week? 6
How many times do you recycle per week? 5
Your sustainability score is 12.
Rating: Good
Week 1 record saved successfully!

Your history:
Week 1: Score = 12, Rating = Good

Your statistics:
Number of records: 1
Average score: 12.00
Highest score: 12
Lowest score: 12
```

The application also displays a chart based on the saved history.

## Project Structure

```text
sustainability-score/
├── main.py              # Main application workflow
├── input_utils.py       # Input validation
├── scoring.py           # Score calculation and ratings
├── storage.py           # CSV saving and loading
├── analysis.py          # Score statistics
├── visualization.py     # History chart
├── requirements.txt     # External dependency
└── README.md            # Project documentation
```

## Data Storage

The application automatically creates `history.csv` in the current working directory when saving the first record.

```csv
week,score,rating
1,12,Good
2,20,Excellent
```

Each run adds a new record. The `week` field is a sequential record number; it represents actual weeks only when the application is used once per week.

Automatic numbering assumes that existing records remain in order and are not deleted. CSV loading currently expects the file to follow the format above.

Historical data is stored locally and is not included in the repository.

## Technologies

- Python
- Python's built-in `csv` module
- Matplotlib
- Git and GitHub

## Future Improvements

- Record dates and the original environmental habit inputs.
- Improve handling of manually edited or damaged CSV files.
- Build a web interface.