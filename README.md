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
4. Install the required dependency:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python main.py
   ```

A chart window will open after the results are displayed. Close the chart window to finish the program.

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

- Add AI-generated personalized environmental advice.
- Record dates and the original environmental habit inputs.
- Improve handling of manually edited or damaged CSV files.
- Build a web interface.