import pandas as pd


def ingest_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df.columns = [col.strip().lower() for col in df.columns]
    return df
