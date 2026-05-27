import pandas as pd

NUMERIC_COLUMNS = [
    "duration_ms",
    "popularity",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "instrumentalness",
    "tempo",
    "stream_count",
    "explicit",
]


def clean_listening_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    cleaned = cleaned.drop_duplicates(subset=["track_id", "release_date", "country"])
    cleaned = cleaned.dropna(subset=["track_id", "track_name", "artist_name", "release_date"])

    cleaned["release_date"] = pd.to_datetime(cleaned["release_date"], errors="coerce", format="mixed")
    cleaned = cleaned.dropna(subset=["release_date"])

    cleaned[NUMERIC_COLUMNS] = cleaned[NUMERIC_COLUMNS].apply(
        pd.to_numeric, errors="coerce"
    )

    cleaned = cleaned.dropna(subset=["stream_count", "duration_ms"])

    cleaned["stream_count"] = cleaned["stream_count"].clip(lower=0).astype("int64")
    cleaned["duration_min"] = (cleaned["duration_ms"] / 60000).round(2)
    cleaned["year"] = cleaned["release_date"].dt.year.astype("int64")
    cleaned["month"] = cleaned["release_date"].dt.month.astype("int64")
    cleaned["year_month"] = cleaned["release_date"].dt.strftime("%Y-%m")

    cleaned[["genre", "country", "label"]] = cleaned[["genre", "country", "label"]].fillna(
        "Unknown"
    )

    return cleaned.reset_index(drop=True)
