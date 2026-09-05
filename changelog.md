# MLR Reference Changelog

### 2.4 - September 5, 2026
- Update draft history with IDs of players with newly assigned IDs
- Add "Enthusiasts" to S9 MiLR Montclair team name
- Fix W-L% to recalculate after pitcher decision adjustments are applied
- Add games played adjustments. Players are now credited with a game played if they play in the field or pinch run, even if they don't record a plate appearance or stolen base attempt. Players are not credited with a game played if they:
    - Are pinch hit for in T1
    - Are pinch hit for in their first plate appearance AND are the DH
    - Enter the game as a pinch hitter, and are pinch hit for
    - Were scheduled to pinch hit, but the game ended before their PA
    - These games played are recorded in a player's batting stats. A player is *not* currently credited with a batting game played if they do not have any plate appearnaces or stolen base attempts *and* appear as a pitcher, even if the pitcher spot is in the lineup or the player also plays another position.
- Add run scored adjustments. Handles the case of a pinch runner that doesn't steal a base scoring a run, or a fielding replacement scoring as a ghost runner.

#### 2.3.6 - August 29, 2026
- Add S13 draft results
- Start MLR S13
- Start MiLR S13
- Change GM of the Year to Hannibal Bligh GM of the Year starting with S12

#### 2.3.5 - August 25, 2026
- Make infinite values display as "Inf." rather than the same as other indeterminate forms (e.g. 0/0)

#### 2.3.4 - August 24, 2026
- Fix S5-10 TBR bug associated with changing S4 to TBD
- Fix logos for all-stars who were traded between the All-Star Break and the end of the season
- End FCB S13

#### 2.3.3 - August 23, 2026
- Add MLR S12 Playoff brackets
- Add S12 awards
- Change S4 Devil Rays abbreviation from TBR to TBD
- Fix bug where streaks aren't broken in the last game of the season

#### 2.3.2 - July 9, 2026
- Add SB 2B, SB 3B, SB Home
- Add CS 2B, CS 3B, CS Home

#### 2.3.1 - July 7, 2026
- End MLR S12
- Start MLR S12 Playoffs

### 2.3 - July 5, 2026
- Added WPA for seasons where it was missing
- Recalculated WPA for some seasons to be in line with current WPA calculations

#### 2.2.1 - July 4, 2026
- Fix incorrect MiLR S5 and S6 team records
- Add caching for vs team stats
- Add styling for league and all-time leaders

### 2.2 - July 3, 2026
- Add BARISP
- Add stats vs other teams

#### 2.1.4 - July 2, 2026
- End MiLR S12
- Start FCB S13

#### 2.1.3 - June 30, 2026
- Fix scoreless innings streaks
- Allow players to tie themselves in streaks
- Add single game records for leagues other than MLR
- Add 1RHR, 2RHR, 3RHR, 4RHR

#### 2.1.2 - June 29, 2026
- Add streaks

#### 2.1.1 - June 27, 2026
- Add draft history
- Add single game records for MLR

### 2.1 - June 26, 2026
- Add team leaderboards
- Add playoff brackets

#### 2.0.5 - June 23, 2026
- Add leagues for MiLR S8A
- Fix franchise-team linkage bug in player stat tables

#### 2.0.4 - June 10, 2026
- Change Rochester Null abbreviation from N/A to NUL

#### 2.0.3 - June 9, 2026
- Add more MiLR logos
- Fix Cy Hadd's ID in awards
- Bug fixes

#### 2.0.2 - June 7, 2026
- Add more MiLR logos

#### 2.0.1 - June 6, 2026
- Add some FCB logos
- Add WBC flags
- Add S9-S12 MiLR logos

### 2.0 - June 5, 2026
- For in depth changes and updates, see: https://docs.google.com/document/d/1Rzsf8Mb7Te3oy2DLX2rT6RU62OscoBm58HuEwqsIyjk/edit?usp=sharing

#### 1.3.3 - May 4, 2026
- Add S12 MLR All Star Game reserves

#### 1.3.2 - May 2, 2026
- Add S12 MLR All Star Game starters

#### 1.3.1 - January 11, 2026
- Corrected loss determination for the case of inherited runners scoring go-ahead run
- Fixed errant gamelogs for S2(171) and S2(178)

### 1.3 - January 7, 2026
- Added FCB stats and leaderboards
- Corrected save and hold determination logic

#### 1.2.1 - December 18, 2025
- Fixed S3 MiLR CIN overriding S3 MLR CLE (current CIN)
- Fixed name display for when players have more recently played in MiLR than MLR
- Changed "Show Minors" to "Show MiLR"
- Add Rusty's S4 Home Run Derby win

### 1.2 - December 16, 2025
- Added MiLR stats and leaderboards

#### 1.1.3 - December 11, 2025
- Fixed 1.000 displaying as .000 in the standings

#### 1.1.2 - December 10, 2025
- Improved mobile display and scrolling of player stats, team stats, and awards

#### 1.1.1 - December 9, 2025
- Added awards page
- Added Hall of Fame

### 1.1 - December 7, 2025
- Added player awards

#### 1.0.4 - December 6, 2025
- Fixed leaderboard filtering for when both team and type are selected

#### 1.0.3 - December 5, 2025
- Applied patch for 'Result at Neutral' column missing BB in S8-11

#### 1.0.2 - November 30, 2025
- Removed inaccurate FAQs
- Fixed S2 WSH forfeit against SDP

#### 1.0.1 - November 29, 2025
- Added light mode
- Fixed pinch runners affecting multiple seasons
- Fixed player search for names used by multiple players
- Allowed searching for single digit player ID
- Removed 'IMPORT ERROR' as a valid name

### 1.0 - November 28, 2025
- First full release

