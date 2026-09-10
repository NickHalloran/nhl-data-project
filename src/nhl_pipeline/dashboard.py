"""Shared Streamlit layout for NHL race dashboard pages."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

RACE_PAGES = (
    (
        "Primary Races",
        (
            ("Top Goals", "top_goals.gif"),
            ("Top Points", "top_points.gif"),
            ("Team Points", "top_team_points.gif"),
            ("Team Goal Differential", "top_team_goal_differential.gif"),
        ),
    ),
    (
        "Skater Races",
        (
            ("Top Assists", "top_assists.gif"),
            ("Top Hits", "top_hits.gif"),
            ("Top Penalty Minutes", "top_pims.gif"),
            ("Top Plus/Minus", "top_plus_minus_race.gif"),
        ),
    ),
    (
        "Goalie Races",
        (
            ("Top Scorers Race", "top_scorers_race.gif"),
            ("Goalies by Goals Against", "top_goalie_goals_against.gif"),
            ("Goalies by Save Percentage", "top_goalie_save_percentage.gif"),
            ("Goalies by Shots Faced", "top_goalie_shots_faced.gif"),
        ),
    ),
    (
        "Query Races",
        (
            ("Daily Point Leaders", "query_daily_point_race.gif"),
            ("Daily Team Point Leaders", "query_top_teams_race.gif"),
            ("Conference Team Leaders", "query_conference_leaders_race.gif"),
            ("Team Top Scorers", "query_team_top_scorers_race.gif"),
        ),
    ),
)


def _media_markup(path: Path, title: str) -> str:
    """Return browser markup for an animation file."""
    media_type = "video/mp4" if path.suffix.lower() == ".mp4" else "image/gif"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    if media_type == "video/mp4":
        return (
            f'<video autoplay loop muted controls aria-label="{title}" '
            f'style="width:100%; height:100%; object-fit:contain;">'
            f'<source src="data:{media_type};base64,{encoded}" type="{media_type}">'
            "</video>"
        )
    return (
        f'<img src="data:{media_type};base64,{encoded}" alt="{title}" '
        'style="width:100%; height:100%; object-fit:contain;">'
    )


def _race_card(title: str, filename: str) -> str:
    """Build one dashboard card, including a missing-file state."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        return (
            '<section class="race-card missing">'
            f"<h2>{title}</h2>"
            f"<p>Generate <code>{filename}</code> to populate this panel.</p>"
            "</section>"
        )
    return (
        '<section class="race-card">'
        f"<h2>{title}</h2>"
        f'<div class="race-media">{_media_markup(path, title)}</div>'
        "</section>"
    )


def render_race_page(page_title: str, races: tuple[tuple[str, str], ...]) -> None:
    """Render one four-panel race page."""
    st.set_page_config(page_title=f"{page_title} | NHL Dashboard", page_icon="🏒", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { max-width: 1700px; padding-top: 2rem; }
        .race-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            grid-template-rows: repeat(4, minmax(180px, 1fr));
            gap: 1rem;
            min-height: 760px;
        }
        .race-card {
            grid-column: span 2;
            grid-row: span 2;
            overflow: hidden;
            border: 1px solid rgba(128, 128, 128, 0.35);
            border-radius: 0.6rem;
            background: rgba(128, 128, 128, 0.08);
            padding: 0.65rem;
        }
        .race-card h2 { margin: 0 0 0.45rem 0; font-size: 1.05rem; }
        .race-media { height: calc(100% - 2rem); display: flex; align-items: center; justify-content: center; }
        .race-card.missing { padding: 1rem; }
        .race-card.missing p { color: rgba(128, 128, 128, 0.95); }
        @media (max-width: 900px) {
            .race-grid { display: block; min-height: 0; }
            .race-card { min-height: 360px; margin-bottom: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title(page_title)
    st.caption("Animated NHL leaders and team races")
    cards = "".join(_race_card(title, filename) for title, filename in races)
    st.markdown(f'<div class="race-grid">{cards}</div>', unsafe_allow_html=True)
