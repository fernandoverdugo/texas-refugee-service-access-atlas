from pathlib import Path

import pandas as pd

from src.ingestion.gtfs import (
    build_gtfs_summary,
    download_gtfs_zip,
    save_core_gtfs_tables,
)


OUTPUT_DIR = Path("data/processed/gtfs")
SUMMARY_PATH = Path("data/processed/dart_gtfs_summary.csv")


def main() -> None:
    content = download_gtfs_zip()
    summary = build_gtfs_summary(content)
    save_core_gtfs_tables(content, OUTPUT_DIR)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([summary]).to_csv(SUMMARY_PATH, index=False)

    print(summary)


if __name__ == "__main__":
    main()
