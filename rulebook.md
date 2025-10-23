# Baseball Play Outcome Rulebook

This document details the logic for various baseball play outcomes as implemented in the game simulation engine (`game_processing.py`). For each outcome, it shows how the base-out state changes and how many runs are scored.

## Outcomes: HR

**Logic:** All runners on base score, plus the batter. Bases become empty.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 1 | 0 |
| 0 | 100 | 000 | 2 | 0 |
| 0 | 010 | 000 | 2 | 0 |
| 0 | 001 | 000 | 2 | 0 |
| 0 | 110 | 000 | 3 | 0 |
| 0 | 101 | 000 | 3 | 0 |
| 0 | 011 | 000 | 3 | 0 |
| 0 | 111 | 000 | 4 | 0 |
| 1 | 000 | 000 | 1 | 1 |
| 1 | 100 | 000 | 2 | 1 |
| 1 | 010 | 000 | 2 | 1 |
| 1 | 001 | 000 | 2 | 1 |
| 1 | 110 | 000 | 3 | 1 |
| 1 | 101 | 000 | 3 | 1 |
| 1 | 011 | 000 | 3 | 1 |
| 1 | 111 | 000 | 4 | 1 |
| 2 | 000 | 000 | 1 | 2 |
| 2 | 100 | 000 | 2 | 2 |
| 2 | 010 | 000 | 2 | 2 |
| 2 | 001 | 000 | 2 | 2 |
| 2 | 110 | 000 | 3 | 2 |
| 2 | 101 | 000 | 3 | 2 |
| 2 | 011 | 000 | 3 | 2 |
| 2 | 111 | 000 | 4 | 2 |

## Outcomes: 3B

**Logic:** All runners on base score. Batter is on 3rd.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 001 | 0 | 0 |
| 0 | 100 | 001 | 1 | 0 |
| 0 | 010 | 001 | 1 | 0 |
| 0 | 001 | 001 | 1 | 0 |
| 0 | 110 | 001 | 2 | 0 |
| 0 | 101 | 001 | 2 | 0 |
| 0 | 011 | 001 | 2 | 0 |
| 0 | 111 | 001 | 3 | 0 |
| 1 | 000 | 001 | 0 | 1 |
| 1 | 100 | 001 | 1 | 1 |
| 1 | 010 | 001 | 1 | 1 |
| 1 | 001 | 001 | 1 | 1 |
| 1 | 110 | 001 | 2 | 1 |
| 1 | 101 | 001 | 2 | 1 |
| 1 | 011 | 001 | 2 | 1 |
| 1 | 111 | 001 | 3 | 1 |
| 2 | 000 | 001 | 0 | 2 |
| 2 | 100 | 001 | 1 | 2 |
| 2 | 010 | 001 | 1 | 2 |
| 2 | 001 | 001 | 1 | 2 |
| 2 | 110 | 001 | 2 | 2 |
| 2 | 101 | 001 | 2 | 2 |
| 2 | 011 | 001 | 2 | 2 |
| 2 | 111 | 001 | 3 | 2 |

## Outcomes: 2B

**Logic:** Standard double. Runners advance two bases. With 2 outs, all runners advance two bases, and the batter is on 2nd.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 010 | 0 | 0 |
| 0 | 100 | 011 | 0 | 0 |
| 0 | 010 | 010 | 1 | 0 |
| 0 | 001 | 010 | 1 | 0 |
| 0 | 110 | 011 | 1 | 0 |
| 0 | 101 | 011 | 1 | 0 |
| 0 | 011 | 010 | 2 | 0 |
| 0 | 111 | 011 | 2 | 0 |
| 1 | 000 | 010 | 0 | 1 |
| 1 | 100 | 011 | 0 | 1 |
| 1 | 010 | 010 | 1 | 1 |
| 1 | 001 | 010 | 1 | 1 |
| 1 | 110 | 011 | 1 | 1 |
| 1 | 101 | 011 | 1 | 1 |
| 1 | 011 | 010 | 2 | 1 |
| 1 | 111 | 011 | 2 | 1 |
| 2 | 000 | 010 | 0 | 2 |
| 2 | 100 | 010 | 1 | 2 |
| 2 | 010 | 010 | 1 | 2 |
| 2 | 001 | 010 | 1 | 2 |
| 2 | 110 | 010 | 2 | 2 |
| 2 | 101 | 010 | 2 | 2 |
| 2 | 011 | 010 | 2 | 2 |
| 2 | 111 | 010 | 3 | 2 |

## Outcomes: 1B

**Logic:** Standard single. Runners advance one base. With 2 outs, all runners advance two bases, and the batter is on 1st.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 100 | 0 | 0 |
| 0 | 100 | 110 | 0 | 0 |
| 0 | 010 | 101 | 0 | 0 |
| 0 | 001 | 100 | 1 | 0 |
| 0 | 110 | 111 | 0 | 0 |
| 0 | 101 | 110 | 1 | 0 |
| 0 | 011 | 101 | 1 | 0 |
| 0 | 111 | 111 | 1 | 0 |
| 1 | 000 | 100 | 0 | 1 |
| 1 | 100 | 110 | 0 | 1 |
| 1 | 010 | 101 | 0 | 1 |
| 1 | 001 | 100 | 1 | 1 |
| 1 | 110 | 111 | 0 | 1 |
| 1 | 101 | 110 | 1 | 1 |
| 1 | 011 | 101 | 1 | 1 |
| 1 | 111 | 111 | 1 | 1 |
| 2 | 000 | 100 | 0 | 2 |
| 2 | 100 | 101 | 0 | 2 |
| 2 | 010 | 100 | 1 | 2 |
| 2 | 001 | 100 | 1 | 2 |
| 2 | 110 | 101 | 1 | 2 |
| 2 | 101 | 101 | 1 | 2 |
| 2 | 011 | 100 | 2 | 2 |
| 2 | 111 | 101 | 2 | 2 |

## Outcomes: BUNT 1B, Bunt 1B

**Logic:** Batter on 1st. Runners advance one base.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 100 | 0 | 0 |
| 0 | 100 | 110 | 0 | 0 |
| 0 | 010 | 101 | 0 | 0 |
| 0 | 001 | 100 | 1 | 0 |
| 0 | 110 | 111 | 0 | 0 |
| 0 | 101 | 110 | 1 | 0 |
| 0 | 011 | 101 | 1 | 0 |
| 0 | 111 | 111 | 1 | 0 |
| 1 | 000 | 100 | 0 | 1 |
| 1 | 100 | 110 | 0 | 1 |
| 1 | 010 | 101 | 0 | 1 |
| 1 | 001 | 100 | 1 | 1 |
| 1 | 110 | 111 | 0 | 1 |
| 1 | 101 | 110 | 1 | 1 |
| 1 | 011 | 101 | 1 | 1 |
| 1 | 111 | 111 | 1 | 1 |
| 2 | 000 | 100 | 0 | 2 |
| 2 | 100 | 110 | 0 | 2 |
| 2 | 010 | 101 | 0 | 2 |
| 2 | 001 | 100 | 1 | 2 |
| 2 | 110 | 111 | 0 | 2 |
| 2 | 101 | 110 | 1 | 2 |
| 2 | 011 | 101 | 1 | 2 |
| 2 | 111 | 111 | 1 | 2 |

## Outcomes: BB, IBB, Auto BB, AUTO BB

**Logic:** Batter on 1st. All forced runners advance one base.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 100 | 0 | 0 |
| 0 | 100 | 110 | 0 | 0 |
| 0 | 010 | 110 | 0 | 0 |
| 0 | 001 | 101 | 0 | 0 |
| 0 | 110 | 111 | 0 | 0 |
| 0 | 101 | 111 | 0 | 0 |
| 0 | 011 | 111 | 0 | 0 |
| 0 | 111 | 111 | 1 | 0 |
| 1 | 000 | 100 | 0 | 1 |
| 1 | 100 | 110 | 0 | 1 |
| 1 | 010 | 110 | 0 | 1 |
| 1 | 001 | 101 | 0 | 1 |
| 1 | 110 | 111 | 0 | 1 |
| 1 | 101 | 111 | 0 | 1 |
| 1 | 011 | 111 | 0 | 1 |
| 1 | 111 | 111 | 1 | 1 |
| 2 | 000 | 100 | 0 | 2 |
| 2 | 100 | 110 | 0 | 2 |
| 2 | 010 | 110 | 0 | 2 |
| 2 | 001 | 101 | 0 | 2 |
| 2 | 110 | 111 | 0 | 2 |
| 2 | 101 | 111 | 0 | 2 |
| 2 | 011 | 111 | 0 | 2 |
| 2 | 111 | 111 | 1 | 2 |

## Outcomes: STEAL 2B

**Logic:** Runner on 1st steals 2nd.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 010 | 0 | 0 |
| 0 | 101 | 011 | 0 | 0 |
| 1 | 100 | 010 | 0 | 1 |
| 1 | 101 | 011 | 0 | 1 |
| 2 | 100 | 010 | 0 | 2 |
| 2 | 101 | 011 | 0 | 2 |

## Outcomes: STEAL 3B

**Logic:** Runner on 2nd steals 3rd.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 010 | 001 | 0 | 0 |
| 0 | 110 | 101 | 0 | 0 |
| 1 | 010 | 001 | 0 | 1 |
| 1 | 110 | 101 | 0 | 1 |
| 2 | 010 | 001 | 0 | 2 |
| 2 | 110 | 101 | 0 | 2 |

## Outcomes: STEAL HOME

**Logic:** Runner on 3rd steals home.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 001 | 000 | 1 | 0 |
| 0 | 101 | 100 | 1 | 0 |
| 0 | 011 | 010 | 1 | 0 |
| 0 | 111 | 110 | 1 | 0 |
| 1 | 001 | 000 | 1 | 1 |
| 1 | 101 | 100 | 1 | 1 |
| 1 | 011 | 010 | 1 | 1 |
| 1 | 111 | 110 | 1 | 1 |
| 2 | 001 | 000 | 1 | 2 |
| 2 | 101 | 100 | 1 | 2 |
| 2 | 011 | 010 | 1 | 2 |
| 2 | 111 | 110 | 1 | 2 |

## Outcomes: MSTEAL 3B

**Logic:** Runner on 1st advances to 2nd, runner on 2nd advances to 3rd.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 110 | 011 | 0 | 0 |
| 1 | 110 | 011 | 0 | 1 |
| 2 | 110 | 011 | 0 | 2 |

## Outcomes: MSTEAL HOME

**Logic:** Runner on 1st advances to 2nd, runner on 2nd advances to 3rd, runner on 3rd scores.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 101 | 010 | 1 | 0 |
| 0 | 011 | 001 | 1 | 0 |
| 0 | 111 | 011 | 1 | 0 |
| 1 | 101 | 010 | 1 | 1 |
| 1 | 011 | 001 | 1 | 1 |
| 1 | 111 | 011 | 1 | 1 |
| 2 | 101 | 010 | 1 | 2 |
| 2 | 011 | 001 | 1 | 2 |
| 2 | 111 | 011 | 1 | 2 |

## Outcomes: FO, Sac

**Logic:** Flyout. Batter is out. Runners advance if tagging up.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 100 | 0 | 1 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 000 | 1 | 1 |
| 0 | 110 | 110 | 0 | 1 |
| 0 | 101 | 100 | 1 | 1 |
| 0 | 011 | 010 | 1 | 1 |
| 0 | 111 | 110 | 1 | 1 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 100 | 0 | 2 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 000 | 1 | 2 |
| 1 | 110 | 110 | 0 | 2 |
| 1 | 101 | 100 | 1 | 2 |
| 1 | 011 | 010 | 1 | 2 |
| 1 | 111 | 110 | 1 | 2 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 100 | 0 | 3 |
| 2 | 010 | 010 | 0 | 3 |
| 2 | 001 | 001 | 0 | 3 |
| 2 | 110 | 110 | 0 | 3 |
| 2 | 101 | 101 | 0 | 3 |
| 2 | 011 | 011 | 0 | 3 |
| 2 | 111 | 111 | 0 | 3 |

## Outcomes: BUNT Sac, Bunt Sac, Bunt

**Logic:** Sacrifice bunt. Batter is out. Runners advance one base.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 010 | 0 | 1 |
| 0 | 010 | 001 | 0 | 1 |
| 0 | 110 | 011 | 0 | 1 |
| 0 | 101 | 011 | 0 | 1 |
| 1 | 100 | 010 | 0 | 2 |
| 1 | 010 | 001 | 0 | 2 |
| 1 | 110 | 011 | 0 | 2 |
| 1 | 101 | 011 | 0 | 2 |
| 2 | 100 | 100 | 0 | 3 |
| 2 | 010 | 010 | 0 | 3 |
| 2 | 110 | 110 | 0 | 3 |
| 2 | 101 | 101 | 0 | 3 |

## Outcomes: LO, K, Auto K, Bunt K, AUTO K, PO

**Logic:** Lineout. Batter is out. Runners hold their bases.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 100 | 0 | 1 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 001 | 0 | 1 |
| 0 | 110 | 110 | 0 | 1 |
| 0 | 101 | 101 | 0 | 1 |
| 0 | 011 | 011 | 0 | 1 |
| 0 | 111 | 111 | 0 | 1 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 100 | 0 | 2 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 001 | 0 | 2 |
| 1 | 110 | 110 | 0 | 2 |
| 1 | 101 | 101 | 0 | 2 |
| 1 | 011 | 011 | 0 | 2 |
| 1 | 111 | 111 | 0 | 2 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 100 | 0 | 3 |
| 2 | 010 | 010 | 0 | 3 |
| 2 | 001 | 001 | 0 | 3 |
| 2 | 110 | 110 | 0 | 3 |
| 2 | 101 | 101 | 0 | 3 |
| 2 | 011 | 011 | 0 | 3 |
| 2 | 111 | 111 | 0 | 3 |

## Outcomes: LGO (normal diff)

**Logic:** A standard groundout. With a runner on 1st, this becomes a 2-out double play.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 000 | 0 | 2 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 000 | 1 | 1 |
| 0 | 110 | 001 | 0 | 2 |
| 0 | 101 | 000 | 1 | 2 |
| 0 | 011 | 010 | 1 | 1 |
| 0 | 111 | 001 | 1 | 2 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 000 | 1 | 2 |
| 1 | 110 | 000 | 0 | 3 |
| 1 | 101 | 000 | 0 | 3 |
| 1 | 011 | 010 | 1 | 2 |
| 1 | 111 | 000 | 0 | 3 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 000 | 0 | 3 |
| 2 | 101 | 000 | 0 | 3 |
| 2 | 011 | 000 | 0 | 3 |
| 2 | 111 | 000 | 0 | 3 |

## Outcomes: LGO (high diff) S9+

**Logic:** A special high-diff result for Season 9+. Can become a lineout (1 out), lineout double play (2 outs), or triple play (3 outs) depending on base state and outs, as per the table.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 000 | 0 | 2 |
| 0 | 010 | 000 | 0 | 2 |
| 0 | 001 | 000 | 0 | 2 |
| 0 | 110 | 000 | 0 | 3 |
| 0 | 101 | 001 | 0 | 2 |
| 0 | 011 | 001 | 0 | 2 |
| 0 | 111 | 001 | 0 | 3 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 010 | 000 | 0 | 3 |
| 1 | 001 | 000 | 0 | 3 |
| 1 | 110 | 000 | 0 | 3 |
| 1 | 101 | 001 | 0 | 3 |
| 1 | 011 | 001 | 0 | 3 |
| 1 | 111 | 001 | 0 | 3 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 000 | 0 | 3 |
| 2 | 101 | 000 | 0 | 3 |
| 2 | 011 | 000 | 0 | 3 |
| 2 | 111 | 000 | 0 | 3 |

## Outcomes: LGO (high diff) S1-8

**Logic:** A special high-diff result for Seasons 1-8. Can become a triple play (3 outs) if runners are on 1st and 2nd or bases loaded, otherwise it behaves like a normal LGO.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 000 | 0 | 2 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 000 | 1 | 1 |
| 0 | 110 | 000 | 0 | 3 |
| 0 | 101 | 000 | 1 | 2 |
| 0 | 011 | 010 | 1 | 1 |
| 0 | 111 | 000 | 0 | 3 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 000 | 1 | 2 |
| 1 | 110 | 000 | 0 | 3 |
| 1 | 101 | 000 | 0 | 3 |
| 1 | 011 | 010 | 1 | 2 |
| 1 | 111 | 000 | 0 | 3 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 000 | 0 | 3 |
| 2 | 101 | 000 | 0 | 3 |
| 2 | 011 | 000 | 0 | 3 |
| 2 | 111 | 000 | 0 | 3 |

## Outcomes: RGO

**Logic:** Groundout. With a runner on 1st, this becomes a 2-out double play.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 000 | 0 | 2 |
| 0 | 010 | 001 | 0 | 1 |
| 0 | 001 | 000 | 1 | 1 |
| 0 | 110 | 001 | 0 | 2 |
| 0 | 101 | 000 | 1 | 2 |
| 0 | 011 | 001 | 1 | 1 |
| 0 | 111 | 001 | 1 | 2 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 010 | 001 | 0 | 2 |
| 1 | 001 | 000 | 1 | 2 |
| 1 | 110 | 000 | 0 | 3 |
| 1 | 101 | 000 | 0 | 3 |
| 1 | 011 | 001 | 1 | 2 |
| 1 | 111 | 000 | 0 | 3 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 000 | 0 | 3 |
| 2 | 101 | 000 | 0 | 3 |
| 2 | 011 | 000 | 0 | 3 |
| 2 | 111 | 000 | 0 | 3 |

## Outcomes: BUNT GO, Bunt GO, Bunt DP

**Logic:** Bunt groundout. Batter is out. Runners advance one base.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 000 | 0 | 2 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 001 | 0 | 1 |
| 0 | 110 | 001 | 0 | 2 |
| 0 | 101 | 101 | 0 | 1 |
| 0 | 011 | 011 | 0 | 1 |
| 0 | 111 | 011 | 0 | 2 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 001 | 0 | 2 |
| 1 | 110 | 001 | 0 | 3 |
| 1 | 101 | 101 | 0 | 2 |
| 1 | 011 | 011 | 0 | 2 |
| 1 | 111 | 011 | 0 | 3 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 010 | 0 | 3 |
| 2 | 001 | 001 | 0 | 3 |
| 2 | 110 | 001 | 0 | 3 |
| 2 | 101 | 101 | 0 | 3 |
| 2 | 011 | 011 | 0 | 3 |
| 2 | 111 | 011 | 0 | 3 |

## Outcomes: RGO/LGO (Infield In)

**Logic:** Special logic for seasons 7+ when the infield is playing in. Applies to both RGO and LGO. The batter is out, and runners advance based on a specific set of rules designed to reflect the infield-in strategy.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 010 | 0 | 1 |
| 0 | 010 | 001 | 0 | 1 |
| 0 | 001 | 001 | 0 | 1 |
| 0 | 110 | 011 | 0 | 1 |
| 0 | 101 | 011 | 0 | 1 |
| 0 | 011 | 011 | 0 | 1 |
| 0 | 111 | 111 | 0 | 1 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 010 | 0 | 2 |
| 1 | 010 | 001 | 0 | 2 |
| 1 | 001 | 001 | 0 | 2 |
| 1 | 110 | 011 | 0 | 2 |
| 1 | 101 | 011 | 0 | 2 |
| 1 | 011 | 011 | 0 | 2 |
| 1 | 111 | 111 | 0 | 2 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 010 | 0 | 3 |
| 2 | 010 | 001 | 0 | 3 |
| 2 | 001 | 001 | 0 | 3 |
| 2 | 110 | 011 | 0 | 3 |
| 2 | 101 | 011 | 0 | 3 |
| 2 | 011 | 011 | 0 | 3 |
| 2 | 111 | 111 | 0 | 3 |

## Outcomes: DP

**Logic:** Generic Double Play. Primarily used in seasons before S4. In modern seasons, DPs are typically derived from LGO/RGO results.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 000 | 0 | 2 |
| 0 | 110 | 001 | 0 | 2 |
| 0 | 101 | 000 | 1 | 2 |
| 0 | 111 | 001 | 1 | 2 |
| 1 | 100 | 000 | 0 | 3 |
| 1 | 110 | 000 | 0 | 3 |
| 1 | 101 | 000 | 0 | 3 |
| 1 | 111 | 000 | 0 | 3 |

## Outcomes: TP

**Logic:** Generic Triple Play. In modern seasons, TPs are typically derived from LGO results with high diff.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 110 | 000 | 0 | 3 |
| 0 | 111 | 000 | 0 | 3 |

## Outcomes: CS 2B

**Logic:** Caught stealing 2nd. Runner on 1st is out.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 000 | 0 | 1 |
| 0 | 101 | 001 | 0 | 1 |
| 1 | 100 | 000 | 0 | 2 |
| 1 | 101 | 001 | 0 | 2 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 101 | 001 | 0 | 3 |

## Outcomes: CS 3B

**Logic:** Caught stealing 3rd. Runner on 2nd is out.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 010 | 000 | 0 | 1 |
| 0 | 110 | 100 | 0 | 1 |
| 1 | 010 | 000 | 0 | 2 |
| 1 | 110 | 100 | 0 | 2 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 110 | 100 | 0 | 3 |

## Outcomes: CS Home

**Logic:** Caught stealing home. Runner on 3rd is out.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 001 | 000 | 0 | 1 |
| 0 | 101 | 100 | 0 | 1 |
| 0 | 011 | 010 | 0 | 1 |
| 0 | 111 | 110 | 0 | 1 |
| 1 | 001 | 000 | 0 | 2 |
| 1 | 101 | 100 | 0 | 2 |
| 1 | 011 | 010 | 0 | 2 |
| 1 | 111 | 110 | 0 | 2 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 101 | 100 | 0 | 3 |
| 2 | 011 | 010 | 0 | 3 |
| 2 | 111 | 110 | 0 | 3 |

## Outcomes: CS

**Logic:** Caught stealing. Trailing runner is out.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 000 | 0 | 1 |
| 0 | 010 | 000 | 0 | 1 |
| 0 | 001 | 000 | 0 | 1 |
| 0 | 110 | 100 | 0 | 1 |
| 0 | 101 | 001 | 0 | 1 |
| 0 | 011 | 010 | 0 | 1 |
| 0 | 111 | 110 | 0 | 1 |
| 1 | 100 | 000 | 0 | 2 |
| 1 | 010 | 000 | 0 | 2 |
| 1 | 001 | 000 | 0 | 2 |
| 1 | 110 | 100 | 0 | 2 |
| 1 | 101 | 001 | 0 | 2 |
| 1 | 011 | 010 | 0 | 2 |
| 1 | 111 | 110 | 0 | 2 |
| 2 | 100 | 000 | 0 | 3 |
| 2 | 010 | 000 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 100 | 0 | 3 |
| 2 | 101 | 001 | 0 | 3 |
| 2 | 011 | 010 | 0 | 3 |
| 2 | 111 | 110 | 0 | 3 |

## Outcomes: SB

**Logic:** Generic Stolen Base. Only occurs in seasons 2 and 3. Runner successfully advances to the next base.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 100 | 010 | 0 | 0 |
| 0 | 010 | 001 | 0 | 0 |
| 0 | 001 | 000 | 1 | 0 |
| 0 | 110 | 101 | 0 | 0 |
| 0 | 101 | 011 | 0 | 0 |
| 0 | 011 | 010 | 1 | 0 |
| 0 | 111 | 110 | 1 | 0 |
| 1 | 100 | 010 | 0 | 1 |
| 1 | 010 | 001 | 0 | 1 |
| 1 | 001 | 000 | 1 | 1 |
| 1 | 110 | 101 | 0 | 1 |
| 1 | 101 | 011 | 0 | 1 |
| 1 | 011 | 010 | 1 | 1 |
| 1 | 111 | 110 | 1 | 1 |
| 2 | 100 | 010 | 0 | 2 |
| 2 | 010 | 001 | 0 | 2 |
| 2 | 001 | 000 | 1 | 2 |
| 2 | 110 | 101 | 0 | 2 |
| 2 | 101 | 011 | 0 | 2 |
| 2 | 011 | 010 | 1 | 2 |
| 2 | 111 | 110 | 1 | 2 |

## Outcomes: CMS 3B

**Logic:** Caught stealing 3rd (multiple runners). Trailing runner is out.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 110 | 010 | 0 | 1 |
| 1 | 110 | 010 | 0 | 2 |
| 2 | 110 | 010 | 0 | 3 |

## Outcomes: CMS Home

**Logic:** No specific logic explanation provided.

| Initial Outs | Initial Bases | Resulting Bases | Runs Scored | Resulting Outs |
|---|---|---|---|---|
| 0 | 000 | 000 | 0 | 1 |
| 0 | 100 | 100 | 0 | 1 |
| 0 | 010 | 010 | 0 | 1 |
| 0 | 001 | 000 | 0 | 1 |
| 0 | 110 | 110 | 0 | 1 |
| 0 | 101 | 010 | 0 | 1 |
| 0 | 011 | 001 | 0 | 1 |
| 0 | 111 | 011 | 0 | 1 |
| 1 | 000 | 000 | 0 | 2 |
| 1 | 100 | 100 | 0 | 2 |
| 1 | 010 | 010 | 0 | 2 |
| 1 | 001 | 000 | 0 | 2 |
| 1 | 110 | 110 | 0 | 2 |
| 1 | 101 | 010 | 0 | 2 |
| 1 | 011 | 001 | 0 | 2 |
| 1 | 111 | 011 | 0 | 2 |
| 2 | 000 | 000 | 0 | 3 |
| 2 | 100 | 100 | 0 | 3 |
| 2 | 010 | 010 | 0 | 3 |
| 2 | 001 | 000 | 0 | 3 |
| 2 | 110 | 110 | 0 | 3 |
| 2 | 101 | 010 | 0 | 3 |
| 2 | 011 | 001 | 0 | 3 |
| 2 | 111 | 011 | 0 | 3 |

