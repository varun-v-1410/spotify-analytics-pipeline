from pathlib import Path

import duckdb
import pandas as pd
import yaml

from src.ingestion.load_raw_data import ingest_csv
from src.transformation.cleaning import clean_listening_data
from src.utils.paths import (
    BRONZE_DIR,
    CONFIGS_DIR,
    DATABASE_DIR,
    GOLD_DIR,
    RAW_DIR,
    SILVER_DIR,
    ensure_directories,
)
from src.warehouse.build_marts import load_warehouse


def read_config(config_path: Path) -> dict:
    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def run_pipeline(config_file: str = "pipeline_config.yaml") -> None:
    ensure_directories()

    config = read_config(CONFIGS_DIR / config_file)
    raw_csv_path = RAW_DIR / config["raw_file_name"]
    db_path = DATABASE_DIR / config["duckdb_name"]

    raw_df = ingest_csv(str(raw_csv_path))
    raw_df.to_parquet(BRONZE_DIR / "listening_history_bronze.parquet", index=False)

    silver_df = clean_listening_data(raw_df)
    silver_df.to_parquet(SILVER_DIR / "listening_history_silver.parquet", index=False)

    load_warehouse(silver_df, db_path)

    conn = duckdb.connect(str(db_path))
    top_tracks = conn.execute("select * from mart_top_tracks limit 1000").df()
    monthly = conn.execute("select * from mart_monthly_streams").df()
    genre = conn.execute("select * from mart_genre_performance").df()
    conn.close()

    top_tracks.to_parquet(GOLD_DIR / "top_tracks_gold.parquet", index=False)
    monthly.to_parquet(GOLD_DIR / "monthly_streams_gold.parquet", index=False)
    genre.to_parquet(GOLD_DIR / "genre_performance_gold.parquet", index=False)

    print("Pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()
