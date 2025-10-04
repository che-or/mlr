# MLR Scouting and Records

This repository contains a suite of Python scripts designed for analyzing and viewing statistics from the MLR (Major League Redditball). It allows users to load game data from Google Sheets, process it, and generate detailed player statistics, scouting reports, and leaderboards.

## Getting Started

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

## Usage

The main entry point for the tool is `scripts/scouting_tool.py`. Run it from the root directory of the project:

```bash
python scripts/scouting_tool.py
```

Upon launching, the tool will load and process all data specified in `gamelogs.txt`. Once loaded, you can use the following commands in the interactive prompt:

---

### `stats <Player Name or ID>`

Displays a comprehensive statistical summary for a specific player, including both hitting and pitching stats, separated by regular season and playoffs.

- **`<Player Name or ID>`:** The player's unique ID (e.g., `1759`) or their full in-game name (e.g., `"John Doe"`). If a name is used and multiple players share it, you will be prompted to use the unique ID instead.

**Example:**
```
stats 1759
```

---

### `scout <Player ID>`

Generates a detailed pitching scouting report for a given pitcher. This includes pitch usage histograms, situational tendencies (e.g., first pitch of the game, with runners in scoring position), and other patterns.

- **`<Player ID>`:** The pitcher's unique ID.

**Example:**
```
scout 1759
```

---

### `leaderboard <stat>`

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

### `exit`

Exits the scouting tool.

## Scripts Overview

- **`scripts/data_loader.py`**: Handles the loading of season data from Google Sheets URLs listed in `data/gamelogs.txt`. It fetches the data, converts it to a pandas DataFrame, and adds a `GameType` column to distinguish between regular season and playoff games.

- **`scripts/game_processing.py`**: Contains the logic for simulating a game play-by-play to determine pitching decisions (Win, Loss, Save, Hold). It processes a game's DataFrame to track score changes, lead changes, and pitcher appearances.

- **`scripts/scouting_tool.py`**: The main interactive CLI application. It integrates the other modules to:
    - Load and pre-process all data.
    - Calculate detailed hitting and pitching statistics for all players.
    - Generate scouting reports and leaderboards based on user commands.
    - Provide an interactive prompt for user input.
