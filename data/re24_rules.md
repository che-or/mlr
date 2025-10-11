### RE24 (Run Expectancy Over 24 Base-Out States) Explained

RE24 is an advanced statistic that measures the total impact a player has on their team's run-scoring potential. It calculates the change in run expectancy from the beginning of a plate appearance to the end, crediting or debiting the player for the outcome.

Unlike stats that only measure hits or outs, RE24 captures the full context of a play. For example, a solo home run is good, but a bases-clearing double that doesn't score the batter might be even more valuable in a given situation. RE24 quantifies this value.

---

#### **Interpretation**

RE24 is a counting stat, not a rate stat. It accumulates over a season.

*   **For Hitters:** A **higher** RE24 is better. It means the player consistently creates situations that lead to more runs. A positive value indicates they have been more productive than an average player would have been in the same situations.
*   **For Pitchers:** A **lower** RE24 is better. It means the pitcher consistently reduces the opponent's chances of scoring. A negative value indicates the pitcher has been more effective at suppressing run-scoring opportunities than an average pitcher.

A value of **0** represents a league-average performance.

---

#### **Calculation in MLR**

The formula for a single play is:

**RE24 = (Run Expectancy After Play) - (Run Expectancy Before Play) + (Runs Scored on Play)**

The calculation process in this tool is as follows:

1.  **Run Expectancy (RE) Matrix:** First, the tool calculates a Run Expectancy Matrix for each season. This matrix contains the average number of runs that will be scored from every possible base-out state (e.g., "runner on 1st, 0 outs") until the end of the inning. There are 24 possible states (8 base states x 3 out states).

2.  **Before and After States:** For every single plate appearance in the season, the tool looks at the base-out state *before* the play and the state *after* the play.

3.  **Applying the Formula:** The tool retrieves the RE values for the before and after states from the matrix and applies the formula above. Any runs that score directly on the play are also added.

4.  **Aggregation:** A player's seasonal RE24 is the sum of the RE24 values from all of their plate appearances.

---

#### **Why Use RE24?**

RE24 provides a more complete picture of a player's offensive contribution (or run prevention skill) than traditional stats.

*   **Context Matters:** It properly credits a hitter for a walk with the bases loaded or a sacrifice fly that scores a run, plays that are often undervalued by stats like batting average.
*   **Situational Value:** It correctly penalizes a pitcher for a walk that loads the bases, even if no runs score immediately, because the run expectancy has increased significantly.
*   **Comprehensive Value:** It moves beyond just outcomes (hit, out, walk) and measures a player's direct impact on the one thing that wins games: scoring runs.
