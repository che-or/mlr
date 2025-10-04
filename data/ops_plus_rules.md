### OPS+ (On-base Plus Slugging Plus) Explained

OPS+ is an advanced statistic that measures a hitter's total offensive value, adjusted for the overall offensive context of the league in a given season. It normalizes a player's On-base Plus Slugging (OPS) so that 100 is always the league average.

---

#### **Interpretation**

*   **100:** Exactly league average.
*   **150:** 50% better than the league average hitter.
*   **75:** 25% worse than the league average hitter.

OPS+ is a great way to compare players across different seasons and ballparks, as it accounts for variations in both league-wide offensive performance and park effects.

---

#### **Calculation in MLR**

The formula used for OPS+ in this tool is:

**OPS+ = 100 * ( (Player's Park-Neutral OBP / League's Park-Neutral OBP) + (Player's Park-Neutral SLG / League's Park-Neutral SLG) - 1 )**

To achieve a park-neutral statistic, the calculation uses the **'Result at Neutral'** column for seasons where it is available (S3 and later). This column shows what the outcome of the play would have been in a perfectly average ballpark.

For older seasons (S2), where this data is not available, the standard results are used as a baseline.

This approach ensures that OPS+ correctly compares players by adjusting for both league-wide offensive trends and ballpark effects.

---

#### **Why Use OPS+?**

A player with a .900 OPS in a high-offense season might be less valuable than a player with an .850 OPS in a low-offense (pitcher-dominated) season. Similarly, a player in an extreme hitter's park will have inflated raw stats. OPS+ cuts through this noise by showing how much better each player was compared to their peers in a normalized environment. It answers the question: "How good was this hitter relative to the league average, once external factors are stripped away?"
