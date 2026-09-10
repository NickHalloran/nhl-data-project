"""Stable NHL team colors used by query results and visualizations."""

from __future__ import annotations

import pandas as pd


TEAM_COLORS: dict[str, str] = {
    "ANA": "#FC4C02",
    "BOS": "#FFB81C",
    "BUF": "#003087",
    "CGY": "#D2001C",
    "CAR": "#CC0000",
    "CHI": "#CF0A2C",
    "COL": "#6F263D",
    "CBJ": "#002654",
    "DAL": "#006847",
    "DET": "#CE1126",
    "EDM": "#041E42",
    "FLA": "#C8102E",
    "LAK": "#A2AAAD",
    "MIN": "#154734",
    "MTL": "#AF1E2D",
    "NSH": "#FFB81C",
    "NJD": "#CE1126",
    "NYI": "#00539B",
    "NYR": "#0038A8",
    "OTT": "#C52032",
    "PHI": "#F74902",
    "PIT": "#FCB514",
    "SJS": "#006D75",
    "SEA": "#001628",
    "STL": "#002F87",
    "TBL": "#002868",
    "TOR": "#00205B",
    "UTA": "#6CACE4",
    "VAN": "#00205B",
    "VGK": "#B4975A",
    "WPG": "#041E42",
    "WSH": "#C8102E",
}

DEFAULT_TEAM_COLOR = "#6B7280"


def get_team_color(team_abbrev: str | None) -> str:
    """Return the stable color for a team abbreviation."""
    if not isinstance(team_abbrev, str):
        return DEFAULT_TEAM_COLOR
    return TEAM_COLORS.get(team_abbrev.upper(), DEFAULT_TEAM_COLOR)


def add_team_colors(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of a result frame with a derived ``team_color`` column."""
    if "team_abbrev" not in frame.columns:
        raise ValueError("Team color enrichment requires a team_abbrev column")

    colored = frame.copy()
    colored["team_color"] = colored["team_abbrev"].map(get_team_color)
    return colored
