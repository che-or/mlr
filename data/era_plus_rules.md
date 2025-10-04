### ERA+ (Earned Run Average Plus) Explained

ERA+ is an advanced statistic that measures a pitcher's performance, adjusted for the overall offensive context of the league and park in a given season. It normalizes a pitcher's Earned Run Average (ERA) so that 100 is always the league average, but unlike traditional ERA, a higher number is better.

---

#### **Interpretation**

*   **100:** Exactly league average.
*   **150:** 50% better than the league average pitcher.
*   **75:** 25% worse than the league average pitcher.

ERA+ is the pitching equivalent of OPS+ and is one of the best ways to compare pitchers across different eras, seasons, and ballparks.

---

#### **Calculation in MLR**

The formula used for ERA+ in this tool is:

**ERA+ = 100 * (League's Park-Neutral ERA / Player's Park-Neutral ERA)**

Calculating a pitcher's Park-Neutral ERA (`nERA`) is a complex process that goes beyond their standard ERA:

1.  **Neutral Simulation:** Each inning a pitcher has thrown is re-simulated play-by-play using the **'Result at Neutral'** column. This determines what the outcome of each play would have been in a perfectly average ballpark.

2.  **Rulebook Logic:** The simulation uses the official MLR Rulebook (Section 3.3) to determine how runners advance and how many runs score on each of these neutral plays.

3.  **Run Expectancy Matrix:** A key challenge is handling innings that end in reality but would have continued in the neutral simulation. To solve this, the tool uses a **Run Expectancy Matrix**. This matrix, calculated for each season, determines the average number of additional runs that are likely to score from any given base-out situation (e.g., "runners on 1st and 3rd, 1 out"). These expected runs are added to the pitcher's `nERA` total.

This comprehensive simulation produces a pitcher's `nERA`, which reflects their performance independent of park effects. This `nERA` is then compared against the league-average `nERA` to produce the final ERA+.

---

#### **Why Use ERA+?**

A pitcher with a 3.50 ERA in a high-offense season is far more valuable than a pitcher with a 3.50 ERA in a dead-ball, pitcher-dominated season. ERA+ makes this comparison easy. By normalizing for external factors like park effects and the league's run-scoring environment, it provides a single, context-adjusted number to measure a pitcher's true performance relative to their peers.
