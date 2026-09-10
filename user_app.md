# NHL Data Project User App Specification

## 1. Document Purpose

This document defines the product, architecture, implementation plan, and acceptance criteria for turning the NHL Data Project into an interactive application that users can download and run in a web browser.

The work is divided into two deliberate phases:

- **Phase 1:** A local Python web application built with Streamlit. It runs locally and opens in the user's browser while reusing the existing Python, Pandas, DuckDB, Parquet, and NHL API code.
- **Phase 2:** A browser-only application that runs without Python or a local Python server. This phase refactors the data and visualization layers for frontend execution, likely using React, DuckDB-WASM, and a browser-compatible charting library.

Phase 1 is the initial product target. Phase 2 is a later portability and distribution refactor, not a requirement for the first usable release.

## 2. Product Vision

The application will provide an approachable NHL analytics workspace where a user can:

- Inspect current and historical NHL team standings.
- Compare team performance.
- Explore player and goalie leaderboards.
- Filter rankings by season, team, conference, division, position, and statistic.
- View animated bar chart races for player and team statistics.
- See team identity consistently represented through stable team colors.
- Refresh data from the official NHL API when current data is needed.
- Use a bundled data snapshot when the API is unavailable or when an immediate offline start is preferred.

The application should feel like an analytical tool rather than a collection of disconnected demo scripts. Existing extraction and query functions should become reusable services beneath the user interface.

## 3. Goals

### 3.1 Primary Goals

1. Provide a single command that starts a browser-based NHL analytics application locally.
2. Reuse the current extraction, transformation, storage, and query logic wherever practical.
3. Make the application functional with bundled data before any network refresh is attempted.
4. Support interactive standings, player, goalie, team, and race views.
5. Preserve team colors across all players, teams, goal bars, and other chart entities.
6. Make failures understandable when data is missing, stale, malformed, or unavailable.
7. Add focused tests around data loading, query behavior, filters, and visualization preparation.
8. Keep the Phase 1 data contracts clear enough to support the Phase 2 frontend refactor.

### 3.2 Secondary Goals

- Add a lightweight refresh workflow for current NHL data.
- Make it possible to select a season without rewriting query logic.
- Provide reproducible sample data for development and demonstrations.
- Keep generated visualizations deterministic enough for automated testing.
- Document setup for technical users and eventual nontechnical packaging options.

### 3.3 Non-Goals for Phase 1

- Building a public multi-user hosted service.
- Implementing authentication or user accounts.
- Supporting arbitrary user-uploaded datasets.
- Replacing DuckDB with a server database.
- Rewriting all query logic in frontend JavaScript.
- Guaranteeing live game updates every second.
- Providing a native desktop application installer.
- Supporting every possible NHL API endpoint.

## 4. Users and Use Cases

### 4.1 Primary User

A technically comfortable NHL fan, analyst, student, or developer who downloads the repository and wants to explore NHL statistics locally.

### 4.2 Secondary User

A developer who wants to extend the project with new metrics, seasons, queries, or visualizations without learning the internals of every demo script.

### 4.3 Core User Journeys

#### Journey A: First Launch

1. User downloads or clones the project.
2. User installs the project environment with `uv sync`.
3. User starts the application with the documented command.
4. The application opens in the browser.
5. The overview page loads bundled data without requiring the NHL API.
6. The interface shows the data source, season, and last-updated timestamp.

#### Journey B: Explore Team Standings

1. User opens the standings view.
2. User selects a season.
3. User optionally filters by conference or division.
4. The table displays rank, team, points, wins, losses, overtime losses, and goal differential.
5. Team names and visual accents use the shared team color mapping.
6. User can select a team to open team-specific details.

#### Journey C: Explore Player Leaders

1. User opens the player leaders view.
2. User selects a metric such as goals, assists, points, plus/minus, hits, or penalty minutes.
3. User selects a top-N limit.
4. User optionally filters by team or position.
5. The application displays a ranked table and a visual chart.
6. Every player is associated with the color of their team.

#### Journey D: Watch a Bar Chart Race

1. User opens the race view.
2. User selects a statistic and entity type.
3. User selects a season and top-N value.
4. User starts, pauses, restarts, or changes the animation speed.
5. Player bars use the player's team color.
6. Team bars use the team's color.
7. The view explains when data is unavailable for a selected combination.

#### Journey E: Refresh Data

1. User opens the data controls.
2. User selects the target season or current season.
3. User starts a refresh.
4. The application displays progress and any endpoint failures.
5. Successfully fetched data is normalized, validated, and persisted.
6. The application reloads the affected views.
7. The application preserves the previous snapshot if refresh fails.

## 5. Phase 1: Local Streamlit Application

### 5.1 Phase 1 Definition

Phase 1 is a local web application served by Streamlit. The Python process owns data loading, API calls, DuckDB queries, transformations, and chart preparation. The user's browser is the interface.

The expected launch flow is:

```text
uv sync
uv run streamlit run app.py
browser opens at http://localhost:8501
```

The application must also work when the browser does not open automatically by displaying the local URL in the terminal.

### 5.2 Phase 1 Architecture

```text
Streamlit UI
    |
    v
Application services
    |
    +--> Data catalog and snapshot loader
    +--> NHL API refresh service
    +--> DuckDB query service
    +--> Race data preparation service
    +--> Team identity and color service
    |
    v
Parquet snapshots and cached API responses
```

The UI must not contain raw SQL, direct API normalization logic, or duplicated color dictionaries. UI functions should call service functions with explicit inputs and receive DataFrames or typed result objects.

### 5.3 Proposed Phase 1 Structure

The exact names may follow the repository's established conventions, but the application should converge toward a structure similar to:

```text
app.py
src/
    nhl_pipeline/
        __init__.py
        main.py
        team_colors.py
        config.py
        data_catalog.py
        data_loader.py
        refresh.py
        queries.py
        race_data.py
        validation.py
        ui/
            __init__.py
            layout.py
            overview.py
            standings.py
            player_leaders.py
            goalie_leaders.py
            races.py
            team_detail.py
            data_controls.py
        charts/
            __init__.py
            rankings.py
            races.py
            theme.py
pages/
    1_Standings.py
    2_Player_Leaders.py
    3_Goalie_Leaders.py
    4_Bar_Chart_Races.py
    5_Team_Detail.py
data/
    snapshots/
    metadata/
tests/
    test_data_catalog.py
    test_queries.py
    test_race_data.py
    test_team_colors.py
    test_refresh.py
```

This is a target organization, not a requirement to perform a large restructuring before the first app screen works. Refactoring should be incremental and tested after each step.

### 5.4 Application Entry Point

The application entry point must:

- Configure the Streamlit page.
- Initialize shared application state.
- Load the default data snapshot.
- Render navigation and the default overview screen.
- Display a useful error state rather than raising an opaque traceback for user-facing data problems.
- Avoid running expensive extraction work on every Streamlit rerun.

The entry point should not contain all page implementation code. It should compose reusable page functions and services.

### 5.5 Streamlit Configuration

The initial configuration should define:

- Application title: `NHL Data Explorer` or an equivalent final name.
- A meaningful page icon.
- Wide layout for tables and races.
- A sidebar for navigation and global data controls.
- A consistent chart and table theme.
- Optional development-only debug information controlled by configuration.

The UI should clearly identify:

- Selected season.
- Data source: bundled snapshot, local refreshed snapshot, or live request.
- Last successful refresh time.
- Whether the displayed dataset is stale.

## 6. Phase 1 Data Architecture

### 6.1 Data Source Strategy

Phase 1 will use a hybrid data strategy:

1. **Bundled snapshot:** The application launches successfully without network access.
2. **Local refreshed snapshot:** A successful refresh writes new data locally.
3. **Cached API responses:** Existing request caching reduces unnecessary API calls.
4. **Fallback behavior:** Failed refreshes leave the last known-good snapshot intact.

The application must never replace a valid snapshot with an empty or partially invalid result without explicitly marking that operation as failed.

### 6.2 Dataset Categories

The initial catalog should support these dataset categories:

- Team standings.
- Season-level skater statistics.
- Season-level goalie statistics.
- Game-by-game player logs.
- Daily cumulative player statistics used by races.
- Daily cumulative team statistics used by races.
- Data metadata and refresh status.

### 6.3 Dataset Metadata

Every managed snapshot should have associated metadata containing at least:

- Dataset name.
- Season identifier.
- Entity type.
- File path.
- Row count.
- Column names.
- Created timestamp.
- Source endpoint or source description.
- Data coverage start and end dates where applicable.
- Last successful refresh timestamp.
- Validation status.
- Application schema version.

Metadata may be stored as JSON, Parquet metadata, or a small DuckDB metadata table. The implementation should choose one consistent mechanism rather than scattering metadata across filenames and UI code.

### 6.4 File Naming

Snapshot filenames should make the entity and season obvious. A target pattern is:

```text
<data-set-name>_<season-id>.parquet
```

Examples:

```text
standings_20252026.parquet
player_stats_20252026.parquet
goalie_stats_20252026.parquet
player_daily_20252026.parquet
team_daily_20252026.parquet
```

The application should not depend on a single hard-coded season filename.

### 6.5 Data Loading Contract

A data loader should accept explicit parameters such as:

```text
load_dataset(dataset_name, season_id, source_policy)
```

Where `source_policy` can distinguish:

- `bundled_only`
- `local_only`
- `local_then_bundled`
- `refresh_if_stale`
- `force_refresh`

The loader should return either:

- A validated DataFrame plus metadata, or
- A structured error that the UI can display.

The loader must not silently return a DataFrame with missing required columns.

### 6.6 Validation Rules

Before a dataset becomes available to the application, validation should check:

- Required columns exist.
- Required identifiers are not unexpectedly null.
- Team abbreviations are recognized or explicitly reported as unknown.
- Numeric metrics have compatible types.
- Dates can be parsed.
- Duplicate keys are either valid by design or rejected.
- Values fall within reasonable domain bounds where practical.
- The resulting DataFrame is not unexpectedly empty.

Validation should distinguish warnings from fatal errors. For example, an unknown future team abbreviation might be a warning, while a missing `team_abbrev` column is fatal for team-colored charts.

## 7. Phase 1 Service Boundaries

### 7.1 Data Catalog Service

Responsibilities:

- Discover available snapshots.
- Resolve dataset names and seasons to files.
- Read metadata.
- Report freshness and availability.
- Select the best source according to a source policy.

Non-responsibilities:

- Rendering UI controls.
- Executing arbitrary SQL supplied by a user.
- Mutating files without going through the refresh service.

### 7.2 Query Service

Responsibilities:

- Own DuckDB connections and query statements.
- Accept validated DataFrames or dataset references.
- Return stable, documented result columns.
- Apply filters and ranking rules.
- Add derived presentation fields such as `team_color` at the result boundary where appropriate.

Required initial query capabilities:

- Top teams by points.
- Top teams by goal differential.
- Conference leaders.
- Player leaders by selected metric.
- Goalie leaders by selected metric.
- Team-specific top scorers.
- Daily cumulative player rankings.
- Daily cumulative team rankings.

The query layer must not assume that the UI is Streamlit. Its results should be usable by scripts, tests, and the future Phase 2 frontend adapter.

### 7.3 Team Identity Service

Responsibilities:

- Own the abbreviation-to-color dictionary.
- Normalize team abbreviations for lookup.
- Return a documented fallback color for unknown teams.
- Optionally expose team display names, logos, conference, and division later.
- Enrich results with `team_color` without mutating caller-owned DataFrames.

The team color mapping must be used consistently by:

- Standings tables and accents.
- Player rankings.
- Goalie rankings.
- Team rankings.
- Player bar chart races.
- Team bar chart races.
- Goal, assist, point, plus/minus, hit, and penalty-minute races.

### 7.4 Race Data Service

Responsibilities:

- Convert raw game logs or daily totals into cumulative time-series data.
- Apply season and date boundaries.
- Select top-N entities by final or configured ranking policy.
- Preserve `team_abbrev` for every entity.
- Add stable `team_color` values.
- Return data in a renderer-independent format.

The race data service should not own Matplotlib or Streamlit rendering. This separation is required so that Phase 2 can consume the same race data through a frontend chart adapter.

### 7.5 Refresh Service

Responsibilities:

- Call the existing NHL API extraction functions.
- Use the existing cache-backed session behavior.
- Normalize API responses.
- Validate output.
- Write a new snapshot atomically.
- Update metadata only after successful completion.
- Preserve the previous snapshot on failure.
- Report per-dataset success, warning, and failure states.

The refresh service should support a dry-run or validation-only mode for development and testing.

## 8. Phase 1 User Interface

### 8.1 Global Controls

Global controls should be placed in a consistent sidebar or top-level control area:

- Season selector.
- Data source selector or source status.
- Refresh button.
- Team selector.
- Conference selector.
- Division selector.
- Data freshness indicator.
- Optional top-N control when relevant.

Controls should be disabled or narrowed when the selected dataset does not support them.

### 8.2 Overview Page

The overview page should provide a useful first screen without requiring navigation.

Required content:

- Current selected season.
- Snapshot status.
- Top teams by points.
- Top teams by goal differential.
- Leading skaters.
- Leading goalies.
- Links or navigation hints to detailed pages.

The overview should avoid loading every expensive race dataset immediately. It should prioritize fast summary queries.

### 8.3 Standings Page

Required table columns:

- Rank.
- Team.
- Abbreviation.
- Games played.
- Wins.
- Losses.
- Overtime losses.
- Points.
- Goal differential.
- Goals for.
- Goals against.
- Points percentage.

Required filters:

- Season.
- Conference.
- Division.
- Optional team.

Required behaviors:

- Sortable columns.
- Clear empty state.
- Team color indicator.
- Exportable filtered table if Streamlit support makes this straightforward.

### 8.4 Player Leaders Page

Initial supported metrics:

- Goals.
- Assists.
- Points.
- Plus/minus.
- Shots.
- Hits.
- Penalty minutes.

Required controls:

- Season.
- Metric.
- Top-N limit.
- Team.
- Position where available.
- Table or chart mode.

Each result must include:

- Player name.
- Team abbreviation.
- Team color.
- Selected metric.
- Supporting metrics where useful.

### 8.5 Goalie Leaders Page

Initial supported metrics:

- Save percentage.
- Wins.
- Saves.
- Goals against.
- Shots against.
- Goals-against average.

Required controls:

- Season.
- Metric.
- Top-N limit.
- Team.
- Minimum games played or minimum shots faced where meaningful.

The UI should avoid ranking goalies with statistically meaningless denominators without making the filtering policy visible.

### 8.6 Team Detail Page

The team detail page should display:

- Team identity and stable team color.
- Current or selected-season standing.
- Team record.
- Goal differential.
- Top skaters.
- Goalie summary.
- Team daily point or goal trend.
- Team-specific player race.

The page should be reachable from standings and ranking results where Streamlit supports convenient selection behavior.

### 8.7 Bar Chart Race Page

Required controls:

- Entity type: players or teams.
- Metric.
- Season.
- Team filter where applicable.
- Top-N count.
- Date range.
- Playback speed.
- Start, pause, restart, and replay controls if supported by the chosen renderer.

Required visual behavior:

- Bars are ordered by current value.
- Labels remain readable.
- Colors come from team identity, never from bar position.
- Unknown teams use the documented fallback color.
- The current date is visible.
- Values are visible on or next to bars.
- Empty and insufficient-data states are clear.

Phase 1 may use a generated animation artifact if fully interactive Streamlit animation is too fragile. The data preparation API must still be renderer-independent.

### 8.8 Approved Interactive Race Controls

The race page will use a parameter-driven configuration rather than separate hardcoded controls for each statistic. The selected parameters must be validated together before the query runs.

#### Entity Type

The user may select:

- Players.
- Teams.
- Goalies.

The entity selection determines the available statistic list and which filters are meaningful. Changing entity type resets incompatible controls to valid defaults.

#### Statistic

Initial player statistics:

- Goals.
- Assists.
- Points.
- Plus/minus.
- Hits.
- Penalty minutes.
- Shots.

Initial team statistics:

- Points.
- Goals for.
- Goals against.
- Goal differential.
- Wins.
- Losses.
- Overtime losses.

Initial goalie statistics:

- Save percentage.
- Wins.
- Saves.
- Goals against.
- Shots faced.
- Goals-against average.

Metric calculation types must be explicit. Additive statistics use cumulative sums. Rate statistics use their documented numerator and denominator. For example, save percentage is cumulative saves divided by cumulative shots faced.

#### Season and Date Range

The user may select a season and then choose one of these date modes:

- Full available season.
- First month.
- Last 30 days.
- Last 14 days.
- Playoffs when playoff data is available.
- Custom start and end dates.

Date controls must be constrained to available data for the selected season. The interface must reject an end date before the start date and explain when a selected range contains insufficient data.

#### Scope

The user may select:

- Entire league.
- Eastern Conference.
- Western Conference.
- A division.
- An individual team.

Scope controls should cascade from broad to narrow:

```text
League -> Conference -> Division -> Team
```

Conference and division membership must come from a season-aware team dimension rather than being inferred from the current standings alone.

#### Top-N and Ranking Policy

The user may select the number of bars, initially supporting 5, 10, 20, 32, and 50, subject to the available population. A custom value may be added after the fixed choices are stable.

The initial ranking policy is top-N by final value within the selected date range. This keeps the set of racing entities stable and makes the animation easier to interpret. The current value determines ordering within each frame.

#### Aggregation Mode

The first interactive version will support:

- Cumulative value.
- Daily value.
- Rolling seven-day value.
- Rolling fourteen-day value.

Rolling modes apply only where the selected metric and source data support meaningful daily aggregation. The UI should hide or disable invalid combinations instead of returning misleading output.

#### Minimum Participation Threshold

Goalie and other rate-based races will support a minimum participation filter. Depending on the dataset, this may be expressed as:

- Minimum games played.
- Minimum shots faced.
- Minimum minutes played.

The selected threshold must be visible in the race configuration and included in the result metadata. The default should prevent very small samples from dominating rate statistics.

#### Playback and Frame Controls

The user may select playback speed from 0.5x, 1x, 2x, and 4x, or enter a custom frame delay in milliseconds. The race should provide start, pause, restart, and replay behavior where supported by the chosen renderer.

For generated GIFs and other saved animations, the user may choose one of two timing modes:

- **Frame delay mode:** Set the delay between frames directly. A smaller delay produces a faster race.
- **Target duration mode:** Set the desired total animation length in seconds. The application derives the frame rate from the number of selected game-day frames.

These modes are mutually exclusive because animation duration is mathematically constrained by:

```text
total duration = number of frames * duration of each frame
```

The UI must make the active timing mode visible and must not silently override one timing value with another. The backend should reject requests that provide both a frame delay and a target total duration. Preview playback and saved GIF output must use the same resolved timing.

Race frame generation will use game days by default. A game day is a date represented by the selected input dataset after filtering. Non-game calendar dates will not produce frames for GIF generation or interactive playback. The underlying race builder will retain calendar-day mode for compatibility and for future use cases that require a continuous calendar axis.

The game-day mode reduces redundant zero-change frames and shortens GIF generation while preserving cumulative values. The selected frame mode should be represented in the race configuration even if the initial UI exposes only game days.

#### Current Ranking Table

The race page should include a current-date ranking table alongside or below the animation. The table should show:

- Rank.
- Entity name.
- Team abbreviation where applicable.
- Team color.
- Current value.
- Change from the previous game day where available.

This provides exact values for users who do not want to interpret an animation.

#### Deferred Controls

The following controls are intentionally deferred:

- CSV downloads.
- Video export controls inside the dashboard.
- Alternate conference or division color modes.
- Arbitrary user-uploaded datasets.

These may be added after the core query configuration, filtering, and race rendering are stable.

### 8.9 Race Configuration Contract

The dashboard should normalize UI selections into one configuration object before calling the query service. Conceptually:

```text
RaceConfig(
    entity_type="player",
    statistic="goals",
    season_id=20252026,
    scope_type="conference",
    conference="Eastern",
    division=None,
    team_abbrev=None,
    start_date="2025-10-07",
    end_date="2026-04-16",
    top_n=20,
    ranking_policy="final_value",
    aggregation_mode="cumulative",
    minimum_participation=None,
    frame_mode="game_day",
    playback_speed=1.0,
    timing_mode="frame_delay",
    frame_duration_ms=200,
    target_duration_seconds=None,
)
```

The query service should receive this normalized configuration rather than individual UI widget values. It should return a renderer-independent result with at least:

```text
date
entity_id
entity_name
team_abbrev
team_color
value
rank
```

The configuration validator must reject unsupported entity/statistic combinations, invalid dates, invalid scopes, unsupported thresholds, and top-N values outside the allowed range.

### 8.10 Race Query Pipeline

Every interactive race should follow this sequence:

```text
UI controls
    |
    v
Validate and normalize RaceConfig
    |
    v
Resolve season and available date range
    |
    v
Apply league, conference, division, and team filters
    |
    v
Aggregate the selected statistic by game day and entity
    |
    v
Calculate cumulative, daily, or rolling values
    |
    v
Apply participation thresholds
    |
    v
Select top-N entities by final value
    |
    v
Rank each game-day frame by current value
    |
    v
Attach team colors and return renderer-ready data
```

Population filtering, metric calculation, ranking, and rendering must remain separate. Adding a new statistic should require a metric definition and query transformation rather than a new chart implementation.

## 9. Visualization and Team Color Requirements

### 9.1 Color Contract

Every visualization-ready result involving a team must preserve:

```text
team_abbrev
team_color
```

`team_color` is derived from `team_abbrev` through the shared team identity service.

### 9.2 Stable Color Rules

- A team always maps to the same primary color within the application.
- A player's color is the color of the player's team for that record.
- A team bar uses the team's own color.
- Color assignment must not depend on ranking order.
- Colors must remain stable when entities enter or leave the top-N set.
- Unknown or missing teams use a neutral fallback color.
- The fallback state should be observable in validation or diagnostics.

### 9.3 Accessibility

Team colors should not be the only way to identify an entity. Charts and tables must also show text labels. Where feasible:

- Check contrast between text and bar backgrounds.
- Use label outlines or contrasting label colors when needed.
- Avoid relying on color alone to communicate status.
- Preserve recognizable differences for teams with similar primary colors.

## 10. Phase 1 Performance and State

### 10.1 Caching

Use Streamlit caching deliberately:

- Cache immutable or versioned snapshot reads.
- Cache expensive query results based on explicit parameters.
- Do not cache mutable refresh state indefinitely.
- Clear relevant caches after a successful refresh.
- Keep API response caching separate from UI result caching.

### 10.2 Session State

Session state may contain:

- Selected season.
- Selected team.
- Selected metric.
- Top-N value.
- Playback settings.
- Current refresh status.

Session state should not be the only persistence mechanism for downloaded datasets or refresh results.

### 10.3 Performance Targets

Initial targets for a typical developer laptop:

- App startup with bundled data: under 5 seconds after dependencies are installed.
- Changing a simple leaderboard filter: under 2 seconds.
- Loading a cached leaderboard query: under 1 second where practical.
- Refresh progress should be visible for operations longer than 1 second.
- A race should not block the rest of the application from rendering.

These are targets for normal-sized NHL season datasets, not hard guarantees for unusually large exports.

## 11. Phase 1 Error Handling

The application must handle:

- Missing data directory.
- Missing snapshot file.
- Corrupt Parquet file.
- Missing required columns.
- NHL API timeout.
- NHL API rate limiting.
- NHL API schema changes.
- Empty API response.
- Unsupported season.
- Unknown team abbreviation.
- Insufficient data for a race.
- Missing optional charting dependency.

User-facing errors should include:

- What operation failed.
- Which dataset or season was involved.
- Whether an older snapshot remains available.
- What action the user can take next.

Tracebacks should be reserved for development mode or logs, not shown as the primary user experience.

## 12. Phase 1 Testing Plan

### 12.1 Unit Tests

Add tests for:

- Dataset path resolution.
- Metadata parsing.
- Source policy selection.
- Required-column validation.
- Team color normalization.
- Unknown team fallback behavior.
- Player ranking queries.
- Goalie ranking queries.
- Standings queries.
- Daily cumulative race preparation.
- Date and season filtering.
- Top-N behavior.
- Atomic snapshot writing behavior.

### 12.2 Integration Tests

Add tests that:

- Load a small fixture Parquet dataset.
- Run the query service against the fixture.
- Confirm all visualization results retain `team_abbrev` and `team_color`.
- Simulate a successful refresh.
- Simulate a failed refresh and verify the old snapshot remains intact.
- Start the app or import the app entry point without network access where practical.

### 12.3 Visualization Tests

Do not rely exclusively on inspecting rendered pixels. Test the preparation layer directly:

- Every player result has a team color.
- Every team result has its own team color.
- A known team always resolves to the same color.
- An entity's color does not change when ranking order changes.
- Unknown teams receive the fallback color.

A small renderer smoke test may verify that the chart function accepts the prepared data and produces an artifact without errors.

### 12.4 Manual Acceptance Tests

A release candidate should be manually checked for:

- Fresh installation.
- Startup with network disabled.
- Startup with an empty data directory.
- Refresh with a working API.
- Refresh with an unavailable API.
- Mobile-width or narrow browser layout where relevant.
- Team color consistency across at least three different race types.
- Long player names and long team labels.

## 13. Phase 1 Packaging and Distribution

### 13.1 Initial Developer Distribution

The repository should document:

```bash
uv sync
uv run streamlit run app.py
```

The documentation should also include:

- Required Python version.
- Supported operating systems.
- How to stop the app.
- How to select another port.
- Where local data and cache files are stored.
- How to refresh data.
- How to troubleshoot missing dependencies.

### 13.2 One-Command Launcher

After the first stable app version, add a project script such as:

```bash
uv run nhl-app
```

This command should start Streamlit with the correct entry point and any required configuration.

### 13.3 Optional Container Distribution

A later Phase 1 extension may provide:

```bash
docker compose up
```

The container option should be documented as optional and should not replace the simpler `uv` workflow for developers.

### 13.4 Packaged Executable Evaluation

A native executable can be evaluated after the app stabilizes. Packaging should be treated as a separate effort because Streamlit, Python dependencies, Matplotlib, DuckDB, and platform-specific binaries may make a single-file distribution large and platform-dependent.

## 14. Phase 1 Milestones

### Milestone 1: Application Skeleton

Deliverables:

- Streamlit dependency.
- Working `app.py`.
- Page configuration.
- Overview placeholder.
- Startup documentation.

Acceptance criteria:

- The app starts with one documented command.
- The browser displays a meaningful page.
- The app can start with bundled or fixture data.

### Milestone 2: Data Catalog and Snapshot Loading

Deliverables:

- Dataset catalog.
- Season-aware path resolution.
- Metadata model.
- Validation layer.
- Bundled snapshot loading.

Acceptance criteria:

- The app identifies available datasets and seasons.
- Missing or invalid snapshots produce understandable messages.
- No network call is required for initial startup.

### Milestone 3: Standings and Leaderboards

Deliverables:

- Standings page.
- Player leaders page.
- Goalie leaders page.
- Shared filters.
- Query service integration.

Acceptance criteria:

- All requested filters work.
- Results are deterministic for fixture data.
- Team colors are present and consistent.

### Milestone 4: Race Experience

Deliverables:

- Renderer-independent race preparation.
- Player races.
- Team races.
- Metric selection.
- Playback controls or generated animation fallback.

Acceptance criteria:

- At least goals, points, and one goalie metric work.
- Colors remain tied to team identity.
- Empty data states are handled.

### Milestone 5: Refresh and Resilience

Deliverables:

- Refresh controls.
- Progress indicators.
- Atomic writes.
- Failure fallback.
- Metadata updates.

Acceptance criteria:

- A successful refresh updates the selected data.
- A failed refresh preserves the last known-good snapshot.
- The UI explains refresh status.

### Milestone 6: Release Documentation

Deliverables:

- Updated README.
- Setup guide.
- Usage guide.
- Troubleshooting guide.
- Test instructions.
- Optional container instructions.

Acceptance criteria:

- A new user can start the app from a clean environment using documented commands.
- The documentation identifies known limitations.

## 15. Phase 2: Browser-Only Refactor

### 15.1 Phase 2 Definition

Phase 2 converts the application from a Python-served local web app into a true browser-only application. The target user should be able to download static assets or visit a static deployment and use the application without installing Python or starting a local Python process.

The preferred architecture is:

```text
Static web application
    |
    +--> React or equivalent frontend
    +--> Browser charting library
    +--> DuckDB-WASM or browser-compatible query layer
    +--> Bundled Parquet or converted compact data assets
    +--> Optional browser fetch to NHL API
```

### 15.2 Phase 2 Goals

- Eliminate the Python runtime requirement for normal use.
- Run data queries inside the browser where practical.
- Preserve the Phase 1 user journeys.
- Preserve team color behavior and result contracts.
- Support static hosting.
- Support offline use with bundled datasets.
- Keep refresh optional and clearly separated from bundled-data use.

### 15.3 Phase 2 Refactoring Principles

1. Do not rewrite the application UI and data contracts simultaneously without fixtures.
2. Treat Phase 1 query outputs as the initial contract for frontend adapters.
3. Move data preparation into portable, testable transformations.
4. Replace Python-specific rendering with browser-native chart components.
5. Keep a reproducible data build step that creates browser-consumable assets.
6. Preserve a Python reference implementation for data validation during migration.

### 15.4 Phase 2 Proposed Structure

```text
web/
    package.json
    src/
        app/
        components/
        pages/
        charts/
        data/
        query/
        state/
        theme/
        teamColors.ts
    public/
        data/
        metadata/
    tests/
        unit/
        browser/
    vite.config.ts
```

The exact frontend framework can be chosen at Phase 2 kickoff, but it should support:

- Static builds.
- TypeScript.
- Component testing.
- Browser automation.
- Efficient table rendering.
- Responsive layout.

### 15.5 Browser Data Options

#### Option B1: DuckDB-WASM with Parquet

The browser loads Parquet assets and executes SQL through DuckDB-WASM.

Advantages:

- Closest conceptual match to the current architecture.
- Reuses SQL thinking and columnar data.
- Good fit for analytical queries.

Risks:

- WASM bundle size.
- Browser memory usage.
- Worker configuration.
- Asset loading and cross-origin requirements.
- Some DuckDB features may differ from the server version.

#### Option B2: Precomputed JSON or Arrow Assets

A build step converts commonly used query results into frontend-oriented assets.

Advantages:

- Simple browser loading.
- Smaller runtime complexity.
- Predictable performance for known views.

Risks:

- Less flexible ad hoc querying.
- More build-time data generation.
- More asset versions to manage.

#### Option B3: Hybrid Browser Querying

Use precomputed assets for common pages and DuckDB-WASM for deeper exploration.

This may become the best long-term option, but it should not be selected until bundle size and query performance are measured.

### 15.6 Phase 2 Data Build Pipeline

The project should add a repeatable build step that:

1. Selects the supported seasons.
2. Reads validated Parquet snapshots.
3. Produces browser-consumable assets.
4. Writes metadata and schema versions.
5. Copies team identity metadata.
6. Generates a manifest containing available datasets and seasons.
7. Fails loudly if required datasets are missing or invalid.

The static application should never assume that a dataset exists merely because a route exists.

### 15.7 Phase 2 Query Adapter Contract

Frontend query adapters should expose operations conceptually equivalent to:

```text
getStandings(filters)
getPlayerLeaders(filters)
getGoalieLeaders(filters)
getTeamDetail(team, filters)
getRaceData(filters)
getDatasetStatus()
```

Each result should contain explicit fields rather than relying on chart-specific positional arrays.

For visualization results, the minimum contract remains:

```text
entity_id
entity_name
team_abbrev
team_color
date
value
rank
```

### 15.8 Phase 2 Visualization Refactor

The browser application should replace Matplotlib animations with an interactive chart implementation that supports:

- Current-value bar ranking.
- Date progression.
- Play and pause.
- Speed adjustment.
- Restart.
- Responsive sizing.
- Accessible labels.
- Stable team colors.
- Export where practical.

The race data transformation should remain conceptually identical to Phase 1. Only the rendering adapter should change initially.

### 15.9 Phase 2 NHL API Strategy

Direct browser requests to the NHL API must be evaluated for:

- CORS behavior.
- Rate limits.
- Browser security policy.
- Endpoint stability.
- User privacy and request volume.
- Need for a proxy or serverless function.

The browser-only app must remain useful without live API access. Bundled snapshots are the fallback and should be the default for offline reliability.

If direct API access is not reliable, Phase 2 should use one of these approaches:

- A build-time data refresh process.
- A small optional API proxy.
- A serverless refresh endpoint.
- User-provided downloaded data.

The app should not make the user experience dependent on undocumented browser access to a third-party API.

### 15.10 Phase 2 Distribution

The target distribution options are:

1. Static hosted website.
2. Downloadable zip containing static assets.
3. Optional desktop wrapper such as Electron or Tauri if a native shell is later valuable.

The initial Phase 2 release should prefer static hosting and downloadable static assets before introducing a desktop wrapper.

### 15.11 Phase 2 Testing

Add:

- TypeScript unit tests for query adapters.
- Fixture-based tests comparing browser results to Python reference results.
- Component tests for filters and empty states.
- Browser tests for navigation and core workflows.
- Responsive viewport tests.
- Visual tests for team colors and race labels.
- Offline tests with network access disabled.
- Performance tests for initial load and race startup.

At least one cross-runtime comparison should verify that a known fixture produces equivalent rankings in Python and the browser.

## 16. Phase 2 Milestones

### Phase 2 Milestone 1: Frontend Shell

- Create static frontend project.
- Reproduce navigation and visual design.
- Load a static fixture.
- Implement team color theme.

### Phase 2 Milestone 2: Data Adapter

- Select DuckDB-WASM, JSON, Arrow, or hybrid strategy.
- Load the manifest.
- Implement standings and leaderboard adapters.
- Compare results with Phase 1 fixtures.

### Phase 2 Milestone 3: Interactive Pages

- Implement standings.
- Implement player leaders.
- Implement goalie leaders.
- Implement team detail.
- Implement shared filters and URL state where useful.

### Phase 2 Milestone 4: Browser Race Renderer

- Implement player and team race views.
- Match Phase 1 race data semantics.
- Verify stable team colors.
- Verify behavior on narrow and wide viewports.

### Phase 2 Milestone 5: Offline and Static Distribution

- Produce a static build.
- Bundle a known-good data snapshot.
- Test from a static server.
- Test downloaded asset distribution.
- Document refresh limitations.

### Phase 2 Milestone 6: Optional Live Refresh

- Measure direct API feasibility.
- Add a proxy or build-time refresh if needed.
- Preserve offline behavior.
- Document data freshness clearly.

## 17. Cross-Phase Compatibility Requirements

The following concepts must remain stable across both phases:

- Season identifiers.
- Team abbreviations.
- Team color mapping.
- Dataset names.
- Metric names.
- Ranking direction.
- Top-N semantics.
- Date semantics for cumulative races.
- Handling of missing and unknown teams.
- Meaning of player and team race values.

Changes to these contracts require a documented schema or application version update.

## 18. Security and Privacy

The application does not need user accounts or personal data for the initial scope.

Still required:

- Do not execute arbitrary SQL supplied through UI text fields.
- Validate file paths before reading local data.
- Avoid logging API credentials if future endpoints require them.
- Keep refresh endpoints constrained to known NHL API routes.
- Avoid silently sending user data anywhere.
- Document all network calls.
- Make external API use visible in the data source status.

## 19. Observability and Diagnostics

The application should log enough information to diagnose failures without overwhelming users:

- Dataset load attempts.
- Refresh start and completion.
- Row counts.
- Validation warnings.
- API endpoint failures.
- Snapshot paths.
- Query duration where useful.

The UI should expose a compact diagnostics section containing:

- Current data source.
- Snapshot timestamp.
- Selected season.
- Available datasets.
- Last refresh result.

Detailed logs may remain in the terminal during Phase 1.

## 20. Open Decisions Before Implementation

These decisions should be confirmed before beginning the first application milestone:

1. Final application name.
2. Whether the default view is overview or standings.
3. Which seasons are bundled initially.
4. Whether bundled data is committed to the repository or downloaded during setup.
5. Whether the app should automatically open the browser.
6. Whether live refresh is available to all users or developer-only initially.
7. Whether race output should be interactive inside Streamlit or generated as downloadable media first.
8. Whether the app should support only English labels initially.
9. Whether a hosted public deployment is planned after Phase 1.
10. Which frontend framework and browser data strategy will be used for Phase 2.

The following interaction decisions are approved for implementation:

- Include minimum participation thresholds.
- Include daily and rolling seven-day and fourteen-day modes.
- Select top-N entities by final value within the chosen range by default.
- Do not add CSV downloads in the first interactive release.
- Generate race frames on game days rather than every calendar day.
- Allow users to control either frame delay or target GIF duration, but not both at once.

## 21. Definition of Done for Phase 1

Phase 1 is complete when:

- A clean environment can install dependencies with `uv sync`.
- A documented command starts the app.
- The app loads bundled data without network access.
- Standings, player leaders, goalie leaders, and at least one race page work.
- Filters produce correct results.
- Team colors are stable and shared across all visualizations.
- Refresh can update data without destroying the previous valid snapshot on failure.
- Tests cover the data catalog, query layer, race preparation, team colors, and refresh behavior.
- The README explains setup, usage, data sources, refresh behavior, and troubleshooting.
- The app reports the selected season and data freshness.

## 22. Definition of Done for Phase 2

Phase 2 is complete when:

- The application builds as static browser assets.
- A user can run it without Python.
- Bundled data works offline.
- Standings, leaderboards, team detail, and races are available.
- Browser results match the Python reference results for representative fixtures.
- Team colors remain stable across all supported visualizations.
- The application is tested in supported desktop and mobile viewport sizes.
- Static deployment and downloadable asset instructions are documented.
- Live refresh, if implemented, is optional and does not break offline behavior.

## 23. Recommended Execution Order

The recommended order is:

1. Confirm Phase 1 decisions in Section 20.
2. Add a minimal Streamlit dependency and entry point.
3. Build the data catalog around existing Parquet outputs.
4. Extract reusable query and race services from demo-oriented code.
5. Build the overview and standings pages.
6. Add player and goalie leaderboards.
7. Add the race page using the existing team color contract.
8. Add refresh and snapshot resilience.
9. Add tests and documentation.
10. Use the stabilized Phase 1 contracts to begin Phase 2.
11. Build a browser fixture and compare it with Python results.
12. Select and implement the browser data strategy.
13. Rebuild the pages and race renderer for static execution.

## 24. Summary

The safest product path is a two-stage application strategy:

- Phase 1 delivers a useful local browser experience quickly by keeping Python, DuckDB, Parquet, and the current extraction pipeline.
- Phase 2 removes the Python runtime requirement by moving the query and visualization experience into a static frontend with browser-compatible data processing.

The most important architectural investment in Phase 1 is not the Streamlit page layout. It is the separation of data loading, validation, queries, race preparation, and team identity from rendering. That separation allows the application to evolve from a local Python dashboard into a true browser application without discarding the project's analytical foundations.
