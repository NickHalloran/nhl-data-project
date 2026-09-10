#!/usr/bin/env python3
"""Demo script showing the bar chart race animation of top 20 point leaders.

This script demonstrates:
1. Extracting roster data
2. Fetching game logs for each player
3. Building daily cumulative points
4. Creating a bar chart race animation
"""

from __future__ import annotations

import logging
from pathlib import Path

from nhl_pipeline.main import (
    animation_output_path,
    build_daily_cumulative_stat,
    choose_animation_format,
    create_bar_chart_race,
    extract_all_player_game_logs,
    extract_all_team_player_profiles,
    create_cached_session,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)


def demo_bar_chart_race() -> None:
    """Create a bar chart race animation of top 20 point leaders."""
    LOGGER.info("Starting bar chart race demo...")

    season_id = 20252026

    # Step 1: Extract rosters for multiple teams
    # 8 team lightweight test with ~150 players
    # teams = ["EDM", "COL", "DAL", "LAK", "NYR", "TOR", "VAN", "BUF"]
    # Full 32 team extraction with ~800 players
    teams = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL",
    "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NSH",
    "NJD", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WSH", "WPG"
]

#print(f"Total teams: {len(teams)}")  # Outputs: 32

    LOGGER.info(f"Fetching rosters for {len(teams)} teams...")
    session = create_cached_session()

    roster = extract_all_team_player_profiles(teams, season_id, session=session)
    if roster.empty:
        LOGGER.error("No roster data extracted")
        return

    LOGGER.info(f"Extracted {len(roster)} players from {len(teams)} teams")

    # Step 2: Fetch game logs for all players
    player_ids = roster["player_id"].unique().tolist()
    LOGGER.info(f"Fetching game logs for {len(player_ids)} players...")

    game_logs = extract_all_player_game_logs(player_ids, season_id, session=session)
    if game_logs.empty:
        LOGGER.error("No game log data extracted")
        return

    LOGGER.info(f"Extracted {len(game_logs)} game records")

    # Merge player names from roster
    game_logs = game_logs.merge(
        roster[["player_id", "first_name", "last_name"]].drop_duplicates(),
        on="player_id",
        how="left"
    )
    game_logs["player_name"] = game_logs["first_name"].fillna("") + " " + game_logs["last_name"].fillna("")
    game_logs["player_name"] = game_logs["player_name"].str.strip()

    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    game_logs.to_parquet(output_dir / f"nhl_player_game_logs_{season_id}.parquet", index=False)

    # Step 3: Build daily cumulative points
    LOGGER.info("Building daily cumulative points dataset...")
    daily_points = build_daily_cumulative_stat(game_logs, stat_column="plus_minus", top_n=20)

    if daily_points.empty:
        LOGGER.error("No daily points data")
        return

    LOGGER.info(f"Built dataset with {len(daily_points)} records for {daily_points['player_name'].nunique()} players")

    # Show preview
    print("\n=== Sample Daily Points Data (Top 5) ===")
    print(daily_points.tail(10).to_string(index=False))

    # Step 4: Create bar chart race animation
    LOGGER.info("Creating bar chart race animation...")
    output_path = animation_output_path(output_dir / "top_scorers_race.gif", choose_animation_format())
    try:
        create_bar_chart_race(
            daily_points,
            output_path=output_path,
            fps=5,
            top_n=20,
            title="NHL Plus/Minus Leaders",
        )
        LOGGER.info(f"Saved animation to {output_path}")
    except Exception as e:
        LOGGER.warning(f"Failed to save GIF: {e}")
        LOGGER.info("Displaying animation instead...")
        create_bar_chart_race(daily_points)

    LOGGER.info("Demo complete!")


if __name__ == "__main__":
    demo_bar_chart_race()
