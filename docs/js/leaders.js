// Shared ranking/qualifier logic used by both the Leaderboards view and the
// per-cell league-leader styling on the player page. Pure data helpers, no DOM.

// Lower is better regardless of batting/pitching context
export const LOWER_IS_BETTER = new Set([
    'ERA', 'FIP', 'WHIP', 'H6', 'HR6', 'BB6', 'ERA-',
]);
// Lower is better only in batting context (e.g. K% = strikeout rate)
export const LOWER_IS_BETTER_BATTING = new Set(['GB%', 'GB/FB', 'K%', 'Avg Diff']);
// Lower is better only in pitching context (opponent stats)
export const LOWER_IS_BETTER_PITCHING = new Set([
    'BA', 'BABIP', 'BB%', 'FB%', 'HR%', 'OBP', 'OPS', 'RE24', 'SB%', 'SLG',
]);
export const CAN_BE_NEGATIVE = new Set(['WAR', 'WPA', 'RE24']);

// All-time qualifier defaults keyed by league (not adjustable by the user, but shown as editable input)
export const ALLTIME_DEFAULTS = {
    pa:  { mlr: 100, milr: 100, fcb: 10, mlr_playoff: 20, milr_playoff: 20, gib: 20 },
    ip:  { mlr: 50,  milr: 50,  fcb: 10, mlr_playoff: 10, milr_playoff: 10, gib: 20 },
    dec: { mlr: 10,  milr: 10,  fcb: 3,  mlr_playoff: 3,  milr_playoff: 3,  gib: 5  },
    sv:  { mlr: 10,  milr: 10,  fcb: 2,  mlr_playoff: 2,  milr_playoff: 2,  gib: 2  },
    att: { mlr: 20,  milr: 20,  fcb: 5,  mlr_playoff: 5,  milr_playoff: 5,  gib: 5  },
};

export function getAlltimeMin(key, league) {
    return ALLTIME_DEFAULTS[key]?.[league] ?? ALLTIME_DEFAULTS[key].mlr;
}

// Per-season qualifier defaults keyed by league (pre-fills the user-adjustable inputs on Leaderboards)
export const SEASON_DEFAULTS = {
    dec: { mlr: 3, milr: 3, fcb: 3, mlr_playoff: 2, milr_playoff: 2, gib: 3, eco: 2, npr: 3, wbc: 3 },
    sv:  { mlr: 3, milr: 3, fcb: 1, mlr_playoff: 1, milr_playoff: 1, gib: 1, eco: 1, npr: 1, wbc: 2 },
    att: { mlr: 5, milr: 5, fcb: 3, mlr_playoff: 3, milr_playoff: 3, gib: 3, eco: 1, npr: 1, wbc: 1 },
};

export function getSeasonMin(key, league) {
    return SEASON_DEFAULTS[key]?.[league] ?? SEASON_DEFAULTS[key].mlr;
}

// Converts a raw stat value (number, null/undefined, or the "Inf." sentinel) into a value
// usable in a numeric sort comparator. "Inf." is a real (extreme) value, not a missing one,
// so it always sorts as +Infinity — unlike null/undefined, which sorts toward whichever end
// of the list is "last" for the given direction (+1 = ascending, -1 = descending), so missing
// values stay out of the way regardless of sort direction.
export function sortableValue(v, direction) {
    if (v === 'Inf.') return Infinity;
    return v ?? (direction === 1 ? Infinity : -Infinity);
}

// direction: true = lower value is better for this stat in this batting/pitching context
export function lowerIsBetter(stat, isHitting) {
    return LOWER_IS_BETTER.has(stat)
        || (isHitting  && LOWER_IS_BETTER_BATTING.has(stat))
        || (!isHitting && LOWER_IS_BETTER_PITCHING.has(stat));
}

// ── Qualifying-row filters (shared with Leaderboards) ────────────────────────

export function filterCareer(data, stat, isHitting, isCounting, selTeam, selType, minAtt, minDec, atQualMin) {
    let rows = data.filter(r => r[stat] !== undefined && r[stat] !== null);

    if (selTeam) rows = rows.filter(r => r.Franchise === selTeam);
    if (selType) {
        if (isHitting) rows = rows.filter(r => r['Batting Type'] === selType);
        else           rows = rows.filter(r => r['Pitching Type'] === selType);
    }

    if (!isCounting) {
        if (stat === 'SB%') {
            rows = rows.filter(r => (r.SB || 0) + (r.CS || 0) >= (atQualMin ?? minAtt));
        } else if (stat === 'W-L%') {
            rows = rows.filter(r => (r.W || 0) + (r.L || 0) >= (atQualMin ?? minDec));
        } else if (stat === 'SV%') {
            rows = rows.filter(r => (r.OPP || 0) >= (atQualMin ?? 10));
        } else {
            if (isHitting) rows = rows.filter(r => (r.PA || 0) >= (atQualMin ?? 0));
            else           rows = rows.filter(r => (r.IP || 0) >= (atQualMin ?? 0));
        }
    }
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

export function filterSeasonRows(data, displaySeason, stat, isHitting, isCounting, selTeam, selType, minPA, minOuts, minAtt, minDec, minOpp, seasonGames) {
    let rows = data.filter(r => r[stat] !== undefined && r[stat] !== null
        && (selTeam ? r.Franchise === selTeam : !r.is_sub_row)
        && r['Display Season']?.startsWith('S'));
    if (displaySeason) rows = rows.filter(r => r['Display Season'] === displaySeason);
    if (selType) {
        if (isHitting) rows = rows.filter(r => r['Batting Type'] === selType);
        else           rows = rows.filter(r => r['Pitching Type (Main)'] === selType);
    }

    if (!isCounting) {
        rows = rows.filter(r => {
            const ds    = r['Display Season'];
            const games = seasonGames[ds] || 0;
            if (!games) return false;
            if (stat === 'SB%')  return (r.SB || 0) + (r.CS || 0) >= minAtt;
            if (stat === 'W-L%') return (r.W  || 0) + (r.L  || 0) >= minDec;
            if (stat === 'SV%')  return (r.OPP || 0) >= minOpp;
            if (isHitting) return (r.PA || 0) >= minPA * games;
            return Math.round((r.IP || 0) * 3) >= minOuts * games;
        });
    }
    if (isCounting && !CAN_BE_NEGATIVE.has(stat)) rows = rows.filter(r => (r[stat] || 0) > 0);
    return rows;
}

// ── Batch leader computation (used by the player page) ───────────────────────

// Given the full (all-players) season/career/team-hitting arrays for one
// league and the list of stat columns shown on the player page, returns:
//   { season: { [displaySeason]: { [stat]: Set<ID> } },
//     career: { [stat]: Set<ID> } }
// Only stats with at least one qualifying row get an entry, and the Set
// contains only the ID(s) of qualifying rows that hit the leading value —
// matching on raw value alone would wrongly flag a non-qualifying player
// whose small-sample stat happens to equal a qualifying leader's value
// (e.g. a 1-0 W-L% of 1.000 matching a qualifying 3-0 pitcher's 1.000).
export function computeLeagueLeaders(seasonData, careerData, teamHittingData, isHitting, statList, league, isCounting) {
    const minPA  = 2.0, minOuts = 3;
    const minAtt = getSeasonMin('att', league);
    const minDec = getSeasonMin('dec', league);
    const minOpp = getSeasonMin('sv',  league);

    const atMinAtt = getAlltimeMin('att', league);
    const atMinDec = getAlltimeMin('dec', league);
    const atMinPA  = getAlltimeMin('pa',  league);
    const atMinIP  = getAlltimeMin('ip',  league);

    // Bucket season rows by Display Season once (combined-team rows only).
    const bySeason = new Map();
    for (const r of seasonData) {
        const ds = r['Display Season'];
        if (!ds || !ds.startsWith('S') || r.is_sub_row) continue;
        if (!bySeason.has(ds)) bySeason.set(ds, []);
        bySeason.get(ds).push(r);
    }

    const seasonGames = {};
    for (const ds of bySeason.keys()) {
        seasonGames[ds] = teamHittingData
            .filter(r => r['Display Season'] === ds)
            .reduce((m, r) => Math.max(m, r.G || 0), 0);
    }

    const season = {};
    for (const [ds, rows] of bySeason) {
        const leaders = {};
        for (const stat of statList) {
            const counting = isCounting(stat);
            const direction = lowerIsBetter(stat, isHitting) ? 1 : -1;
            const qualRows = filterSeasonRows(
                rows, ds, stat, isHitting, counting,
                '', '', minPA, minOuts, minAtt, minDec, minOpp, seasonGames
            );
            if (!qualRows.length) continue;
            let best = qualRows[0][stat];
            for (const r of qualRows) {
                if (direction * (r[stat] - best) < 0) best = r[stat];
            }
            leaders[stat] = new Set(qualRows.filter(r => r[stat] === best).map(r => r.ID));
        }
        season[ds] = leaders;
    }

    const career = {};
    for (const stat of statList) {
        const counting = isCounting(stat);
        const direction = lowerIsBetter(stat, isHitting) ? 1 : -1;
        const atQualMin = counting ? undefined
            : stat === 'SB%'  ? atMinAtt
            : stat === 'W-L%' ? atMinDec
            : stat === 'SV%'  ? 10
            : isHitting ? atMinPA : atMinIP;
        const qualRows = filterCareer(careerData, stat, isHitting, counting, '', '', atMinAtt, atMinDec, atQualMin);
        if (!qualRows.length) continue;
        let best = qualRows[0][stat];
        for (const r of qualRows) {
            if (direction * (r[stat] - best) < 0) best = r[stat];
        }
        career[stat] = new Set(qualRows.filter(r => r[stat] === best).map(r => r.ID));
    }

    return { season, career };
}
