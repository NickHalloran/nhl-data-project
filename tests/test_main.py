from __future__ import annotations

import duckdb
import pandas as pd

from nhl_pipeline.team_colors import DEFAULT_TEAM_COLOR, TEAM_COLORS, add_team_colors, get_team_color
from nhl_pipeline.main import (
    build_daily_cumulative_points,
    build_daily_point_race,
    extract_all_team_player_profiles,
    extract_all_team_season_goalie_stats,
    extract_all_team_season_player_stats,
    fetch_current_standings,
    fetch_full_season_goalie_stats,
    fetch_full_season_player_stats,
    fetch_player_game_log,
    fetch_player_profile,
    fetch_roster_by_team,
    get_goalie_stats_schema_sql,
    get_player_stats_schema_sql,
    get_standings_schema_sql,
    normalize_goalie_profile,
    normalize_player_profile,
    query_conference_leaders,
    query_team_top_scorers,
)


def test_team_colors_are_stable_and_case_insensitive():
    assert get_team_color("COL") == TEAM_COLORS["COL"]
    assert get_team_color("dal") == TEAM_COLORS["DAL"]
    assert get_team_color("unknown") == DEFAULT_TEAM_COLOR

    colored = add_team_colors(pd.DataFrame({"team_abbrev": ["COL", "DAL"]}))
    assert colored["team_color"].tolist() == [TEAM_COLORS["COL"], TEAM_COLORS["DAL"]]


def test_fetch_current_standings_returns_rows():
    standings = fetch_current_standings()
    assert not standings.empty
    assert {"team_name", "team_abbrev", "points", "wins", "losses"}.issubset(set(standings.columns))
    assert standings["points"].notna().all()


def test_schema_sql_is_valid_and_creates_table():
    sql = get_standings_schema_sql()
    normalized = " ".join(sql.lower().split())
    assert "create table nhl_standings" in normalized
    assert "team_abbrev" in normalized
    assert "points" in normalized

    connection = duckdb.connect()
    try:
        connection.execute(sql)
        tables = connection.execute("SHOW TABLES").fetchall()
        assert any(name == "nhl_standings" for (name,) in tables)
    finally:
        connection.close()


def test_query_conference_leaders_returns_ranked_rows():
    results = query_conference_leaders(fetch_current_standings(), limit=3)
    assert not results.empty
    assert "conference_name" in results.columns
    assert "conference_rank" in results.columns
    assert "team_color" in results.columns
    assert (results["conference_rank"] <= 3).all()


def test_player_and_goalie_schemas_are_valid_and_daily_race_ranks_top_n():
    player_sql = get_player_stats_schema_sql()
    goalie_sql = get_goalie_stats_schema_sql()
    assert "create table nhl_player_stats" in " ".join(player_sql.lower().split())
    assert "player_id" in player_sql.lower()
    assert "create table nhl_goalie_stats" in " ".join(goalie_sql.lower().split())
    assert "save_pct" in goalie_sql.lower()

    profile = fetch_player_profile(8478402)
    player_row = normalize_player_profile(profile)
    goalie_row = normalize_goalie_profile(profile)

    assert player_row["player_id"] == 8478402
    assert player_row["player_name"] == "Connor McDavid"
    assert goalie_row["goalie_id"] == 8478402
    assert goalie_row["goalie_name"] == "Connor McDavid"

    daily = pd.DataFrame(
        [
            {"date": "2025-10-12", "player_name": "A", "team_abbrev": "COL", "points": 3, "goals": 1},
            {"date": "2025-10-12", "player_name": "B", "team_abbrev": "DAL", "points": 5, "goals": 2},
            {"date": "2025-10-13", "player_name": "A", "team_abbrev": "COL", "points": 6, "goals": 2},
            {"date": "2025-10-13", "player_name": "C", "team_abbrev": "BUF", "points": 4, "goals": 1},
        ]
    )
    rankings = build_daily_point_race(daily, top_n=2)
    assert not rankings.empty
    assert {"date", "player_name", "team_abbrev", "team_color", "points", "rank"}.issubset(set(rankings.columns))
    assert (rankings["rank"] <= 2).all()


def test_query_team_top_scorers_returns_ranked_player_rows():
    players = pd.DataFrame(
        [
            {"player_id": 1, "player_name": "A", "team_abbrev": "COL", "points": 70, "goals": 25, "assists": 45},
            {"player_id": 2, "player_name": "B", "team_abbrev": "COL", "points": 62, "goals": 18, "assists": 44},
            {"player_id": 3, "player_name": "C", "team_abbrev": "DAL", "points": 68, "goals": 30, "assists": 38},
        ]
    )
    result = query_team_top_scorers(players, "COL", limit=2)
    assert not result.empty
    assert list(result["team_abbrev"]) == ["COL", "COL"]
    assert result["team_color"].eq(TEAM_COLORS["COL"]).all()
    assert list(result["player_name"]) == ["A", "B"]
    assert result["rank"].tolist() == [1, 2]


def test_fetch_roster_by_team_and_extract_all_team_player_profiles():
    roster = fetch_roster_by_team("COL", 20252026)
    assert not roster.empty
    assert {"player_id", "first_name", "last_name", "team_abbrev", "position_code"}.issubset(set(roster.columns))
    assert roster["team_abbrev"].eq("COL").all()

    combined = extract_all_team_player_profiles(["COL", "DAL"], season_id=20252026)
    assert not combined.empty
    assert {"player_id", "team_abbrev", "position_code"}.issubset(set(combined.columns))
    assert set(combined["team_abbrev"].unique()) <= {"COL", "DAL"}


def test_fetch_full_season_player_and_goalie_stats_from_live_roster():
    roster = fetch_roster_by_team("EDM", 20252026)
    assert not roster.empty

    player_row = roster[roster["position_code"] != "G"].iloc[0]
    goalie_row = roster[roster["position_code"] == "G"].iloc[0]

    player_stats = fetch_full_season_player_stats(player_row["player_id"], 20252026)
    goalie_stats = fetch_full_season_goalie_stats(goalie_row["player_id"], 20252026)

    assert player_stats["player_id"] == player_row["player_id"]
    assert player_stats["season_id"] == 20252026
    assert player_stats["points"] >= 0

    assert goalie_stats["goalie_id"] == goalie_row["player_id"]
    assert goalie_stats["season_id"] == 20252026
    assert 0.0 <= goalie_stats["save_pct"] <= 1.0


def test_extract_all_team_season_stats_returns_player_and_goalie_dfs():
    team_list = ["EDM", "COL"]
    player_stats = extract_all_team_season_player_stats(team_list, season_id=20252026)
    goalie_stats = extract_all_team_season_goalie_stats(team_list, season_id=20252026)

    assert not player_stats.empty
    assert {"player_id", "team_abbrev", "points", "season_id"}.issubset(set(player_stats.columns))
    assert all(player_stats["season_id"] == 20252026)

    assert not goalie_stats.empty
    assert {"goalie_id", "team_abbrev", "save_pct", "season_id"}.issubset(set(goalie_stats.columns))
    assert all(goalie_stats["season_id"] == 20252026)


def test_fetch_player_game_log_returns_game_by_game_data():
    # Connor McDavid ID
    game_log = fetch_player_game_log(8478402, season_id=20252026)
    assert not game_log.empty
    assert {"game_date", "player_id", "team_abbrev", "points", "goals", "assists"}.issubset(set(game_log.columns))
    assert all(game_log["player_id"] == 8478402)
    assert all(game_log["season_id"] == 20252026)
    # Regular season has 82 games
    assert len(game_log) == 82


def test_build_daily_cumulative_points_creates_ranking_dataset():
    # Create mock game logs
    game_logs = pd.DataFrame({
        "game_date": pd.date_range("2025-10-10", periods=20),
        "player_name": ["Player A"] * 10 + ["Player B"] * 10,
        "team_abbrev": ["COL"] * 20,
        "player_id": [1] * 10 + [2] * 10,
        "points": [1, 0, 2, 1, 1, 0, 1, 2, 1, 0] + [2, 2, 1, 0, 1, 2, 0, 1, 1, 2],
    })

    daily = build_daily_cumulative_points(game_logs, top_n=2)

    assert not daily.empty
    assert {"game_date", "player_name", "team_color", "cumulative_points"}.issubset(set(daily.columns))
    # Should have both players
    assert set(daily["player_name"].unique()) == {"Player A", "Player B"}
    # Cumulative should be increasing
    assert all(daily.groupby("player_name")["cumulative_points"].apply(
        lambda x: (x.diff() >= 0).all() or (x.diff().iloc[1:] >= 0).all()
    ))


def test_build_daily_point_race_can_use_game_days_only():
    daily_input = pd.DataFrame(
        [
            {"date": "2025-10-07", "player_name": "A", "team_abbrev": "COL", "points": 1},
            {"date": "2025-10-09", "player_name": "A", "team_abbrev": "COL", "points": 2},
        ]
    )

    race = build_daily_point_race(
        daily_input,
        top_n=1,
        season_start="2025-10-07",
        season_end="2025-10-10",
        date_step="game_day",
    )

    assert list(race["date"].dt.strftime("%Y-%m-%d").unique()) == ["2025-10-07", "2025-10-09"]
