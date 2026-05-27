# Spotify Analytics Pipeline

End-to-end batch ETL project that ingests Spotify track analytics from CSV, cleans and transforms data, loads analytical tables in DuckDB, and serves business dashboards with Streamlit.

## Dataset

This pipeline uses the **[Spotify Music Analytics Dataset (2015–2025)](https://www.kaggle.com/datasets/rohiteng/spotify-music-analytics-dataset-20152025)** by [rohiteng](https://www.kaggle.com/rohiteng) on Kaggle.

| Detail | Value |
|--------|--------|
| **Source** | [Kaggle — Spotify Music Analytics Dataset (2015–2025)](https://www.kaggle.com/datasets/rohiteng/spotify-music-analytics-dataset-20152025) |
| **Author** | rohiteng |
| **Coverage** | ~85,000 tracks (2015–2025) |
| **Local file** | `data/raw/spotify_2015_2025_85k.csv` |

### Download

1. Open the [dataset page on Kaggle](https://www.kaggle.com/datasets/rohiteng/spotify-music-analytics-dataset-20152025).
2. Download the dataset (requires a free Kaggle account).
3. Place the CSV in `data/raw/` and name it `spotify_2015_2025_85k.csv` (or update `raw_file_name` in `configs/pipeline_config.yaml`).

Raw data is **not** committed to this repository. See `data/raw/README.md`.

### Columns used in the pipeline

`track_id`, `track_name`, `artist_name`, `album_name`, `release_date`, `genre`, `duration_ms`, `popularity`, `danceability`, `energy`, `key`, `loudness`, `mode`, `instrumentalness`, `tempo`, `stream_count`, `country`, `explicit`, `label`

> **License:** Use of the dataset is subject to Kaggle’s terms and the license shown on the dataset page. This project does not redistribute the data.

## Tech Stack

- Python + Pandas
- DuckDB
- Streamlit

## Project Structure

```text
spotify-analytics-pipeline/
├── configs/
│   └── pipeline_config.yaml
├── dashboards/
│   └── app.py
├── data/
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
├── database/
│   └── spotify_analytics.duckdb
├── scripts/
│   └── run_pipeline.py
└── src/
    ├── ingestion/
    │   └── load_raw_data.py
    ├── transformation/
    │   └── cleaning.py
    ├── warehouse/
    │   └── build_marts.py
    ├── utils/
    │   └── paths.py
    └── pipeline.py
```

## Setup

1. Create and activate your virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download the [Kaggle dataset](https://www.kaggle.com/datasets/rohiteng/spotify-music-analytics-dataset-20152025) and place the CSV at:

```text
data/raw/spotify_2015_2025_85k.csv
```

See the [Dataset](#dataset) section and `data/raw/README.md` for details.

## Run ETL Pipeline (optional)

```bash
python scripts/run_pipeline.py
```

This will:

- Ingest raw CSV
- Create cleaned silver dataset
- Build dimensional model + marts in DuckDB
- Export processed parquet layers in `data/bronze`, `data/silver`, and `data/gold`

## Run Dashboard

```bash
streamlit run dashboards/app.py
```
This runs both Dashboard and ETL pipeline together. Did this to run streamlit and etl together in streamlit deployment.

Dashboard includes:

- KPI cards (tracks, artists, total streams)
- Top tracks and artists
- Genre distribution
- Monthly stream trend
- Country performance

The dashboard sidebar includes filters for `Genre`, `Country`, and `Year`.

