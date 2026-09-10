#!/usr/bin/env python3
"""Generate full-season top-20 player, goalie, and team stat races.

The NHL player game-log endpoint does not expose hits or goalie statistics.
This script uses the cached gamecenter boxscores, where those daily values are
available, and renders every calendar day in the regular season.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from nhl_pipeline.main import (
    animation_output_path,
    build_daily_point_race,
    choose_animation_format,
    create_bar_chart_race,
    create_cached_session,
)


INPUT_PATH = Path("data/processed/nhl_player_game_logs_20252026.parquet")
OUTPUT_DIR = Path("data/outputs")
PROCESSED_DIR = Path("data/processed")
SKATER_STATS_PATH = PROCESSED_DIR / "nhl_daily_skater_boxscore_stats_20252026.parquet"
GOALIE_STATS_PATH = PROCESSED_DIR / "nhl_daily_goalie_boxscore_stats_20252026.parquet"
TEAM_STATS_PATH = PROCESSED_DIR / "nhl_daily_team_boxscore_stats_20252026.parquet"
SEASON_START = "2025-10-07"
SEASON_END = "2026-04-16"


def fetch_boxscore_stats(game_logs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch daily skater, goalie, and team values from each season boxscore."""
    session = create_cached_session()
    skater_rows: list[dict] = []
    goalie_rows: list[dict] = []
    team_rows: list[dict] = []
    for game_id in game_logs["game_id"].dropna().unique():
        payload = session.get(f"https://api-web.nhle.com/v1/gamecenter/{int(game_id)}/boxscore").json()
        game_date = payload.get("gameDate")
        teams = {side: payload.get(side, {}) for side in ("homeTeam", "awayTeam")}
        stats = payload.get("playerByGameStats", {})
        for side, team in teams.items():
            abbrev = team.get("abbrev", "")
            score = int(team.get("score") or 0)
            opponent = teams["awayTeam" if side == "homeTeam" else "homeTeam"]
            opponent_score = int(opponent.get("score") or 0)
            last_period = payload.get("gameOutcome", {}).get("lastPeriodType", "REG")
            team_rows.append({
                "date": game_date,
                "player_name": abbrev,
                "team_abbrev": abbrev,
                "points": 2 if score > opponent_score else (1 if last_period != "REG" else 0),
                "goal_differential": score - opponent_score,
            })
            for group in ("forwards", "defense"):
                for player in stats.get(side, {}).get(group, []):
                    skater_rows.append({
                        "date": game_date,
                        "player_id": player.get("playerId"),
                        "player_name": player.get("name", {}).get("default", str(player.get("playerId"))),
                        "team_abbrev": abbrev,
                        "hits": player.get("hits") or 0,
                        "pims": player.get("pim") or 0,
                        "assists": player.get("assists") or 0,
                        "goals": player.get("goals") or 0,
                    })
            for goalie in stats.get(side, {}).get("goalies", []):
                goalie_rows.append({
                    "date": game_date,
                    "player_name": goalie.get("name", {}).get("default", str(goalie.get("playerId"))),
                    "team_abbrev": abbrev,
                    "saves": goalie.get("saves") or 0,
                    "shots_faced": goalie.get("shotsAgainst") or 0,
                    "goals_against": goalie.get("goalsAgainst") or 0,
                })
    return pd.DataFrame(skater_rows), pd.DataFrame(goalie_rows), pd.DataFrame(team_rows)


def additive_race(
    frame: pd.DataFrame,
    value_column: str,
    output_name: str,
    title: str,
    top_n: int = 20,
    output_format: str | None = None,
) -> None:
    """Build and save a calendar-day cumulative race for an additive stat."""
    input_frame = frame[["date", "player_name", "team_abbrev", value_column]].rename(
        columns={value_column: "points"}
    )
    race = build_daily_point_race(
        input_frame,
        top_n=top_n,
        season_start=SEASON_START,
        season_end=SEASON_END,
        date_step="game_day",
    )
    race = race.rename(columns={"date": "game_date", "points": "cumulative_points"})
    selected_format = output_format or choose_animation_format()
    output_path = animation_output_path(OUTPUT_DIR / output_name, selected_format)
    create_bar_chart_race(race, output_path, fps=5, top_n=top_n, title=title)
    print(f"Saved {output_path} ({race['game_date'].nunique()} calendar-day frames)")


def save_percentage_race(goalies: pd.DataFrame, output_format: str | None = None) -> None:
    """Render a rolling season save percentage race.

    Each frame uses cumulative saves divided by cumulative shots faced, which
    is the standard season save-percentage calculation as of that date.
    """
    saves = build_daily_point_race(
        goalies[["date", "player_name", "team_abbrev", "saves"]].rename(columns={"saves": "points"}),
        top_n=len(goalies), season_start=SEASON_START, season_end=SEASON_END, date_step="game_day",
    )
    shots = build_daily_point_race(
        goalies[["date", "player_name", "team_abbrev", "shots_faced"]].rename(columns={"shots_faced": "points"}),
        top_n=len(goalies), season_start=SEASON_START, season_end=SEASON_END, date_step="game_day",
    )
    keys = ["date", "player_name", "team_abbrev"]
    race = saves.merge(shots, on=keys, suffixes=("_saves", "_shots"))
    race["season_save_percentage"] = (
        pd.to_numeric(race["points_saves"], errors="coerce")
        / pd.to_numeric(race["points_shots"], errors="coerce").replace(0, float("nan"))
    ).fillna(0.0)
    race["rank"] = race.groupby("date")["season_save_percentage"].rank(method="first", ascending=False)
    race = race[race["rank"] <= 20].rename(
        columns={"date": "game_date", "season_save_percentage": "cumulative_points"}
    )
    selected_format = output_format or choose_animation_format()
    output_path = animation_output_path(OUTPUT_DIR / "top_goalie_save_percentage.gif", selected_format)
    create_bar_chart_race(
        race, output_path, fps=5, top_n=20,
        title="Goalies by Rolling Season Save Percentage",
        value_format="{:.1%}",
        xlim=(0.0, 1.0),
    )
    print(f"Saved {output_path} ({race['game_date'].nunique()} calendar-day frames)")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_format = choose_animation_format()
    game_logs = pd.read_parquet(INPUT_PATH)
    if all(path.exists() for path in (SKATER_STATS_PATH, GOALIE_STATS_PATH, TEAM_STATS_PATH)):
        skaters = pd.read_parquet(SKATER_STATS_PATH)
        goalies = pd.read_parquet(GOALIE_STATS_PATH)
        teams = pd.read_parquet(TEAM_STATS_PATH)
    else:
        skaters, goalies, teams = fetch_boxscore_stats(game_logs)
        skaters.to_parquet(SKATER_STATS_PATH, index=False)
        goalies.to_parquet(GOALIE_STATS_PATH, index=False)
        teams.to_parquet(TEAM_STATS_PATH, index=False)

    for column, filename, title in (
        ("hits", "top_hits.gif", "NHL Hit Leaders"),
        ("pims", "top_pims.gif", "NHL Penalty-Minute Leaders"),
        ("assists", "top_assists.gif", "NHL Assist Leaders"),
        ("goals", "top_goals.gif", "NHL Goal Leaders"),
    ):
        additive_race(skaters, column, filename, title, output_format=output_format)

    save_percentage_race(goalies, output_format=output_format)
    goalie_values = (
        ("goals_against", "top_goalie_goals_against.gif", "Goalies by Goals Against"),
        ("shots_faced", "top_goalie_shots_faced.gif", "Goalies by Shots Faced"),
    )
    for column, filename, title in goalie_values:
        additive_race(goalies, column, filename, title, output_format=output_format)

    additive_race(teams, "points", "top_team_points.gif", "NHL Teams by Points", top_n=32, output_format=output_format)
    additive_race(teams, "goal_differential", "top_team_goal_differential.gif", "NHL Teams by Goal Differential", top_n=32, output_format=output_format)


if __name__ == "__main__":
    main()