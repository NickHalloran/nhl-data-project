# Project Overview: Serverless NHL Analytics Pipeline & Lakehouse

## Purpose
This project builds a reproducible NHL analytics pipeline that transforms official league API data into typed, queryable tables and enables fast SQL-driven exploration with DuckDB. The goal is to deliver a lightweight analytics stack that is easy to maintain, extensible, and ready for interactive visualization.

## Objectives
* Ingest official NHL API data with a cache-backed pipeline.
* Normalize nested JSON into analytics-ready tabular datasets.
* Enforce explicit column types with PyArrow schemas.
* Persist data as Parquet for efficient analytical storage.
* Query datasets with DuckDB without requiring a separate database server.
* Prepare a future Streamlit dashboard for interactive data exploration.

---

## Project Milestones

1. **Data Extraction**
   - Implement API request caching.
   - Collect player, goalie, and team dataset payloads.

2. **Data Transformation**
   - Flatten nested JSON into clean analytical tables.
   - Standardize naming, fill missing values, and enforce shape.
   - Apply explicit PyArrow schemas before serialization.

3. **Parquet Storage**
   - Persist typed datasets into `data/` as Parquet files.
   - Keep files organized by entity and season.

4. **Analytical Querying**
   - Use DuckDB to query Parquet files directly.
   - Support ad hoc analytics without a separate database server.

5. **Dashboard & Visualization**
   - Build an interactive Streamlit application.
   - Add metric filters, ranking controls, and animated visualizations.

---

## Core Architectural Rationale
* **Separation of concerns:** Clear extraction, transformation, storage, and analysis layers.
* **Reproducibility:** Cached API responses and schema enforcement keep results stable and predictable.
* **Performance:** Parquet and DuckDB enable efficient analytics on columnar data.
* **Scalability:** The stack can evolve from local exploration to serverless dashboard deployment.
