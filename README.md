# MLR Scouting and Records

This repository contains a suite of Python scripts designed for analyzing and viewing statistics from the MLR (Major League Redditball). It allows users to load game data from Google Sheets, process it, and generate detailed player statistics, scouting reports, and leaderboards.

## Web Application Interface

This project now includes a web-based interface to view all player stats, leaderboards, and scouting reports in a user-friendly format.

### Running the Web App

1.  **Generate the Data:**
    First, run the data generation script from the root directory. This script processes all the raw data and creates the JSON files needed by the web app.
    ```bash
    python scripts/generate_web_data.py
    ```

2.  **Start the Web Server:**
    Navigate to the `docs` directory and start a local web server. The simplest way is to use Python's built-in module.
    ```bash
    cd docs
    python -m http.server
    ```

3.  **View the App:**
    Open your web browser and navigate to `http://localhost:8000` (or the address shown in your terminal).

### Deploying to GitHub Pages

Since the web application is built with static files (HTML, CSS, JS), it can be easily hosted on GitHub Pages.

1.  Push the entire project repository to GitHub.
2.  In your repository's settings, go to the "Pages" section.
3.  Configure the source to deploy from the `/docs` folder on your main branch.

## Original Command-Line Tool

### Prerequisites

- Python 3.x
- pip (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd mlr
    ```

2.  **Install dependencies:**
    This project requires the `pandas` library. Install it using pip:
    ```bash
    pip install pandas
    ```

### Data Setup

The tool loads game data based on URLs specified in the `data/gamelogs.txt` file. This file must be structured as a tab-separated list with three columns:

**Format:**
```
<SeasonName>    <NumberOfRegularSeasonGames>    <GoogleSheetURL>
```

**Example `data/gamelogs.txt`:**
```
S5	30	https://docs.google.com/spreadsheets/d/123.../edit#gid=456
S6	32	https://docs.google.com/spreadsheets/d/789.../edit#gid=101
```

- **SeasonName:** A unique identifier for the season (e.g., `S5`).
- **NumberOfRegularSeasonGames:** The total number of games played in the regular season. This is used to differentiate between regular season and playoff games.
- **GoogleSheetURL:** The full URL to the Google Sheet containing the play-by-play data for that season. The script will automatically convert this to a CSV export link.

### Usage

The main entry point for the tool is `scripts/scouting_tool.py`. Run it from the root directory of the project:

```bash
python scripts/scouting_tool.py
```

Upon launching, the tool will load and process all data specified in `gamelogs.txt`. Once loaded, you can use the following commands in the interactive prompt:

---

#### `stats <Player Name or ID>`

Displays a comprehensive statistical summary for a specific player, including both hitting and pitching stats, separated by regular season and playoffs.

- **`<Player Name or ID>`:** The player's unique ID (e.g., `1759`) or their full in-game name (e.g., `"John Doe"`). If a name is used and multiple players share it, you will be prompted to use the unique ID instead.

**Example:**
```
stats 1759
```

---

#### `scout <Player ID>`

Generates a detailed pitching scouting report for a given pitcher. This includes pitch usage histograms, situational tendencies (e.g., first pitch of the game, with runners in scoring position), and other patterns.

- **`<Player ID>`:** The pitcher's unique ID.

**Example:**
```
scout 1759
```

---

#### `leaderboard <stat>`

Shows the top 10 players (seasonal and all-time) for a specified statistic. For rate stats, it automatically applies qualifying minimums (e.g., 2 PA per game for hitters, 1 IP per game for pitchers).

- **`<stat>`:** The statistic you want to see the leaderboard for (e.g., `HR`, `ERA`, `OPS+`, `WHIP`).

**Examples:**
```
leaderboard HR
leaderboard ERA
leaderboard OPS+
```

If the provided stat is not a standard calculated one, the tool will search for event occurrences matching the term (e.g., `leaderboard Bunt`).

---

#### `exit`

Exits the scouting tool.

## Scripts Overview

- **`scripts/data_loader.py`**: Handles the loading of season data from Google Sheets URLs listed in `data/gamelogs.txt`.
- **`scripts/game_processing.py`**: Contains the logic for simulating a game play-by-play to determine pitching decisions (Win, Loss, Save, Hold).
- **`scripts/scouting_tool.py`**: The main interactive CLI application.
- **`scripts/generate_web_data.py`**: A script to process all data and export it to JSON files for the web application.