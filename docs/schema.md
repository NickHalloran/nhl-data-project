### Database Schema Specifications

```markdown
# Database Schema Specifications

The project maintains an analytical layout split across core Parquet files acting as relational tables via DuckDB.

---

## 1. Skaters Table (`nhl_skaters.parquet`)
Stores season-level skater metrics by team.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `player_id` | `INT32` | `INTEGER` | Unique NHL player identifier |
| `first_name` | `STRING` | `VARCHAR` | Player first name |
| `last_name` | `STRING` | `VARCHAR` | Player last name |
| `team_abbr` | `STRING` | `VARCHAR` | 3-letter team abbreviation (e.g., `CAR`) |
| `season` | `STRING` | `VARCHAR` | Season string (e.g., `20252026`) |
| `games_played` | `INT16` | `SMALLINT` | Total games played |
| `goals` | `INT16` | `SMALLINT` | Total goals scored |
| `assists` | `INT16` | `SMALLINT` | Total assists recorded |
| `points` | `INT16` | `SMALLINT` | Combined goals and assists |
| `plus_minus` | `INT16` | `SMALLINT` | On-ice goal differential |
| `penalty_minutes` | `INT16` | `SMALLINT` | Total penalty minutes |
| `shots` | `INT16` | `SMALLINT` | Total shots on goal |
| `shooting_percentage` | `FLOAT32` | `REAL` | Shot conversion rate |
| `time_on_ice_per_game` | `FLOAT32` | `REAL` | Average ice time per game |
| `team_abbr` | `STRING` | `VARCHAR` | Team identifier for later joins |
| `season` | `STRING` | `VARCHAR` | Team-season partition key |

---

## 2. Goalies Table (`nhl_goalies.parquet`)
Tracks season-level goalie production and efficiency.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `player_id` | `INT32` | `INTEGER` | Unique NHL player identifier |
| `first_name` | `STRING` | `VARCHAR` | Goalie first name |
| `last_name` | `STRING` | `VARCHAR` | Goalie last name |
| `team_abbr` | `STRING` | `VARCHAR` | 3-letter team abbreviation |
| `season` | `STRING` | `VARCHAR` | Season string |
| `games_played` | `INT16` | `SMALLINT` | Games dressed/played |
| `wins` | `INT16` | `SMALLINT` | Total wins |
| `losses` | `INT16` | `SMALLINT` | Total losses |
| `ot_losses` | `INT16` | `SMALLINT` | Overtime/shootout losses |
| `shots_against` | `INT16` | `SMALLINT` | Total shots faced |
| `goals_against` | `INT16` | `SMALLINT` | Goals allowed |
| `saves` | `INT16` | `SMALLINT` | Saves made |
| `save_percentage` | `FLOAT32` | `REAL` | Save percentage |
| `goals_against_average` | `FLOAT32` | `REAL` | Goals allowed per game |

---

## 3. Macro Team Table (`nhl_team_macro.parquet`)
Captures team-level season summary, standings, and performance metrics.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `team_abbr` | `STRING` | `VARCHAR` | 3-letter team abbreviation |
| `season` | `STRING` | `VARCHAR` | Season string |
| `games_played` | `INT16` | `SMALLINT` | Total games played |
| `wins` | `INT16` | `SMALLINT` | Wins |
| `losses` | `INT16` | `SMALLINT` | Losses |
| `ot_losses` | `INT16` | `SMALLINT` | Overtime/shootout losses |
| `points` | `INT16` | `SMALLINT` | League points |
| `goals_for` | `INT16` | `SMALLINT` | Goals scored |
| `goals_against` | `INT16` | `SMALLINT` | Goals allowed |
| `goal_differential` | `INT16` | `SMALLINT` | Goals for minus goals against |
| `power_play_percentage` | `FLOAT32` | `REAL` | Power play efficiency |
| `penalty_kill_percentage` | `FLOAT32` | `REAL` | Penalty kill efficiency |
| `rank_division` | `INT16` | `SMALLINT` | Division ranking |
| `rank_conference` | `INT16` | `SMALLINT` | Conference ranking |

---

## 4. Skater Game Logs (`nhl_skaters_game_logs.parquet`)
Stores one row per game per skater, allowing trend analysis over the season.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `game_pk` | `INT32` | `INTEGER` | Unique game identifier |
| `game_date` | `DATE` | `DATE` | Date of the game |
| `team_abbr` | `STRING` | `VARCHAR` | Player's team abbreviation |
| `opponent_abbr` | `STRING` | `VARCHAR` | Opposing team abbreviation |
| `home_away` | `STRING` | `VARCHAR` | `home` or `away` |
| `player_id` | `INT32` | `INTEGER` | Player identifier |
| `first_name` | `STRING` | `VARCHAR` | Player first name |
| `last_name` | `STRING` | `VARCHAR` | Player last name |
| `season` | `STRING` | `VARCHAR` | Season string |
| `goals` | `INT16` | `SMALLINT` | Goals in the game |
| `assists` | `INT16` | `SMALLINT` | Assists in the game |
| `points` | `INT16` | `SMALLINT` | Total points in the game |
| `shots` | `INT16` | `SMALLINT` | Shots on goal |
| `penalty_minutes` | `INT16` | `SMALLINT` | Penalty minutes |
| `time_on_ice` | `FLOAT32` | `REAL` | Minutes on ice |
| `plus_minus` | `INT16` | `SMALLINT` | Game plus/minus |

---

## 5. Goalie Game Logs (`nhl_goalies_game_logs.parquet`)
Stores per-game goalie stats, suitable for matchup analysis.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `game_pk` | `INT32` | `INTEGER` | Unique game identifier |
| `game_date` | `DATE` | `DATE` | Date of the game |
| `team_abbr` | `STRING` | `VARCHAR` | Goalie's team abbreviation |
| `opponent_abbr` | `STRING` | `VARCHAR` | Opponent abbreviation |
| `home_away` | `STRING` | `VARCHAR` | `home` or `away` |
| `player_id` | `INT32` | `INTEGER` | Goalie identifier |
| `first_name` | `STRING` | `VARCHAR` | Goalie first name |
| `last_name` | `STRING` | `VARCHAR` | Goalie last name |
| `season` | `STRING` | `VARCHAR` | Season string |
| `decision` | `STRING` | `VARCHAR` | `W`, `L`, or `OT` |
| `shots_against` | `INT16` | `SMALLINT` | Shots faced |
| `goals_against` | `INT16` | `SMALLINT` | Goals allowed |
| `saves` | `INT16` | `SMALLINT` | Saves made |
| `save_percentage` | `FLOAT32` | `REAL` | Save percentage |
| `time_on_ice` | `FLOAT32` | `REAL` | Minutes played |

---

## 6. Team Game Logs (`nhl_team_game_logs.parquet`)
Captures one row per team game, useful for win/loss and possession trend analysis.

| Column Name | PyArrow Type | SQL Type Equivalent | Description |
| :--- | :--- | :--- | :--- |
| `game_pk` | `INT32` | `INTEGER` | Unique game identifier |
| `game_date` | `DATE` | `DATE` | Game date |
| `team_abbr` | `STRING` | `VARCHAR` | Team abbreviation |
| `opponent_abbr` | `STRING` | `VARCHAR` | Opponent abbreviation |
| `home_away` | `STRING` | `VARCHAR` | `home` or `away` |
| `season` | `STRING` | `VARCHAR` | Season string |
| `goals_for` | `INT16` | `SMALLINT` | Goals scored by team |
| `goals_against` | `INT16` | `SMALLINT` | Goals allowed |
| `result` | `STRING` | `VARCHAR` | `W`, `L`, or `OT` |
| `power_play_goals` | `INT16` | `SMALLINT` | Power play goals |
| `power_play_opportunities` | `INT16` | `SMALLINT` | Power play chances |
| `penalty_minutes` | `INT16` | `SMALLINT` | Team penalty minutes |
| `shots_for` | `INT16` | `SMALLINT` | Shots for |
| `shots_against` | `INT16` | `SMALLINT` | Shots against |
| `faceoff_win_percentage` | `FLOAT32` | `REAL` | Faceoff win rate |
