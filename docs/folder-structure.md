# Folder Structure

This project is arranged to separate documentation, data, extraction logic, and deployment code.

## Repository Layout

```text
nhl-pipeline/
├── .git/
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/
│   ├── overview.md
│   ├── data-extraction.md
│   ├── schema.md
│   ├── future-phases.md
│   └── folder-structure.md
├── scripts/
│   └── demo_*.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
├── src/
│   └── nhl_pipeline/
│       ├── __init__.py
│       └── main.py
└── tests/
	└── test_main.py
```

## Key directories and files

* `data/` - generated raw, processed, and visualization outputs.
* `src/nhl_pipeline/` - extraction, transformation, and serialization code.
* `scripts/` - runnable extraction and visualization demos.
* `docs/` - overview, extraction, schema, roadmap, and layout documentation.
* `tests/` - automated pipeline and ranking tests.

## Data flow summary

1. `src/nhl_pipeline/main.py` ingests NHL API data.
2. Data is transformed in-memory using Pandas.
3. A typed PyArrow schema is applied and persisted as Parquet.
4. DuckDB queries the Parquet files for analysis and dashboard rendering.
