from pathlib import Path
import sys

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.paths import DATABASE_DIR


st.set_page_config(page_title="Spotify Analytics Dashboard", layout="wide")
st.title("Spotify Analytics Dashboard")

db_path = DATABASE_DIR / "spotify_analytics.duckdb"

if not db_path.exists():
    st.warning("Database not found. Please run: python scripts/run_pipeline.py")
    st.stop()

conn = duckdb.connect(str(db_path), read_only=True)

def sql_literal(value: str) -> str:
    # Minimal escaping for safe local dashboard usage.
    return "'" + str(value).replace("'", "''") + "'"


def build_in_clause(values: list[str], column_sql: str) -> str:
    if not values:
        return ""
    literals = ",".join(sql_literal(v) for v in values)
    return f"{column_sql} in ({literals})"


st.sidebar.header("Filters")

all_genres = conn.execute("select distinct genre from dim_tracks order by genre").df()["genre"].tolist()
all_countries = conn.execute("select distinct country from fact_streams order by country").df()["country"].tolist()
all_years = (
    conn.execute("select distinct year from dim_dates order by year").df()["year"].dropna().tolist()
)

selected_genres = st.sidebar.multiselect("Genre", options=all_genres, default=[])
selected_countries = st.sidebar.multiselect("Country", options=all_countries, default=[])
selected_years = st.sidebar.multiselect("Year", options=all_years, default=[])

filters = []
genre_pred = build_in_clause(selected_genres, "d.genre")
if genre_pred:
    filters.append(genre_pred)

country_pred = build_in_clause(selected_countries, "f.country")
if country_pred:
    filters.append(country_pred)

year_pred = build_in_clause([str(y) for y in selected_years], "cast(year(f.release_date) as varchar)")
if year_pred:
    filters.append(year_pred)

where_sql = ""
if filters:
    where_sql = "where " + " and ".join(filters)

kpis = conn.execute(
    f"""
    select
        count(distinct f.track_id) as total_tracks,
        count(distinct d.artist_name) as total_artists,
        coalesce(sum(f.stream_count), 0) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    """
).df()

top_tracks = conn.execute(
    f"""
    select
        d.track_name,
        d.artist_name,
        d.genre,
        sum(f.stream_count) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    group by 1,2,3
    order by total_streams desc
    limit 15
    """
).df()

genre_performance = conn.execute(
    f"""
    select
        d.genre,
        sum(f.stream_count) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    group by 1
    order by total_streams desc
    """
).df()

monthly = conn.execute(
    f"""
    select
        strftime(f.release_date, '%Y-%m') as year_month,
        sum(f.stream_count) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    group by 1
    order by 1
    """
).df()

country_performance = conn.execute(
    f"""
    select
        f.country,
        sum(f.stream_count) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    group by 1
    order by total_streams desc
    limit 15
    """
).df()

top_artists = conn.execute(
    f"""
    select
        d.artist_name,
        sum(f.stream_count) as total_streams
    from fact_streams f
    join dim_tracks d using(track_id)
    {where_sql}
    group by 1
    order by total_streams desc
    limit 15
    """
).df()

conn.close()

if kpis.empty:
    kpis = pd.DataFrame(
        [{"total_tracks": 0, "total_artists": 0, "total_streams": 0}]
    )

col1, col2, col3 = st.columns(3)
col1.metric("Total Tracks", f"{int(kpis.loc[0, 'total_tracks']):,}")
col2.metric("Total Artists", f"{int(kpis.loc[0, 'total_artists']):,}")
col3.metric("Total Streams", f"{int(kpis.loc[0, 'total_streams']):,}")

left, right = st.columns(2)

with left:
    st.subheader("Top Tracks")
    st.dataframe(top_tracks, use_container_width=True, hide_index=True)

    fig_genre = px.pie(
        genre_performance.head(10),
        names="genre",
        values="total_streams",
        title="Top Genre Share",
    )
    st.plotly_chart(fig_genre, use_container_width=True)

with right:
    st.subheader("Top Artists")
    fig_artists = px.bar(
        top_artists.sort_values("total_streams", ascending=True),
        x="total_streams",
        y="artist_name",
        orientation="h",
        title="Top Artists by Streams",
    )
    st.plotly_chart(fig_artists, use_container_width=True)

    fig_country = px.bar(
        country_performance.sort_values("total_streams", ascending=True),
        x="total_streams",
        y="country",
        orientation="h",
        title="Top Countries by Streams",
    )
    st.plotly_chart(fig_country, use_container_width=True)

st.subheader("Monthly Streaming Trend")
monthly["year_month"] = pd.to_datetime(monthly["year_month"] + "-01")
fig_monthly = px.line(monthly, x="year_month", y="total_streams", markers=True)
st.plotly_chart(fig_monthly, use_container_width=True)
