import pandas as pd
import os


def correct_neutral_results(df, player_info):
    """
    Applies corrections to the 'Result at Neutral' column based on specific criteria.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Load definition files
    try:
        batting_types_df = pd.read_csv(
            os.path.join(
                script_dir, "..", "data", "player_type_definitions", "batting_types.csv"
            )
        ).set_index("Type")
        pitching_types_df = pd.read_csv(
            os.path.join(
                script_dir,
                "..",
                "data",
                "player_type_definitions",
                "pitching_types.csv",
            )
        ).set_index("Type")
        hand_bonus_df = pd.read_csv(
            os.path.join(
                script_dir,
                "..",
                "data",
                "player_type_definitions",
                "pitching_hand_bonus.csv",
            )
        ).set_index("Type")
    except FileNotFoundError as e:
        print(f"Error loading player type definition files: {e}")
        print("Skipping neutral result correction.")
        return df

    seasons_to_correct = ["S-8", "S8", "S9", "S10", "S11"]

    # --- BEFORE ---
    season_mask = df["Season"].isin(seasons_to_correct)
    before_counts = df.loc[season_mask, "Result at Neutral"].value_counts()
    before_fo = before_counts.get("FO", 0)
    before_bb = before_counts.get("BB", 0)

    # Filter for specified seasons and where 'Result at Neutral' is 'FO'.
    correction_target_mask = df["Season"].isin(seasons_to_correct) & (
        df["Result at Neutral"] == "FO"
    )

    if not correction_target_mask.any():
        print("No rows found that require neutral result correction analysis.")
        return df

    # Apply player info for relevant columns
    df["Hitter Batting Type"] = df["Hitter ID"].map(
        lambda x: player_info.get(x, {}).get("batting_type")
    )
    df["Hitter Hand"] = df["Hitter ID"].map(
        lambda x: player_info.get(x, {}).get("handedness")
    )
    df["Pitcher Pitching Type"] = df["Pitcher ID"].map(
        lambda x: player_info.get(x, {}).get("pitching_type")
    )
    df["Pitcher Hand"] = df["Pitcher ID"].map(
        lambda x: player_info.get(x, {}).get("handedness")
    )

    # Extract Pitcher Hand Bonus and clean Pitcher Pitching Type
    def get_pitcher_details(pitching_type):
        if isinstance(pitching_type, str) and "-" in pitching_type:
            parts = pitching_type.split("-")
            return parts[0], parts[-1]
        return pitching_type, None

    df[["Clean Pitcher Pitching Type", "Pitcher Hand Bonus"]] = df[
        "Pitcher Pitching Type"
    ].apply(lambda x: pd.Series(get_pitcher_details(x)))

    # Ensure 'Diff' is a numeric type for comparison
    df["Diff"] = pd.to_numeric(df["Diff"], errors="coerce")

    num_to_analyze = correction_target_mask.sum()
    print(
        f"Analyzing {num_to_analyze} rows in seasons {', '.join(seasons_to_correct)} where 'Result at Neutral' is 'FO' for potential corrections."
    )

    corrections = []

    # Iterate over the subset of rows that need correction
    for index, row in df[correction_target_mask].iterrows():
        hitter_type = row["Hitter Batting Type"]
        pitcher_type = row["Clean Pitcher Pitching Type"]
        hitter_hand = row["Hitter Hand"]
        pitcher_hand = row["Pitcher Hand"]
        pitcher_hand_bonus_type = row["Pitcher Hand Bonus"]
        diff = row["Diff"]

        # Skip if necessary info is missing
        if pd.isna(hitter_type) or pd.isna(pitcher_type) or pd.isna(diff):
            continue

        try:
            batter_stats = batting_types_df.loc[hitter_type]
            pitcher_stats = pitching_types_df.loc[pitcher_type]

            total_stats = batter_stats.add(pitcher_stats, fill_value=0)

            if (
                hitter_hand == pitcher_hand
                and hitter_hand in ["R", "L"]
                and pd.notna(pitcher_hand_bonus_type)
            ):
                bonus_stats = hand_bonus_df.loc[pitcher_hand_bonus_type]
                total_stats = total_stats.add(bonus_stats, fill_value=0)

            # Ensure no range is negative
            total_stats[total_stats < 0] = 0

            cumulative_range = 0
            determined_result = None
            for outcome, range_val in total_stats.items():
                cumulative_range += range_val
                if diff < cumulative_range:
                    determined_result = outcome
                    break

            if determined_result and determined_result != row["Result at Neutral"]:
                corrections.append((index, determined_result))

        except KeyError:
            # This will catch errors if a batter/pitcher type is not in the definition files
            continue

    if corrections:
        print(f"Applying {len(corrections)} corrections to 'Result at Neutral'...")
        # Create a Series with the corrections, indexed by the DataFrame index
        correction_series = pd.Series(dict(corrections))
        # Update the DataFrame in one go
        df.loc[correction_series.index, "Result at Neutral"] = correction_series

        # --- AFTER ---
        after_counts = df.loc[season_mask, "Result at Neutral"].value_counts()
        after_fo = after_counts.get("FO", 0)
        after_bb = after_counts.get("BB", 0)

        # --- PRINT SUMMARY ---
        print("\n--- Neutral Result Correction Summary ---")
        print(f"Seasons corrected: {', '.join(seasons_to_correct)}")
        print(f"Total rows changed: {len(corrections)}")
        print("\n'Result at Neutral' counts BEFORE correction:")
        print(f"  - FO: {before_fo}")
        print(f"  - BB: {before_bb}")
        print("\n'Result at Neutral' counts AFTER correction:")
        print(f"  - FO: {after_fo}")
        print(f"  - BB: {after_bb}")
        print("-----------------------------------------\n")
    else:
        print("No corrections were necessary.")

    # Clean up added columns
    df.drop(
        columns=[
            "Hitter Batting Type",
            "Hitter Hand",
            "Pitcher Pitching Type",
            "Pitcher Hand",
            "Clean Pitcher Pitching Type",
            "Pitcher Hand Bonus",
        ],
        inplace=True,
    )

    return df
