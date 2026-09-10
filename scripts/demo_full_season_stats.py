#!/usr/bin/env python3
"""Demo script showing full-season player/goalie stat extraction and querying.

This script demonstrates:
1. Extracting roster data for multiple NHL teams
2. Fetching full-season player and goalie stats for each player
3. Exporting to parquet files
4. Running DuckDB queries to find top scorers
"""

from __future__ import annotations

import logging
from pathlib import Path

from nhl_pipeline.main import (
    create_cached_session,
    export_goalie_stats,
    export_player_stats,
    extract_all_team_season_goalie_stats,
    extract_all_team_season_player_stats,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)


def demo_full_season_extraction() -> None:
    """Extract and export full-season stats for multiple NHL teams."""
    LOGGER.info("Starting full-season stat extraction demo...")

    season_id = 20252026

    # Extract for a subset of teams (can be expanded to all 32)
    teams = ["EDM", "COL", "DAL", "LAK", "NYR"]
    LOGGER.info(f"Extracting stats for teams: {', '.join(teams)}")

    session = create_cached_session()

    # Extract player stats
    LOGGER.info("Fetching player stats...")
    player_stats = extract_all_team_season_player_stats(teams, season_id, session=session)
    if not player_stats.empty:
        LOGGER.info(f"Extracted {len(player_stats)} player records")
        export_player_stats(player_stats)

        # Show top scorers
        top_scorers = player_stats.nlargest(20, "points")[["player_name", "team_abbrev", "goals", "assists", "points"]]
        print("\n=== Top 20 Scorers ===")
        print(top_scorers.to_string(index=False))
    else:
        LOGGER.warning("No player stats extracted")

    # Extract goalie stats
    LOGGER.info("Fetching goalie stats...")
    goalie_stats = extract_all_team_season_goalie_stats(teams, season_id, session=session)
    if not goalie_stats.empty:
        LOGGER.info(f"Extracted {len(goalie_stats)} goalie records")
        export_goalie_stats(goalie_stats)

        # Show best goalies by save percentage
        best_goalies = goalie_stats.nlargest(20, "save_pct")[["goalie_name", "team_abbrev", "games_played", "wins", "save_pct"]]
        print("\n=== Top 20 Goalies (by Save %) ===")
        print(best_goalies.to_string(index=False))
    else:
        LOGGER.warning("No goalie stats extracted")

    LOGGER.info("Demo complete!")


if __name__ == "__main__":
    demo_full_season_extraction()
