#!/usr/bin/env python3
"""Create the full-season top-20 points bar chart race."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nhl_pipeline.main import (
    animation_output_path,
    build_daily_point_race,
    choose_animation_format,
    create_bar_chart_race,
)


INPUT_PATH = Path("data/processed/nhl_player_game_logs_20252026.parquet")
OUTPUT_PATH = Path("data/outputs/top_points.gif")


def main() -> None:
    output_path = animation_output_path(OUTPUT_PATH, choose_animation_format())
    game_logs = pd.read_parquet(INPUT_PATH)
    if "player_name" not in game_logs.columns:
        game_logs["player_name"] = game_logs["player_id"].astype(str)

    point_input = game_logs[["game_date", "player_name", "team_abbrev", "points"]].rename(
        columns={"game_date": "date"}
    )
    race = build_daily_point_race(
        point_input,
        top_n=20,
        season_start="2025-10-07",
        season_end="2026-04-16",
        date_step="game_day",
    ).rename(columns={"date": "game_date", "points": "cumulative_points"})
    create_bar_chart_race(
        race,
        output_path=output_path,
        fps=5,
        top_n=20,
        title="NHL Point Leaders",
    )
    print(f"Saved {output_path} with {race['game_date'].nunique()} calendar-day frames.")


if __name__ == "__main__":
    main()