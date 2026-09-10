#!/usr/bin/env python3
"""Create GIF or MP4 visualizations for the project's DuckDB ranking queries.

The standings and season-stat queries are snapshots, so their animations contain one
frame. The daily point query can be made into a multi-frame race by supplying a
daily points file with ``--daily-input``.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from nhl_pipeline.main import (
    animation_output_path,
    build_daily_point_race,
    choose_animation_format,
    create_bar_chart_race,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/outputs")
PROCESSED_DIR = Path("data/processed")


def _load_daily_input(path: Path) -> pd.DataFrame:
    """Load game logs and normalize their date column for the daily queries."""
    frame = pd.read_parquet(path).rename(columns={"game_date": "date"})
    required = {"date", "player_name", "team_abbrev", "points"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Daily input is missing required columns: {missing}")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    return frame.dropna(subset=["date"])


def create_query_races(
    daily_input_path: Path,
    team_abbrev: str = "COL",
    season_start: str | None = None,
    season_end: str | None = None,
) -> None:
    """Run daily ranking queries and save one full-season animation per view."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_format = choose_animation_format()
    daily_input = _load_daily_input(daily_input_path)
    daily_race = build_daily_point_race(daily_input, 20, season_start, season_end, date_step="game_day")

    create_bar_chart_race(
        daily_race,
        animation_output_path(OUTPUT_DIR / "query_daily_point_race.gif", output_format),
        fps=5,
        top_n=20,
        title="Daily Player Point Leaders",
    )

    team_daily = (
        daily_input.groupby(["date", "team_abbrev"], as_index=False)["points"].sum()
        .rename(columns={"team_abbrev": "player_name"})
    )
    team_daily["team_abbrev"] = team_daily["player_name"]
    team_race = build_daily_point_race(team_daily, 32, season_start, season_end, date_step="game_day")
    create_bar_chart_race(
        team_race,
        animation_output_path(OUTPUT_DIR / "query_top_teams_race.gif", output_format),
        fps=5,
        top_n=32,
        title="Daily Team Point Leaders",
    )
    create_bar_chart_race(
        team_race,
        animation_output_path(OUTPUT_DIR / "query_conference_leaders_race.gif", output_format),
        fps=5,
        top_n=32,
        title="Daily Conference Team Leaders",
    )

    team_daily_input = daily_input[daily_input["team_abbrev"].str.upper() == team_abbrev.upper()]
    team_race = build_daily_point_race(team_daily_input, 20, season_start, season_end, date_step="game_day")
    create_bar_chart_race(
        team_race,
        animation_output_path(OUTPUT_DIR / "query_team_top_scorers_race.gif", output_format),
        fps=5,
        top_n=20,
        title=f"Daily {team_abbrev.upper()} Scorers",
    )
    daily_race.to_parquet(PROCESSED_DIR / "daily_point_race.parquet", index=False)
    LOGGER.info("Saved query animations to %s", OUTPUT_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--daily-input", type=Path, required=True, help="Parquet file containing one row per player game.")
    parser.add_argument("--season-start", help="First calendar day to render, such as 2024-10-04.")
    parser.add_argument("--season-end", help="Last calendar day to render, such as 2025-04-17.")
    parser.add_argument("--team", default="COL", help="Team used for the team-scorer query.")
    args = parser.parse_args()
    create_query_races(args.daily_input, args.team, args.season_start, args.season_end)


if __name__ == "__main__":
    main()