"""Query race dashboard page."""

from nhl_pipeline.dashboard import RACE_PAGES, render_race_page


render_race_page(RACE_PAGES[3][0], RACE_PAGES[3][1])
