from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
DATABASE_DIR = ROOT_DIR / "database"
CONFIGS_DIR = ROOT_DIR / "configs"


def ensure_directories() -> None:
    for directory in [BRONZE_DIR, SILVER_DIR, GOLD_DIR, DATABASE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
