from pathlib import Path
import sys

import duckdb
import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.paths import DATABASE_DIR
from scripts.run_pipeline import run_pipeline

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_LIGHT = "#1ED760"
SPOTIFY_GREEN_DARK = "#169C46"
SPOTIFY_BLACK = "#121212"
PIE_COLORS = px.colors.qualitative.Set2

pio.templates.default = "plotly_dark"

AXIS_TITLE_FONT = dict(size=14, color="#FFFFFF", family="Arial Black")
CHART_TITLE_FONT = dict(size=16, color="#FFFFFF", family="Arial Black")

run_pipeline()
def format_label(name: str) -> str:
    return name.replace("_", " ").title()


def format_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=format_label)


def style_bold_headers(df: pd.DataFrame):
    return df.style.set_table_styles(
        [
            {
                "selector": "th",
                "props": [
                    ("font-weight", "bold"),
                    ("text-align", "left"),
                    ("color", "#FFFFFF"),
                ],
            }
        ],
        overwrite=False,
    )


def apply_chart_theme(fig, x_title: str | None = None, y_title: str | None = None):
    fig.update_layout(
        paper_bgcolor=SPOTIFY_BLACK,
        plot_bgcolor="#181818",
        font_color="#FFFFFF",
        title_font=CHART_TITLE_FONT,
    )
    if x_title:
        fig.update_xaxes(title_text=format_label(x_title), title_font=AXIS_TITLE_FONT)
    if y_title:
        fig.update_yaxes(title_text=format_label(y_title), title_font=AXIS_TITLE_FONT)
    return fig


def apply_colorbar_title(fig, title: str = "Total Streams"):
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=dict(text=title, font=AXIS_TITLE_FONT),
        )
    )
    return fig


def sql_literal(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def build_in_clause(values: list[str], column_sql: str) -> str:
    if not values:
        return ""
    literals = ",".join(sql_literal(v) for v in values)
    return f"{column_sql} in ({literals})"


st.set_page_config(
    page_title="Spotify Analytics Dashboard",
    layout="wide",
    page_icon="🎧",
)

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {SPOTIFY_BLACK};
        }}
        h1, h2, h3 {{
            color: #FFFFFF !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {SPOTIFY_GREEN} !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: #B3B3B3 !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: #181818;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Spotify Analytics Dashboard")

db_path = DATABASE_DIR / "spotify_analytics.duckdb"

if not db_path.exists():
    st.warning("Database not found. Please run: python scripts/run_pipeline.py")
    st.stop()

conn = duckdb.connect(str(db_path), read_only=True)

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
    top_tracks_display = format_dataframe_columns(top_tracks)
    st.dataframe(
        style_bold_headers(top_tracks_display),
        width="stretch",
        hide_index=True,
    )

    fig_genre = px.pie(
        genre_performance.head(10),
        names="genre",
        values="total_streams",
        title="Top Genre Share",
        color_discrete_sequence=PIE_COLORS,
    )
    apply_chart_theme(fig_genre)
    st.plotly_chart(fig_genre, width="stretch")

with right:
    st.subheader("Top Artists")
    fig_artists = px.bar(
        top_artists.sort_values("total_streams", ascending=True),
        x="total_streams",
        y="artist_name",
        orientation="h",
        title="Top Artists By Streams",
        color="total_streams",
        color_continuous_scale=[[0, SPOTIFY_GREEN_DARK], [1, SPOTIFY_GREEN]],
    )
    apply_chart_theme(fig_artists, x_title="total_streams", y_title="artist_name")
    apply_colorbar_title(fig_artists)
    st.plotly_chart(fig_artists, width="stretch")

    fig_country = px.bar(
        country_performance.sort_values("total_streams", ascending=True),
        x="total_streams",
        y="country",
        orientation="h",
        title="Top Countries By Streams",
        color="total_streams",
        color_continuous_scale=[[0, SPOTIFY_GREEN_DARK], [1, SPOTIFY_GREEN]],
    )
    apply_chart_theme(fig_country, x_title="total_streams", y_title="country")
    apply_colorbar_title(fig_country)
    st.plotly_chart(fig_country, width="stretch")

st.subheader("Monthly Streaming Trend")
monthly["year_month"] = pd.to_datetime(monthly["year_month"] + "-01", format="%Y-%m-%d")
fig_monthly = px.line(
    monthly,
    x="year_month",
    y="total_streams",
    markers=True,
    title="Monthly Streams",
    color_discrete_sequence=[SPOTIFY_GREEN],
)
fig_monthly.update_traces(line_color=SPOTIFY_GREEN, marker_color=SPOTIFY_GREEN_LIGHT)
apply_chart_theme(fig_monthly, x_title="year-month", y_title="total_streams")
st.plotly_chart(fig_monthly, width="stretch")
