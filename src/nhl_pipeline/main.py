"""Minimal NHL data pipeline entry point.

This project now connects to the live NHL standings API, normalizes the
response into a dataframe, writes it to Parquet, and executes a DuckDB
query to display the top teams.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

import duckdb
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests_cache
from requests import Session

from .team_colors import add_team_colors, get_team_color


CACHE_NAME = "nhl_cache"
CACHE_EXPIRE_SECONDS = 86400
BASE_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
BASE_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger(__name__)


def create_cached_session(cache_name: str = CACHE_NAME, expire_after_seconds: int = CACHE_EXPIRE_SECONDS) -> Session:
    """Create a requests-cache session for NHL API calls."""
    session = requests_cache.CachedSession(
        cache_name,
        expire_after=expire_after_seconds,
        backend="sqlite",
        allowable_methods=("GET",),
    )
    session.headers.update({"User-Agent": "nhl-data-extraction/1.0"})
    LOGGER.info("Created cached session %s expiring after %s seconds", cache_name, expire_after_seconds)
    return session


def _safe_dict_value(payload: Any, key: str) -> str | None:
    value = payload.get(key) if isinstance(payload, dict) else None
    if isinstance(value, dict):
        return value.get("default") or value.get("fr") or value.get("en")
    return value


def fetch_current_standings(session: Session | None = None, team_abbrev: str | None = None) -> pd.DataFrame:
    """Fetch the current NHL standings and flatten the record set into a DataFrame."""
    active_session = session or create_cached_session()
    response = active_session.get("https://api-web.nhle.com/v1/standings/now")
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("standings", [])

    if not rows:
        raise ValueError("The NHL standings endpoint returned no rows.")

    normalized_rows: list[dict[str, Any]] = []
    for row in rows:
        normalized_rows.append(
            {
                "team_name": _safe_dict_value(row, "teamName") or _safe_dict_value(row, "teamCommonName") or "",
                "team_common_name": _safe_dict_value(row, "teamCommonName") or "",
                "team_abbrev": _safe_dict_value(row, "teamAbbrev") or "",
                "conference_name": row.get("conferenceName"),
                "division_name": row.get("divisionName"),
                "games_played": row.get("gamesPlayed"),
                "wins": row.get("wins"),
                "losses": row.get("losses"),
                "ot_losses": row.get("otLosses"),
                "points": row.get("points"),
                "goal_differential": row.get("goalDifferential"),
                "goals_for": row.get("goalFor"),
                "goals_against": row.get("goalAgainst"),
                "points_pct": row.get("pointPctg"),
                "win_pct": row.get("winPctg"),
                "season_id": row.get("seasonId"),
                "date": row.get("date"),
            }
        )

    frame = pd.DataFrame(normalized_rows)
    if "date" in frame.columns:
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

    if team_abbrev is not None:
        frame = frame[frame["team_abbrev"].str.upper() == team_abbrev.upper()]
    return frame


def export_standings(frame: pd.DataFrame, parquet_path: Path | str | None = None) -> Path:
    """Persist the standings to a parquet file in the project data directory."""
    target = Path(parquet_path) if parquet_path is not None else BASE_DATA_DIR / "nhl_standings_now.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, target)
    LOGGER.info("Exported %d standings rows to %s", len(frame), target)
    return target


def export_player_stats(frame: pd.DataFrame, parquet_path: Path | str | None = None) -> Path:
    """Persist player stats to a parquet file in the project data directory."""
    target = Path(parquet_path) if parquet_path is not None else BASE_DATA_DIR / "nhl_player_stats.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, target)
    LOGGER.info("Exported %d player stats rows to %s", len(frame), target)
    return target


def export_goalie_stats(frame: pd.DataFrame, parquet_path: Path | str | None = None) -> Path:
    """Persist goalie stats to a parquet file in the project data directory."""
    target = Path(parquet_path) if parquet_path is not None else BASE_DATA_DIR / "nhl_goalie_stats.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, target)
    LOGGER.info("Exported %d goalie stats rows to %s", len(frame), target)
    return target


def get_standings_schema_sql(table_name: str = "nhl_standings") -> str:
    """Return the canonical DuckDB schema for standings data."""
    return f"""
        CREATE TABLE {table_name} (
            team_name VARCHAR,
            team_common_name VARCHAR,
            team_abbrev VARCHAR,
            conference_name VARCHAR,
            division_name VARCHAR,
            games_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            ot_losses INTEGER,
            points INTEGER,
            goal_differential INTEGER,
            goals_for INTEGER,
            goals_against INTEGER,
            points_pct DOUBLE,
            win_pct DOUBLE,
            season_id INTEGER,
            date DATE
        )
    """.strip()


def get_player_stats_schema_sql(table_name: str = "nhl_player_stats") -> str:
    """Return the schema for season-level player statistics."""
    return f"""
        CREATE TABLE {table_name} (
            player_id INTEGER,
            player_name VARCHAR,
            team_abbrev VARCHAR,
            season_id INTEGER,
            games_played INTEGER,
            goals INTEGER,
            assists INTEGER,
            points INTEGER,
            plus_minus INTEGER,
            shots INTEGER,
            penalty_minutes INTEGER,
            time_on_ice_per_game DOUBLE,
            shooting_pct DOUBLE
        )
    """.strip()


def get_goalie_stats_schema_sql(table_name: str = "nhl_goalie_stats") -> str:
    """Return the schema for season-level goalie statistics."""
    return f"""
        CREATE TABLE {table_name} (
            goalie_id INTEGER,
            goalie_name VARCHAR,
            team_abbrev VARCHAR,
            season_id INTEGER,
            games_played INTEGER,
            wins INTEGER,
            losses INTEGER,
            ot_losses INTEGER,
            saves INTEGER,
            goals_against INTEGER,
            shots_against INTEGER,
            save_pct DOUBLE,
            goals_against_average DOUBLE
        )
    """.strip()


def query_top_teams(frame: pd.DataFrame, limit: int = 32, team_abbrev: str | None = None) -> pd.DataFrame:
    """Load standings into DuckDB using the project schema and query the top teams."""
    connection = duckdb.connect()
    try:
        schema_sql = get_standings_schema_sql()
        connection.execute(schema_sql)
        connection.register("standings_source", frame)
        connection.execute("DELETE FROM nhl_standings")
        connection.execute("INSERT INTO nhl_standings SELECT * FROM standings_source")

        query = """
            SELECT
                team_abbrev,
                team_name,
                points,
                wins,
                losses,
                ot_losses,
                goal_differential
            FROM nhl_standings
            WHERE (? IS NULL OR upper(team_abbrev) = upper(?))
            ORDER BY points DESC, wins DESC
            LIMIT ?
        """
        return add_team_colors(connection.execute(query, [team_abbrev, team_abbrev, limit]).fetchdf())
    finally:
        connection.close()


def query_conference_leaders(frame: pd.DataFrame, limit: int = 32) -> pd.DataFrame:
    """Return the top N teams per conference using the standings schema."""
    connection = duckdb.connect()
    try:
        connection.execute(get_standings_schema_sql())
        connection.register("standings_source", frame)
        connection.execute("DELETE FROM nhl_standings")
        connection.execute("INSERT INTO nhl_standings SELECT * FROM standings_source")

        query = """
            WITH ranked AS (
                SELECT
                    conference_name,
                    team_abbrev,
                    team_name,
                    points,
                    wins,
                    losses,
                    ROW_NUMBER() OVER (
                        PARTITION BY conference_name
                        ORDER BY points DESC, wins DESC, team_abbrev ASC
                    ) AS conference_rank
                FROM nhl_standings
            )
            SELECT *
            FROM ranked
            WHERE conference_rank <= ?
            ORDER BY conference_name, conference_rank, team_abbrev
        """
        return add_team_colors(connection.execute(query, [limit]).fetchdf())
    finally:
        connection.close()


def build_daily_point_race(
    frame: pd.DataFrame,
    top_n: int = 20,
    season_start: str | pd.Timestamp | None = None,
    season_end: str | pd.Timestamp | None = None,
    date_step: str = "calendar",
) -> pd.DataFrame:
    """Build cumulative point rankings for every calendar day in a season.

    This is the query pattern needed for a bar-chart-race visualization of the
    season's top point leaders, without introducing Matplotlib yet.
    """
    required_columns = {"date", "player_name", "team_abbrev", "points"}
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise ValueError(f"Daily point race input is missing required columns: {missing}")

    dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
    if dates.empty:
        return pd.DataFrame()
    start = pd.Timestamp(season_start) if season_start is not None else dates.min()
    end = pd.Timestamp(season_end) if season_end is not None else dates.max()
    if start > end:
        raise ValueError("season_start must be on or before season_end")
    if date_step not in {"calendar", "game_day"}:
        raise ValueError("date_step must be either 'calendar' or 'game_day'")

    if date_step == "game_day":
        calendar_sql = """
            SELECT DISTINCT CAST(date AS DATE) AS date
            FROM daily_input
            WHERE CAST(date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
        """
    else:
        calendar_sql = """
            SELECT CAST(day AS DATE) AS date
            FROM generate_series(CAST(? AS DATE), CAST(? AS DATE), INTERVAL 1 DAY) AS dates(day)
        """

    connection = duckdb.connect()
    try:
        connection.register("daily_input", frame)
        query = """
            WITH players AS (
                SELECT DISTINCT player_name, team_abbrev
                FROM daily_input
            ),
            calendar AS (
                {calendar_sql}
            ),
            daily_totals AS (
                SELECT
                    CAST(date AS DATE) AS date,
                    player_name,
                    team_abbrev,
                    SUM(points) AS points
                FROM daily_input
                GROUP BY 1, 2, 3
            ),
            cumulative AS (
                SELECT
                    calendar.date,
                    players.player_name,
                    players.team_abbrev,
                    SUM(COALESCE(daily_totals.points, 0)) OVER (
                        PARTITION BY players.player_name
                        ORDER BY calendar.date
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) AS points
                FROM calendar
                CROSS JOIN players
                LEFT JOIN daily_totals
                    ON daily_totals.date = calendar.date
                    AND daily_totals.player_name = players.player_name
                    AND daily_totals.team_abbrev = players.team_abbrev
            ),
            ranked AS (
                SELECT
                    date,
                    player_name,
                    team_abbrev,
                    points,
                    ROW_NUMBER() OVER (
                        PARTITION BY date
                        ORDER BY points DESC, player_name ASC
                    ) AS rank
                FROM cumulative
            )
            SELECT *
            FROM ranked
            WHERE rank <= ?
            ORDER BY date, rank, player_name
        """
        return add_team_colors(
            connection.execute(query.format(calendar_sql=calendar_sql), [start.date(), end.date(), top_n]).fetchdf()
        )
    finally:
        connection.close()


def query_team_top_scorers(frame: pd.DataFrame, team_abbrev: str, limit: int = 20) -> pd.DataFrame:
    """Return the top N scorers for a specific team using DuckDB ranking logic."""
    required_columns = {"player_name", "team_abbrev", "points"}
    missing = sorted(required_columns - set(frame.columns))
    if missing:
        raise ValueError(f"Team scorer input is missing required columns: {missing}")

    connection = duckdb.connect()
    try:
        connection.register("player_stats_source", frame)
        query = """
            WITH ranked AS (
                SELECT
                    player_name,
                    team_abbrev,
                    points,
                    ROW_NUMBER() OVER (
                        ORDER BY points DESC, player_name ASC
                    ) AS rank
                FROM player_stats_source
                WHERE upper(team_abbrev) = upper(?)
            )
            SELECT *
            FROM ranked
            WHERE rank <= ?
            ORDER BY rank
        """
        return add_team_colors(connection.execute(query, [team_abbrev, limit]).fetchdf())
    finally:
        connection.close()


def fetch_roster_by_team(team_abbrev: str, season_id: int, session: Session | None = None) -> pd.DataFrame:
    """Fetch the full roster for a single NHL team and flatten it into a DataFrame."""
    active_session = session or create_cached_session()
    response = active_session.get(f"https://api-web.nhle.com/v1/roster/{team_abbrev}/{season_id}")
    response.raise_for_status()
    payload = response.json()

    rows: list[dict[str, Any]] = []
    for group_name in ("forwards", "defensemen", "goalies"):
        for player in payload.get(group_name, []):
            rows.append(
                {
                    "player_id": player.get("id"),
                    "first_name": _safe_dict_value(player, "firstName") or "",
                    "last_name": _safe_dict_value(player, "lastName") or "",
                    "team_abbrev": team_abbrev.upper(),
                    "position_code": player.get("positionCode") or player.get("position") or "",
                    "shoots_catches": player.get("shootsCatches") or "",
                    "height_in_inches": player.get("heightInInches"),
                    "weight_in_pounds": player.get("weightInPounds"),
                    "sweater_number": player.get("sweaterNumber"),
                    "season_id": season_id,
                    "roster_group": group_name,
                }
            )

    return pd.DataFrame(rows)


def extract_all_team_player_profiles(team_abbrevs: list[str], season_id: int, session: Session | None = None) -> pd.DataFrame:
    """Fetch and combine the roster rows for all team abbreviations in the provided list."""
    frames: list[pd.DataFrame] = []
    for team_abbrev in team_abbrevs:
        frame = fetch_roster_by_team(team_abbrev, season_id, session=session)
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_player_profile(player_id: int, session: Session | None = None) -> dict[str, Any]:
    """Fetch the NHL player landing payload for a single player."""
    active_session = session or create_cached_session()
    response = active_session.get(f"https://api-web.nhle.com/v1/player/{player_id}/landing")
    response.raise_for_status()
    payload = response.json()
    if not payload:
        raise ValueError(f"No player payload returned for id {player_id}")
    return payload


def normalize_player_profile(payload: dict[str, Any], season_id: int | None = None) -> dict[str, Any]:
    """Normalize a player landing payload into the canonical player schema row."""
    featured = payload.get("featuredStats") or {}
    career_totals = payload.get("careerTotals") or {}
    current_team = payload.get("currentTeamAbbrev") or ""
    season = season_id if season_id is not None else payload.get("seasonId")

    return {
        "player_id": payload.get("playerId"),
        "player_name": f"{_safe_dict_value(payload, 'firstName') or ''} {_safe_dict_value(payload, 'lastName') or ''}".strip(),
        "team_abbrev": current_team,
        "season_id": season,
        "games_played": featured.get("games") or career_totals.get("games") or 0,
        "goals": featured.get("goals") or career_totals.get("goals") or 0,
        "assists": featured.get("assists") or career_totals.get("assists") or 0,
        "points": featured.get("points") or career_totals.get("points") or 0,
        "plus_minus": featured.get("plusMinus") or career_totals.get("plusMinus") or 0,
        "shots": featured.get("shots") or career_totals.get("shots") or 0,
        "penalty_minutes": featured.get("pim") or career_totals.get("pim") or 0,
        "time_on_ice_per_game": featured.get("timeOnIcePerGame") or career_totals.get("timeOnIcePerGame") or 0.0,
        "shooting_pct": featured.get("shootingPctg") or career_totals.get("shootingPctg") or 0.0,
    }


def normalize_goalie_profile(payload: dict[str, Any], season_id: int | None = None) -> dict[str, Any]:
    """Normalize a player landing payload into the canonical goalie schema row."""
    featured = payload.get("featuredStats") or {}
    career_totals = payload.get("careerTotals") or {}
    current_team = payload.get("currentTeamAbbrev") or ""
    season = season_id if season_id is not None else payload.get("seasonId")

    return {
        "goalie_id": payload.get("playerId"),
        "goalie_name": f"{_safe_dict_value(payload, 'firstName') or ''} {_safe_dict_value(payload, 'lastName') or ''}".strip(),
        "team_abbrev": current_team,
        "season_id": season,
        "games_played": featured.get("games") or career_totals.get("games") or 0,
        "wins": featured.get("wins") or career_totals.get("wins") or 0,
        "losses": featured.get("losses") or career_totals.get("losses") or 0,
        "ot_losses": featured.get("otLosses") or career_totals.get("otLosses") or 0,
        "saves": featured.get("saves") or career_totals.get("saves") or 0,
        "goals_against": featured.get("goalsAgainst") or career_totals.get("goalsAgainst") or 0,
        "shots_against": featured.get("shotsAgainst") or career_totals.get("shotsAgainst") or 0,
        "save_pct": featured.get("savePctg") or career_totals.get("savePctg") or 0.0,
        "goals_against_average": featured.get("goalsAgainstAverage") or career_totals.get("goalsAgainstAverage") or 0.0,
    }


def fetch_full_season_player_stats(player_id: int, season_id: int, session: Session | None = None) -> dict[str, Any]:
    """Fetch and normalize full-season player statistics for a specific season.

    Uses the player landing payload, which includes featured stats (current season)
    and career totals. Normalizes using the player schema.
    """
    payload = fetch_player_profile(player_id, session=session)
    normalized = normalize_player_profile(payload, season_id=season_id)
    return normalized


def fetch_full_season_goalie_stats(goalie_id: int, season_id: int, session: Session | None = None) -> dict[str, Any]:
    """Fetch and normalize full-season goalie statistics for a specific season.

    Uses the player landing payload for a goalie, which includes featured stats
    (current season) and career totals. Normalizes using the goalie schema.
    """
    payload = fetch_player_profile(goalie_id, session=session)
    normalized = normalize_goalie_profile(payload, season_id=season_id)
    return normalized


def extract_all_team_season_player_stats(team_abbrevs: list[str], season_id: int, session: Session | None = None) -> pd.DataFrame:
    """Fetch roster for all teams, then extract full-season player stats for each player.

    Returns a DataFrame with all player stats from the provided team list.
    """
    active_session = session or create_cached_session()
    roster = extract_all_team_player_profiles(team_abbrevs, season_id, session=active_session)

    if roster.empty:
        return pd.DataFrame()

    # Filter to non-goalie players
    players = roster[roster["position_code"] != "G"]
    if players.empty:
        return pd.DataFrame()

    stats_rows: list[dict[str, Any]] = []
    for _, player_row in players.iterrows():
        player_id = player_row["player_id"]
        try:
            stats = fetch_full_season_player_stats(player_id, season_id, session=active_session)
            stats_rows.append(stats)
        except Exception as e:
            LOGGER.warning(f"Failed to fetch player stats for {player_id}: {e}")
            continue

    if not stats_rows:
        return pd.DataFrame()
    return pd.DataFrame(stats_rows)


def extract_all_team_season_goalie_stats(team_abbrevs: list[str], season_id: int, session: Session | None = None) -> pd.DataFrame:
    """Fetch roster for all teams, then extract full-season goalie stats for each goalie.

    Returns a DataFrame with all goalie stats from the provided team list.
    """
    active_session = session or create_cached_session()
    roster = extract_all_team_player_profiles(team_abbrevs, season_id, session=active_session)

    if roster.empty:
        return pd.DataFrame()

    # Filter to goalies only
    goalies = roster[roster["position_code"] == "G"]
    if goalies.empty:
        return pd.DataFrame()

    stats_rows: list[dict[str, Any]] = []
    for _, goalie_row in goalies.iterrows():
        goalie_id = goalie_row["player_id"]
        try:
            stats = fetch_full_season_goalie_stats(goalie_id, season_id, session=active_session)
            stats_rows.append(stats)
        except Exception as e:
            LOGGER.warning(f"Failed to fetch goalie stats for {goalie_id}: {e}")
            continue

    if not stats_rows:
        return pd.DataFrame()
    return pd.DataFrame(stats_rows)


def fetch_player_game_log(player_id: int, season_id: int, game_type_id: int = 2, session: Session | None = None) -> pd.DataFrame:
    """Fetch game-by-game logs for a single player for a specific season.

    Args:
        player_id: NHL player ID
        season_id: Season (e.g., 20252026)
        game_type_id: 2 for regular season, 3 for playoffs
        session: Optional requests session

    Returns:
        DataFrame with one row per game, including game_date, goals, assists, points, etc.
    """
    active_session = session or create_cached_session()
    response = active_session.get(f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/{game_type_id}")
    response.raise_for_status()
    payload = response.json()

    game_log = payload.get("gameLog", [])
    if not game_log:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for game in game_log:
        rows.append({
            "game_id": game.get("gameId"),
            "player_id": player_id,
            "game_date": game.get("gameDate"),
            "team_abbrev": game.get("teamAbbrev"),
            "opponent_abbrev": game.get("opponentAbbrev"),
            "home_away": "HOME" if game.get("homeRoadFlag") == "H" else "AWAY",
            "goals": game.get("goals", 0),
            "assists": game.get("assists", 0),
            "points": game.get("points", 0),
            "plus_minus": game.get("plusMinus", 0),
            "shots": game.get("shots", 0),
            "penalty_minutes": game.get("pim", 0),
            "time_on_ice": game.get("toi"),
            "season_id": season_id,
        })

    frame = pd.DataFrame(rows)
    if not frame.empty and "game_date" in frame.columns:
        frame["game_date"] = pd.to_datetime(frame["game_date"], errors="coerce")
    return frame


def extract_all_player_game_logs(player_ids: list[int], season_id: int, session: Session | None = None) -> pd.DataFrame:
    """Fetch game logs for multiple players and combine into a single DataFrame."""
    active_session = session or create_cached_session()
    frames: list[pd.DataFrame] = []

    for player_id in player_ids:
        try:
            logs = fetch_player_game_log(player_id, season_id, session=active_session)
            if not logs.empty:
                frames.append(logs)
        except Exception as e:
            LOGGER.warning(f"Failed to fetch game logs for player {player_id}: {e}")
            continue

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_daily_cumulative_stat(
    game_logs: pd.DataFrame,
    stat_column: str = "points",
    top_n: int = 20,
) -> pd.DataFrame:
    """Transform game logs into daily cumulative values for a top-N statistic.

    Groups games by date, calculates cumulative points for each player,
    and returns only the top N players by final season total.

    Returns a DataFrame with one row per player per date showing cumulative points up to that date.
    """
    if game_logs.empty:
        return pd.DataFrame()
    if stat_column not in game_logs.columns:
        raise ValueError(f"Game logs are missing statistic column: {stat_column}")

    # Ensure game_date is datetime
    game_logs = game_logs.copy()
    game_logs["game_date"] = pd.to_datetime(game_logs["game_date"], errors="coerce")
    game_logs = game_logs.dropna(subset=["game_date"])

    # If no player_name column, try to create one from player_id or use it directly
    if "player_name" not in game_logs.columns:
        game_logs["player_name"] = game_logs["player_id"].astype(str)

    # Get final season totals to identify top N players
    season_totals = game_logs.groupby("player_name").agg({
        stat_column: "sum",
        "team_abbrev": "first",
        "player_id": "first"
    }).reset_index()
    season_totals = season_totals.nlargest(top_n, stat_column)
    top_player_names = set(season_totals["player_name"])

    # Filter to top players only
    filtered = game_logs[game_logs["player_name"].isin(top_player_names)].copy()

    # Sort by date and calculate cumulative
    filtered = filtered.sort_values("game_date")
    filtered["cumulative_points"] = filtered.groupby("player_name")[stat_column].cumsum()

    # Return only necessary columns, sorted
    result = filtered[["game_date", "player_name", "team_abbrev", "cumulative_points"]].copy()
    return add_team_colors(result.sort_values(["game_date", "player_name"]))


def build_daily_cumulative_points(game_logs: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Transform game logs into daily cumulative points for top-N leaders."""
    return build_daily_cumulative_stat(game_logs, stat_column="points", top_n=top_n)


def choose_animation_format() -> str:
    """Prompt for a supported animation output format."""
    while True:
        selected = input("Choose output format (gif/mp4): ").strip().lower()
        if selected in {"gif", "mp4"}:
            return selected
        print("Please enter gif or mp4.")


def animation_output_path(output_path: Path | str, output_format: str) -> Path:
    """Return an animation path with the requested GIF or MP4 extension."""
    if output_format not in {"gif", "mp4"}:
        raise ValueError("output_format must be either 'gif' or 'mp4'")
    return Path(output_path).with_suffix(f".{output_format}")


def format_bar_label(player_name: object, team_abbrev: object) -> str:
    """Format a race label as ``Player Name (TEAM)``."""
    name = str(player_name)
    team = str(team_abbrev) if pd.notna(team_abbrev) else ""
    return f"{name} ({team})" if team else name


def create_bar_chart_race(
    daily_points: pd.DataFrame,
    output_path: Path | str | None = None,
    fps: int = 10,
    top_n: int = 20,
    title: str = "NHL Point Leaders",
    value_format: str = "{:.0f}",
    xlim: tuple[float, float] | None = None,
    frame_duration_ms: int | None = None,
    target_duration_seconds: float | None = None,
) -> None:
    """Create a bar chart race animation showing top point leaders throughout the season.

    Args:
        daily_points: DataFrame from build_daily_cumulative_points with columns:
                     game_date, player_id, player_name, team_abbrev, cumulative_points
        output_path: Optional path to save the animation as MP4/GIF
        fps: Frames per second for the animation
        frame_duration_ms: Optional delay between frames. Overrides ``fps``.
        target_duration_seconds: Optional total animation duration. Cannot be
            combined with ``frame_duration_ms``.
    """
    if daily_points.empty:
        LOGGER.warning("No data provided for bar chart race")
        return
    if frame_duration_ms is not None and frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be greater than zero")
    if target_duration_seconds is not None and target_duration_seconds <= 0:
        raise ValueError("target_duration_seconds must be greater than zero")
    if frame_duration_ms is not None and target_duration_seconds is not None:
        raise ValueError("Choose either frame_duration_ms or target_duration_seconds, not both")

    # Ensure datetime
    daily_points["game_date"] = pd.to_datetime(daily_points["game_date"], errors="coerce")

    # Get unique dates and prepare data
    dates = sorted(daily_points["game_date"].unique())
    if frame_duration_ms is not None:
        output_fps = 1000 / frame_duration_ms
        frame_interval_ms = frame_duration_ms
    elif target_duration_seconds is not None:
        output_fps = len(dates) / target_duration_seconds
        frame_interval_ms = 1000 / output_fps
    else:
        output_fps = fps
        frame_interval_ms = 1000 / fps

    # Use player names for display if available, otherwise use ID
    if "player_name" not in daily_points.columns:
        daily_points["player_name"] = daily_points["player_id"].astype(str)

    fig, ax = plt.subplots(figsize=(12, 8))

    def update_frame(date_idx: int) -> list:
        """Update frame for a specific date."""
        ax.clear()

        current_date = dates[date_idx]
        data_at_date = daily_points[daily_points["game_date"] == current_date].copy()

        # Get latest cumulative points for each player up to this date
        latest = data_at_date.sort_values("game_date").groupby("player_name").agg({
            "cumulative_points": "last",
            "team_abbrev": "first"
        }).reset_index()

        # Sort and get the requested number of leaders.
        latest = latest.nlargest(top_n, "cumulative_points")
        latest = latest.sort_values("cumulative_points")
        latest["display_name"] = latest.apply(
            lambda row: format_bar_label(row["player_name"], row["team_abbrev"]),
            axis=1,
        )

        # Create horizontal bar chart
        colors = latest["team_abbrev"].map(get_team_color).tolist()
        bars = ax.barh(latest["display_name"], latest["cumulative_points"], color=colors)

        # Add value labels on bars.
        for i, (name, points) in enumerate(zip(latest["player_name"], latest["cumulative_points"])):
            label_offset = (xlim[1] - xlim[0]) * 0.01 if xlim is not None else 0.5
            offset = label_offset if points >= 0 else -label_offset
            alignment = "left" if points >= 0 else "right"
            ax.text(points + offset, i, value_format.format(points), va="center", ha=alignment, fontsize=9)

        ax.set_xlabel("Cumulative Points", fontsize=12, fontweight="bold")
        ax.set_title(f"Top {top_n} {title} - {current_date.strftime('%Y-%m-%d')}",
                    fontsize=14, fontweight="bold")
        if xlim is None:
            minimum_value = daily_points["cumulative_points"].min()
            maximum_value = daily_points["cumulative_points"].max()
            padding = max(1, (maximum_value - minimum_value) * 0.1)
            ax.set_xlim(minimum_value - padding, maximum_value + padding)
        else:
            ax.set_xlim(*xlim)

        return list(bars)

    # Create animation
    num_frames = len(dates)
    anim = animation.FuncAnimation(
        fig, update_frame,
        frames=num_frames,
        interval=frame_interval_ms,
        repeat=True,
        blit=False
    )

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = "pillow" if output_path.suffix.lower() == ".gif" else "ffmpeg"
        try:
            anim.save(str(output_path), writer=writer, fps=output_fps)
            LOGGER.info(f"Saved bar chart race animation to {output_path}")
        except Exception as e:
            if writer == "ffmpeg":
                LOGGER.warning(f"Failed to save MP4 animation: {e}. Install FFmpeg or choose GIF output.")
            else:
                LOGGER.warning(f"Failed to save GIF animation: {e}. Verify Pillow is installed.")
    else:
        plt.show()

    plt.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch live NHL standings and query the top teams.")
    parser.add_argument("--limit", type=int, default=32, help="Number of teams to return in the top query.")
    parser.add_argument("--team", type=str, default=None, help="Optional team abbreviation filter, like COL or CAR.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    standings = fetch_current_standings(create_cached_session(), team_abbrev=args.team)
    LOGGER.info("Fetched %s standings rows", len(standings))
    top_teams = query_top_teams(standings, limit=args.limit, team_abbrev=args.team)
    print(top_teams.to_string(index=False))


if __name__ == "__main__":
    main()
