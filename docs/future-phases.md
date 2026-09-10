# Future Phases Roadmap

## Phase 2: In-Game Momentum & Advanced Telemetry Integration
* **Objective:** Expand analytical depth by ingesting higher-granularity live event and tracking feeds.
* **Execution Plan:**
  - Introduce an extraction script targeting game-level event endpoints.
  - Define custom PyArrow schemas for temporal game logs.
  - Serialize output into a new parallel Parquet file: `nhl_momentum.parquet`.

---

## Phase 3: Interactive Serverless Web Dashboard & Bar Chart Race Animation (Streamlit)
* **Objective:** Transition from a code-only portfolio project to a live, production-ready web application featuring dynamic visual tracking.
* **Execution Plan:**
  - Build a multi-page interactive web UI using **Streamlit**.
  - **Dynamic Metric Selection:** Enable users to pick what stat controls bar length (`points`, `goals`, `assists`, `shots`).
  - **Bar Chart Race Simulation:** Integrate Plotly Express animations (`animation_frame="game_date"`, `animation_group="player_name"`) to let users cycle day-by-day through the regular season.
  - **Custom Speed Controls:** Provide interactive sliders to regulate frame duration (milliseconds per step) and top-$N$ player cutoff counts.
  - **On-the-Fly SQL Execution:** Route dashboard selections directly into parameterized DuckDB queries reading from repository Parquet files.
  - **Deployment:** Host publicly via Streamlit Community Cloud linked to the GitHub repository.
