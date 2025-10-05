### FIP (Fielding Independent Pitching) Explained

Fielding Independent Pitching (FIP) is an advanced pitching metric that estimates a pitcher's performance based only on outcomes that do not involve the defense: home runs, walks, and strikeouts. It operates on the same scale as ERA, making it easy to compare.

---

#### **Interpretation**

Because FIP is on the same scale as ERA, you can read it in the same way. A FIP of 3.50 is roughly equivalent to a 3.50 ERA. The key difference is that FIP measures what a pitcher's ERA *should have been*, given their performance on events they can control. 

*   **If FIP < ERA:** The pitcher may have been unlucky or had poor defensive support.
*   **If FIP > ERA:** The pitcher may have been lucky or had excellent defensive support.

--- 

#### **Calculation in MLR**

The formula used for FIP in this tool is:

**FIP = ((13 * HR) + (3 * BB) - (2 * K)) / IP + FIP Constant**

*   **HR:** Home Runs Allowed
*   **BB:** Walks Allowed (does not include Hit By Pitch, as HBP is not tracked)
*   **K:** Strikeouts
*   **IP:** Innings Pitched

To ensure FIP is on the same scale as ERA, a **FIP Constant** is calculated for each season and added. This constant is derived from the league's overall performance in a given season:

**FIP Constant = League ERA - ((13 * League HR) + (3 * League BB) - (2 * League K)) / League IP**

This adjustment ensures that a league-average FIP will equal the league-average ERA for that season, making for a fair comparison.

---

#### **Why Use FIP?**

A pitcher has no control over what happens once a ball is put in play. A bloop single and a line drive directly at a fielder can have vastly different outcomes based on luck and the quality of the defense behind the pitcher. 

FIP strips away that randomness and focuses only on the three true outcomes a pitcher can largely control: preventing home runs, preventing walks, and getting strikeouts. This makes it a valuable tool for evaluating a pitcher's underlying skill and predicting their future performance more accurately than ERA alone.
