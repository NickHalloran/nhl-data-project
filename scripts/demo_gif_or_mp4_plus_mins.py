#!/usr/bin/env python3
"""Create a plus/minus race as either a GIF or an MP4."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nhl_pipeline.main import build_daily_point_race, create_bar_chart_race


INPUT_PATH = Path("data/processed/nhl_player_game_logs_20252026.parquet")
OUTPUT_DIR = Path("data/outputs")


def choose_format() -> str:
    """Prompt for a supported animation output format."""
    while True:
        selected = input("Choose output format (gif/mp4): ").strip().lower()
        if selected in {"gif", "mp4"}:
            return selected
        print("Please enter gif or mp4.")


def main() -> None:
    output_format = choose_format()
    output_path = OUTPUT_DIR / f"top_plus_minus_race.{output_format}"

    game_logs = pd.read_parquet(INPUT_PATH)
    if "player_name" not in game_logs.columns:
        game_logs["player_name"] = game_logs["player_id"].astype(str)

    plus_minus_input = game_logs[["game_date", "player_name", "team_abbrev", "plus_minus"]].rename(
        columns={"game_date": "date", "plus_minus": "points"}
    )
    race = build_daily_point_race(
        plus_minus_input,
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
        title="NHL Plus/Minus Leaders",
    )
    print(f"Requested {output_path} with {race['game_date'].nunique()} game-day frames.")


if __name__ == "__main__":
    main()