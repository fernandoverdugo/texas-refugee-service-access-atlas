from pathlib import Path

from src.ingestion.acs import fetch_dfw_acs


OUTPUT = Path("data/processed/acs_dfw_tracts.csv")


def main() -> None:
    frame = fetch_dfw_acs()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False)
    print(
        {
            "rows": len(frame),
            "counties": frame["county_name"].nunique(),
            "tracts": frame["geoid"].nunique(),
            "output": str(OUTPUT),
        }
    )


if __name__ == "__main__":
    main()
