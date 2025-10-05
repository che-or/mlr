### WAR (Wins Above Replacement) Explained

Wins Above Replacement (WAR) is a comprehensive statistic that attempts to consolidate a player's total contribution into a single number. It represents how many more wins a player is worth than a "replacement-level" player—a hypothetical, readily available player (e.g., a minor leaguer) who could be substituted at minimal cost.

In this tool, WAR is built upon the foundation of RE24, providing a holistic view of a player's value in the context of the league's run-scoring environment.

---

#### **Interpretation**

WAR provides a convenient way to compare the total value of all players, regardless of whether they are a hitter or a pitcher.

*   **0.0 WAR:** A replacement-level player.
*   **1.0 WAR:** A solid, everyday player.
*   **3.0+ WAR:** An All-Star caliber player.
*   **5.0+ WAR:** An MVP candidate.

Since this is a counting stat, these values are benchmarks for a full season. A player's WAR accumulates over time.

---

#### **Calculation in MLR**

The WAR model in this tool is designed to be balanced and context-neutral, based on your league's specific rules and outcomes.

The final formula is: **WAR = (Runs Above Replacement) / (Runs Per Win)**

Here is the step-by-step process for a given season:

1.  **Total WAR Pool:** The total amount of WAR available for all players in the league for a season is defined as **(Number of Regular Season Games) * 6.17**. This creates a consistent, scaled environment similar to other baseball leagues.

2.  **Hitter/Pitcher Split:** To ensure fair comparison, this total WAR pool is split evenly, with 50% allocated to all hitters and 50% to all pitchers.

3.  **Runs Per Win (RPW):** A standard value of **10 Runs Per Win** is used. This means for every 10 runs a player creates above a replacement player, they are credited with 1 WAR.

4.  **Runs Above Replacement (RAR):** This is the core of the calculation.
    *   First, a player's **Runs Above Average (RAA)** is their `RE24` for the season.
    *   Next, a "replacement-level" run value is calculated based on the total WAR pool and total playing time (Plate Appearances and Batters Faced) in the league.
    *   A player's RAR is their `RAA` plus the replacement-level value scaled by their specific playing time.
    *   `RAR = RE24 + (Replacement Value per PA/BF * Player's PA/BF)`

5.  **Final Value:** The player's total RAR is divided by 10 (the RPW value) to arrive at their final WAR for the season.

---

#### **Why Use WAR?**

WAR is one of the most powerful tools for player analysis because it combines multiple facets of performance into a single, easy-to-understand number that is tied directly to wins.

*   **Universal Comparison:** It provides a unified scale to measure the value of hitters and pitchers against each other.
*   **Context Included:** By being based on RE24, it inherently includes the context of every play.
*   **Value over Volume:** While it rewards players for playing more, it is fundamentally a measure of *value*. A player with a high WAR in limited playing time is recognized as being highly effective.
