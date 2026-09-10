# Data Extraction & Transformation Architecture

## Tech Stack
* **Python 3.10+**: Core programming language for pipeline logic.
* **uv**: Modern, high-performance package manager and environment virtualizer.
* **Requests-Cache**: Local HTTP caching mechanism to persist network responses and prevent redundant external API calls during local iteration.
* **Pandas**: In-memory data manipulation framework used for JSON flattening and structural reshaping.
* **Apache PyArrow**: Columnar memory framework utilized for strict schema enforcement and zero-copy serialization.

---

## Pipeline Architecture & Step-by-Step Breakdown

The data pipeline transitions raw, unstructured web payloads into a rigid, queryable analytical format through five sequential stages:

### Step 1: Controlled Network Ingestion & Caching
* **Mechanism:** The pipeline targets official league endpoints (`api-web.nhle.com`) via a managed HTTP session.
* **Engineering Rationale:** Integrating `requests-cache` establishes a local fallback cache (with a 24-hour expiration). This protects external API resources, drastically accelerates local script testing loops, and ensures development continuity even when offline.

### Step 2: Raw Payload Deserialization
* **Mechanism:** The incoming HTTP JSON payload is parsed into native Python dictionaries and lists.
* **Engineering Rationale:** Sports APIs frequently return deeply nested structures (e.g., localized player name dictionaries or multi-level status mappings) that cannot be directly queried as flat tabular rows.

### Step 3: Tabular Flattening & Semantic Mapping
* **Mechanism:**
  - Nested dictionary fields (such as `firstName` and `lastName`) are safely evaluated and extracted using programmatic safety checks (`isinstance` checks and default fallback handlers).
  - API field names utilizing camelCase nomenclature (e.g., `gamesPlayed`, `plusMinus`, `shootingPctg`) are mapped to standardized analytical snake_case column names (`games_played`, `plus_minus`, `shooting_percentage`).
* **Engineering Rationale:** Establishing standard naming conventions ensures downstream compatibility with SQL query engines and analytical libraries.

### Step 4: Strict Schema Enforcement (PyArrow Protection)
* **Mechanism:** Before data serialization, an explicit PyArrow schema (`pa.schema`) defines every column's exact data type (e.g., `INT32` for IDs, `INT16` for counts, `FLOAT32` for percentages). Missing columns are padded with default values, and data frames are filtered and aligned strictly to this schema blueprint.
* **Engineering Rationale:** Enforcing a contract at the ingestion boundary prevents "data drift" (where API changes quietly corrupt downstream datasets) and guarantees predictable memory layouts.

### Step 5: Columnar Serialization (The Local Lakehouse)
* **Mechanism:** The validated table is written to disk under the local `data/` directory as an Apache Parquet file using snappy compression.
* **Engineering Rationale:** Parquet stores data column-by-column rather than row-by-row. This drastically reduces file size, optimizes disk I/O, and allows query engines like DuckDB to scan only the specific columns needed for a visualization or query rather than reading the entire file.

### Step 6: Analytical Query Engine — DuckDB
* **Mechanism:** DuckDB reads the generated Parquet files directly from disk and executes SQL queries in-process, without requiring a separate database server.
* **Engineering Rationale:** Using DuckDB keeps the analytics stack lightweight and self-contained. It enables fast ad hoc queries over large analytic tables, supports complex SQL operations, and integrates smoothly with both Python and the planned visualization layer.
* **Benefits:**
  * Instant schema discovery from Parquet metadata
  * Efficient vectorized execution on columnar data
  * Simpler local development and deployability for serverless dashboards
  * Compatibility with Pandas and PyArrow for easy data interchange

## Game-by-Game Extraction
In addition to season-level team stats, we will pull per-game logs so the result set can support temporal analytics and performance trends.

### Recommended endpoints
* **Team season stats:** `https://api-web.nhle.com/v1/club-stats/{teamAbbr}/{season}`
* **Team schedule:** `https://api-web.nhle.com/v1/schedule?teamId={teamId}&season={season}` or the team schedule endpoint if available
* **Game box score / live feed:** `https://api-web.nhle.com/v1/game/{gamePk}/feed/live`

### Target Parquet outputs
* `nhl_skaters_{team}_{season}.parquet` — season-level skater stats
* `nhl_goalies_{team}_{season}.parquet` — season-level goalie stats
* `nhl_team_macro_{team}_{season}.parquet` — season-level team summary
* `nhl_skaters_game_logs_{team}_{season}.parquet` — per-game skater performances
* `nhl_goalies_game_logs_{team}_{season}.parquet` — per-game goalie performances
* `nhl_team_game_logs_{team}_{season}.parquet` — per-game team results and box scores

### Game log extraction flow
1. Fetch the team schedule for the season.
2. For each game, request the live or boxscore feed.
3. Flatten the game payload into separate skater, goalie, and team DataFrames.
4. Append or build the game log tables and persist as Parquet.

### Why game logs matter
* Enables trend analysis across the season
* Supports animated timelines and bar chart races
* Allows comparisons of day-to-day player performance
* Keeps the dataset stateless: each Parquet file contains the full extracted history for one team-season

## Example Data Flow: API → Pandas → PyArrow Parquet → DuckDB
1. **API ingestion:** Fetch JSON data from the NHL endpoint using a cached HTTP session.
2. **Pandas transformation:** Load the JSON payload into a `pandas.DataFrame`, flatten nested fields, standardize column names, and apply clean data transformations.
3. **PyArrow serialization:** Convert the DataFrame into a typed `pyarrow.Table` using an explicit schema, then write it to Parquet for efficient long-term storage.
4. **DuckDB analysis:** Open a DuckDB connection, query the Parquet files directly, and return results for analytics or dashboard rendering.

### Example Python Flow
```python
import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests_cache

# 1. Fetch JSON from NHL API
session = requests_cache.CachedSession('nhl_cache', expire_after=86400)
response = session.get('https://api-web.nhle.com/v1/club-stats/CAR/20252026')
raw_json = response.json()

# 2. Normalize into a DataFrame
skaters = raw_json.get('skaters', [])
df = pd.DataFrame(skaters)
df['first_name'] = df['firstName'].apply(lambda x: x.get('default', '') if isinstance(x, dict) else '')
df['last_name'] = df['lastName'].apply(lambda x: x.get('default', '') if isinstance(x, dict) else '')

df = df.rename(columns={
    'gamesPlayed': 'games_played',
    'plusMinus': 'plus_minus',
    'penaltyMinutes': 'penalty_minutes',
    'shootingPctg': 'shooting_percentage',
    'timeOnIcePerGame': 'time_on_ice_per_game'
})

# 3. Persist with PyArrow / Parquet
schema = pa.schema([
    ('player_id', pa.int32()),
    ('first_name', pa.string()),
    ('last_name', pa.string()),
    ('team_abbr', pa.string()),
    ('season', pa.string()),
    ('games_played', pa.int16()),
    ('goals', pa.int16()),
    ('assists', pa.int16()),
    ('points', pa.int16()),
    ('plus_minus', pa.int16()),
    ('penalty_minutes', pa.int16()),
    ('shots', pa.int16()),
    ('shooting_percentage', pa.float32()),
    ('time_on_ice_per_game', pa.float32())
])
table = pa.Table.from_pandas(df[schema.names].fillna(0), schema=schema)
pq.write_table(table, 'data/nhl_skaters_CAR_20252026.parquet')

# 4. Analyze with DuckDB from Parquet
con = duckdb.connect()
results = con.execute("""
    SELECT team_abbr, first_name, last_name, points, goals, assists
    FROM 'data/nhl_skaters_CAR_20252026.parquet'
    WHERE games_played > 10
    ORDER BY points DESC
    LIMIT 20
""").df()
print(results)
```

### Why this flow works well
* **API to pandas:** captures raw payloads and makes nested JSON queryable in memory.
* **Pandas to Parquet:** preserves a typed, compressed dataset that can be queried repeatedly without re-fetching the API.
* **Parquet to DuckDB:** supports fast analytics and SQL-based exploration without spinning up a separate database layer.






# Data Extraction & Transformation Pipeline

## Tech Stack

* **Python 3.10+**
* **uv** (Fast package manager & environment tool)
* **Pandas** (Data wrangling & JSON flattening)
* **PyArrow** (Columnar serialization & strict schema enforcement)
* **Requests-Cache** (Network call caching)

---




## Pipeline Script (`src/nhl_pipeline/main.py`)

```python
import os
import requests_cache
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Setup Cached Session (24-hour cache lifespan)
session = requests_cache.CachedSession('nhl_cache', expire_after=86400)

# Define Strict PyArrow Schemas
skater_schema = pa.schema([
    ('player_id', pa.int32()),
    ('first_name', pa.string()),
    ('last_name', pa.string()),
    ('team_abbr', pa.string()),
    ('season', pa.string()),
    ('games_played', pa.int16()),
    ('goals', pa.int16()),
    ('assists', pa.int16()),
    ('points', pa.int16()),
    ('plus_minus', pa.int16()),
    ('penalty_minutes', pa.int16()),
    ('shots', pa.int16()),
    ('shooting_percentage', pa.float32()),
    ('time_on_ice_per_game', pa.float32())
])

def process_club_stats(team_abbr: str, season: str) -> pd.DataFrame:
    url = f"[https://api-web.nhle.com/v1/club-stats/](https://api-web.nhle.com/v1/club-stats/){team_abbr}/{season}"
    response = session.get(url)
    data = response.json()

    skaters = data.get("skaters", [])
    if not skaters:
        return pd.DataFrame()

    df = pd.DataFrame(skaters)

    # Flatten nested dictionaries safely using anonymous mapping
    df['first_name'] = df['firstName'].apply(lambda x: x.get('default', '') if isinstance(x, dict) else '')
    df['last_name'] = df['lastName'].apply(lambda x: x.get('default', '') if isinstance(x, dict) else '')
    df['player_id'] = df['playerId']
    df['team_abbr'] = team_abbr
    df['season'] = season

    # Map API camelCase keys to analytical snake_case column names
    df = df.rename(columns={
        'gamesPlayed': 'games_played',
        'plusMinus': 'plus_minus',
        'penaltyMinutes': 'penalty_minutes',
        'shots': 'shots',
        'shootingPctg': 'shooting_percentage',
        'timeOnIcePerGame': 'time_on_ice_per_game'
    })

    # Align columns to strict schema expectation
    expected = [field.name for field in skater_schema]
    for col in expected:
        if col not in df.columns:
            df[col] = 0

    return df[expected].fillna(0)

if __name__ == "__main__":
    team, season = "CAR", "20252026"
    df_skaters = process_club_stats(team, season)

    if not df_skaters.empty:
        table = pa.Table.from_pandas(df_skaters, schema=skater_schema)
        os.makedirs("data", exist_ok=True)
        filename = f"data/nhl_skaters_{team}_{season}.parquet"
        pq.write_table(table, filename)
        print(f"Successfully serialized schema-compliant data to {filename}")