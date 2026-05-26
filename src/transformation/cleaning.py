import pandas as pd


def clean_listening_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()

    cleaned = cleaned.drop_duplicates(subset=["track_id", "release_date", "country"])
    cleaned = cleaned.dropna(subset=["track_id", "track_name", "artist_name", "release_date"])

    cleaned["release_date"] = pd.to_datetime(cleaned["release_date"], errors="coerce")
    cleaned = cleaned.dropna(subset=["release_date"])

    numeric_columns = [
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

    for col in numeric_columns:
        cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

    cleaned = cleaned.dropna(subset=["stream_count", "duration_ms"])

    cleaned["stream_count"] = cleaned["stream_count"].clip(lower=0).astype("int64")
    cleaned["duration_min"] = (cleaned["duration_ms"] / 60000).round(2)
    cleaned["year"] = cleaned["release_date"].dt.year
    cleaned["month"] = cleaned["release_date"].dt.month
    cleaned["year_month"] = cleaned["release_date"].dt.to_period("M").astype(str)

    cleaned["genre"] = cleaned["genre"].fillna("Unknown")
    cleaned["country"] = cleaned["country"].fillna("Unknown")
    cleaned["label"] = cleaned["label"].fillna("Unknown")

    return cleaned.reset_index(drop=True)
