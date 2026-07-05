# MLR Reference

This repository contains a suite of Python scripts designed for analyzing and viewing statistics from the MLR (Major League Redditball). It allows users to load game data from Google Sheets, process it, and generate detailed player statistics, leaderboards, team stats, and a glossary of terms.

## Web Application Interface

This project now includes a web-based interface to view all player stats, leaderboards, team statistics, and a glossary in a user-friendly format.

### Features:
- **Player Stats:** Comprehensive hitting and pitching statistics for individual players, including career and seasonal breakdowns.
- **Team Stats:** View team standings and individual player statistics per team for each season.
- **Leaderboards:** Dynamic leaderboards for various batting and pitching statistics, with filters for season and team.
- **Glossary:** Definitions and explanations for various baseball statistics and terms, including run expectancy matrices.

### Application Pages
The web application provides several pages to explore the data:
- **Home (`#/home`):** A landing page that welcomes users and showcases featured players and teams.
- **Player Stats (`#/stats`):** A searchable page for individual player statistics, showing detailed batting and pitching data.
- **Team Stats (`#/team-stats`):** Displays season-by-season standings and allows drilling down into team-specific stats.
- **Leaderboards (`#/leaderboards`):** Provides all-time and single-season leaderboards for a wide variety of statistical categories.
- **Awards (`#/awards`):** A page to view season-by-season award winners.
- **Hall of Fame (`#/hof`):** View the members of the Hall of Fame.
- **Draft History (`#/draft`):** Season-by-season draft picks for MLR.
- **Single-Game Records (`#/single-game-records`):** All-time single-game record holders for batting and pitching stats for all leagues.
- **Streaks (`#/streaks`):** MLR all-time and active streak records for hitting, on-base, scoreless innings, and more.
- **Player Comparison (`#/compare`):** Compare up to 4 players.
- **Glossary (`#/glossary`):** A reference for advanced stats and terminology used in the application.

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

## Scripts Overview
- **`scripts/add_re_column.py`**: Adds a Run Expectancy to the gamelogs based on a season's RE Matrix.
- **`scripts/add_war_columns.py`**: Adds batter WAR and pitcher WAR columns to the gamelogs.
- **`scripts/calculate_fip_constant.py`**: Calculates season FIP Constants.
- **`scripts/calculate_pitching_neutrals.py`**: Calculates nER, nIP, lgnER, and lgnIP.
- **`scripts/calculate_re_matrix.py`**: Calculate the Run Expectancy Matrix for a season.
- **`scripts/create_subrows.py`**: Creates combined season stats for players that played for multiple teams in a single season.
- **`scripts/determine_pitcher_decisions.py`**: Determines W, L, SV, BS, HLD, GS, GF, CG, and SHO for each game.
- **`scripts/download_gamelogs.py`**: Downloads gamelogs from Google Sheets.
- **`scripts/generate_draft_history.py`**: Fetches MLR Draft History from Google Sheets and writes `docs/data/draft_history.json`.
- **`scripts/generate_playoff_brackets.py`**: Generates the playoff bracket data used on the team stats page.
- **`scripts/generate_web_data.py`**: Generates the JSON statistic content the site uses. This script runs automatically every night to keep the site up to date.
- **`scripts/get_hitting_stats.py`**: Calculates hitting stats.
- **`scripts/get_pitching_stats.py`**: Calculates pitching stats.
- **`scripts/get_player_names.py`**: Creates a list of players and their basic player info.
- **`scripts/get_single_game_achievements.py`**: Finds single-game achievements (no-hitters, cycles, triangles, multi-HR games).
- **`scripts/get_single_game_stats.py`**: Calculates single-game and single-season record stats for batting and pitching.
- **`scripts/get_streak_records.py`**: Calculates all-time and active streak records for hitting, on-base, scoreless innings, and more.
- **`scripts/load_gamelogs.py`**: Loads gamelogs
- **`scripts/runner_attribution.py`**: Adds Manfred runners and trailing runner stolen bases to the gamelogs for easier stat calculations
- **`scripts/simulate_inning.py`**: Simulates a gamelog inning.
- **`scripts/simulate_runners.py`**: Simulates a single play.
- **`scripts/update_glossary_re_matrix.py`**: Updates the RE24 glossary entry with the latest MLR RE matrix.

## Maintenance Information

The site requires maintenance, mostly at the beginning of seasons.

- **`data/gamelog_links.csv`** needs to be updated for the new seaons. Make sure to updated the 'Active' column for newly inactive seasons. It's not required, but it is good practice to move the source of gamelogs and player types for completed seasons to an archive.
- **`docs/data/awards.json`** needs to be updated to include the previous season's awards, all-stars, and Hall of Famers.
- **`docs/data/draft_history.json`** needs to be updated with the season's draft picks by running `scripts/generate_draft_history.py`.
- **`docs/data/*_divisions`** needs to be updated with season division structure
- **`docs/data/*_team_history`** needs to be updated with the season's teams, abbreviation, and logo
- **`docs/img/*`** needs to be updated with any new logos as `.svg.` files.