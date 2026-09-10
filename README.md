# NHL Data Project

An NHL data extraction and visualization project built around the NHL web API,
Pandas, DuckDB, PyArrow, and Matplotlib. The current project can extract NHL
rosters, season statistics, and game-by-game logs, then turn daily statistics
into animated bar-chart races.

The project is currently a Python-based pipeline and collection of runnable
demo scripts. A future phase may add an interactive Streamlit application.

## Current Capabilities

- Fetch current NHL standings through a cached HTTP session.
- Extract player and goalie season statistics for selected teams.
- Extract player game logs for a season.
- Build daily or game-day cumulative rankings with DuckDB.
- Generate animated bar-chart races for player, goalie, and team statistics.
- Save animations as GIF or MP4 files.
- Display primary races in a Streamlit dashboard.
- Persist analytical datasets as Parquet files.
- Run automated tests with `pytest`.

## Requirements

- Python 3.13 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Streamlit, installed by `uv sync --dev`
- FFmpeg on `PATH` when creating MP4 files
- Network access for NHL API extraction and the live API tests

The project package is named `nhl-pipeline` and the source package path is
`src/nhl_pipeline/`.

## Setup

From the project root:

```bash
uv sync --dev
```

This creates or updates the local virtual environment and installs runtime and
development dependencies, including `pytest`.

To verify the installation:

```bash
uv run pytest -q
```

## Dashboard

After generating the race files, launch the multi-page dashboard with:

```bash
uv run streamlit run app.py
```

The dashboard keeps a responsive 4x4 grid on every page. Use the Streamlit
page navigation to view:

- Primary Races: top goals, top points, team points, and team goal differential
- Skater Races: assists, hits, penalty minutes, and plus/minus
- Goalie Races: top scorers, goals against, save percentage, and shots faced
- Query Races: daily player, team, conference, and team-scorer queries

The animation files remain generated outputs and are not committed to Git.

## Typical Workflow

The scripts use the 2025-2026 season and write generated files to `data/`.
Run them from the project root.

### 1. Create player game logs

The broad extraction demo fetches rosters and player game logs for the teams
listed inside the script:

```bash
uv run python scripts/demo_bar_chart_race.py
```

This writes a file similar to:

```text
data/processed/nhl_player_game_logs_20252026.parquet
```

The first run may make many API requests. Requests are cached in
`nhl_cache.sqlite` so later runs can reuse responses.

### 2. Create a points race

```bash
uv run python scripts/demo_top_points_race.py
```

The script prompts for `gif` or `mp4` and writes the selected output as
`data/outputs/top_points.gif` or `data/outputs/top_points.mp4`.

### 3. Create a plus/minus race

```bash
uv run python scripts/demo_top_plus_minus_race.py
```

This uses the same game-log input and format selection, producing
`top_plus_minus_race.gif` or `top_plus_minus_race.mp4`.

### 4. Create the full collection of stat races

```bash
uv run python scripts/demo_all_stat_races.py
```

This prompts once for the output format and creates races for skater hits,
penalty minutes, assists, goals, goalie statistics, team points, and team goal
differential. If the daily box-score Parquet files do not exist, the script
fetches and caches them first.

### 5. Run query-based races

```bash
uv run python scripts/demo_query_bar_chart_races.py \
	--daily-input data/processed/nhl_player_game_logs_20252026.parquet \
	--season-start 2025-10-07 \
	--season-end 2026-04-16 \
	--team COL
```

The query demo prompts for a format and creates several player and team race
outputs.

## Data and Outputs

Generated data belongs under `data/processed/` and `data/outputs/`:

| Output | Purpose |
| --- | --- |
| `nhl_player_game_logs_20252026.parquet` | Player game-by-game statistics |
| `nhl_daily_skater_boxscore_stats_20252026.parquet` | Daily skater box-score statistics |
| `nhl_daily_goalie_boxscore_stats_20252026.parquet` | Daily goalie box-score statistics |
| `nhl_daily_team_boxscore_stats_20252026.parquet` | Daily team statistics |
| `nhl_player_stats.parquet` | Season-level player statistics |
| `nhl_goalie_stats.parquet` | Season-level goalie statistics |
| `nhl_standings_now.parquet` | Current standings snapshot |
| `*.gif` / `*.mp4` | Rendered bar-chart-race animations |

These are reproducible outputs and should normally not be committed to Git.
The API cache, virtual environment, Python bytecode, test cache, Parquet
outputs, and rendered animations should remain local or be stored separately
from source control. The scripts can regenerate them when their inputs and API
responses are available.

## Project Layout

```text
.
├── pyproject.toml                 # Project metadata and dependencies
├── uv.lock                        # Locked dependency versions
├── app.py                          # Streamlit dashboard entry point
├── pages/                          # Additional Streamlit dashboard pages
├── data/
│   ├── processed/                 # Generated Parquet datasets
│   └── outputs/                   # Generated GIF and MP4 animations
├── scripts/                       # Runnable extraction and visualization demos
├── docs/                          # Project design and schema documentation
├── src/
│   └── nhl_pipeline/
│       ├── main.py                # API, transformation, query, and renderer logic
│       └── team_colors.py         # NHL team color mapping
├── tests/
│   └── test_main.py               # Pipeline and ranking tests
└── README.md                      # Setup and workflow guide
```

## Testing

Run the full suite with:

```bash
uv run pytest -q
```

Some tests call the live NHL API. They require network access and may be
affected by API availability or changes in upstream responses. The request
cache can reduce repeated calls, but it does not make live-endpoint tests fully
offline or deterministic.

For a quick syntax check across the source and demos:

```bash
uv run python -m compileall -q src scripts
```

## Git Workflow

This repository currently has no commits, so the next Git action should be a
careful baseline rather than staging every file indiscriminately.

Before the first commit:

1. Ensure `.gitignore` excludes the API cache, test cache, generated data, and
   rendered animations.
2. Review the staged file list with `git status`.
3. Commit source code, tests, documentation, `pyproject.toml`, and `uv.lock`.
4. Run `uv run pytest -q` before committing.

Once the baseline exists, use small commits that each represent one coherent
change. Examples:

```text
feat: add daily team goal differential race
test: cover game-day ranking behavior
fix: select animation writer from output extension
docs: describe generated data and setup
```

Use `main` as the stable branch. For a larger feature, create a short-lived
branch such as `feature/streamlit-dashboard` or `fix/mp4-output`, test it,
commit it, and merge it back into `main`. We can inspect `git status`, review a
diff, and choose the next commit together as the project grows.

## Roadmap

The documented future direction includes:

- Higher-granularity game-event and momentum data.
- More analytical schemas and DuckDB queries.
- An interactive Streamlit dashboard with metric selection and animation
	controls.
- Potential deployment through Streamlit Community Cloud.

See [future-phases.md](docs/future-phases.md) for the current roadmap notes.
