"""Primary page for the NHL bar-chart-race dashboard."""

from __future__ import annotations

from nhl_pipeline.dashboard import RACE_PAGES, render_race_page


render_race_page(RACE_PAGES[0][0], RACE_PAGES[0][1])