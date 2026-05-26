from pathlib import Path

import duckdb
import pandas as pd


def load_warehouse(df: pd.DataFrame, db_path: Path) -> None:
    conn = duckdb.connect(str(db_path))

    conn.register("silver_df", df)

    conn.execute(
        """
        create or replace table fact_streams as
        select
            track_id,
            release_date,
            country,
            stream_count,
            popularity,
            danceability,
            energy,
            tempo,
            explicit
        from silver_df
        """
    )

    conn.execute(
        """
        create or replace table dim_tracks as
        select distinct
            track_id,
            track_name,
            artist_name,
            album_name,
            genre,
            duration_ms,
            duration_min,
            label
        from silver_df
        """
    )

    conn.execute(
        """
        create or replace table dim_artists as
        select
            artist_name,
            count(distinct track_id) as track_count,
            avg(popularity) as avg_popularity
        from silver_df
        group by 1
        """
    )

    conn.execute(
        """
        create or replace table dim_dates as
        select distinct
            release_date::date as date_key,
            year(release_date) as year,
            month(release_date) as month,
            strftime(release_date, '%Y-%m') as year_month
        from silver_df
        """
    )

    conn.execute(
        """
        create or replace table mart_monthly_streams as
        select
            strftime(release_date, '%Y-%m') as year_month,
            sum(stream_count) as total_streams
        from fact_streams
        group by 1
        order by 1
        """
    )

    conn.execute(
        """
        create or replace table mart_genre_performance as
        select
            d.genre,
            sum(f.stream_count) as total_streams,
            avg(f.popularity) as avg_popularity,
            count(distinct f.track_id) as unique_tracks
        from fact_streams f
        join dim_tracks d using(track_id)
        group by 1
        order by total_streams desc
        """
    )

    conn.execute(
        """
        create or replace table mart_top_tracks as
        select
            f.track_id,
            d.track_name,
            d.artist_name,
            d.genre,
            sum(f.stream_count) as total_streams
        from fact_streams f
        join dim_tracks d using(track_id)
        group by 1, 2, 3, 4
        order by total_streams desc
        """
    )

    conn.close()
