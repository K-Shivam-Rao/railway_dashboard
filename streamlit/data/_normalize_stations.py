"""
Normalize station names in stations.csv to consistent German convention:
- German city names with proper umlauts (München, Köln, Düsseldorf, Nürnberg)
- "Hbf" abbreviation for Hauptbahnhof stations
- Regenerate parquet
"""
import pandas as pd
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "stations.csv")
PARQUET_PATH = os.path.join(os.path.dirname(__file__), "stations.parquet")

STATION_RENAME = {
    # Original Hauptbahnhof → proper German abbreviation
    "Berlin Hauptbahnhof": "Berlin Hbf",
    "Munchen Hauptbahnhof": "München Hbf",
    "Hamburg Hauptbahnhof": "Hamburg Hbf",
    "Frankfurt (Main) Hbf": "Frankfurt Hbf",
    "Koln Hauptbahnhof": "Köln Hbf",
    "Stuttgart Hauptbahnhof": "Stuttgart Hbf",
    "Leipzig Hauptbahnhof": "Leipzig Hbf",
    # ASCII substitutions → proper umlauts
    "Berlin Suedkreuz": "Berlin Südkreuz",
    "Muenchen Ost": "München Ost",
    "Koeln Messe/Deutz": "Köln Messe/Deutz",
    "Duesseldorf Flughafen": "Düsseldorf Flughafen",
    # Keep already correct names (no change needed)
    # "Dortmund Hbf" → "Dortmund Hbf"
    # "Düsseldorf Hbf" → "Düsseldorf Hbf"
    # "Hannover Hbf" → "Hannover Hbf"
    # "Bremen Hbf" → "Bremen Hbf"
    # "Kiel Hbf" → "Kiel Hbf"
    # "Mainz Hbf" → "Mainz Hbf"
    # "Nürnberg Hbf" → "Nürnberg Hbf"
    # "Freiburg Hbf" → "Freiburg Hbf"
    # "Mannheim Hbf" → "Mannheim Hbf"
    # "Dresden Hbf" → "Dresden Hbf"
    # "Berlin Ostbahnhof" → "Berlin Ostbahnhof"
    # "Frankfurt Flughafen" → "Frankfurt Flughafen"
    # "Hamburg Altona" → "Hamburg Altona"
    # "Stuttgart Flughafen" → "Stuttgart Flughafen"
    # "Hannover Messe/Laatzen" → "Hannover Messe/Laatzen"
    # "Leipzig/Halle Flughafen" → "Leipzig/Halle Flughafen"
}


def main():
    df = pd.read_csv(CSV_PATH)
    old_stations = sorted(df["station"].unique().tolist())
    print(f"Old stations ({len(old_stations)}):")
    for s in old_stations:
        print(f"  {s}")

    # Apply rename
    df["station"] = df["station"].replace(STATION_RENAME)
    new_stations = sorted(df["station"].unique().tolist())
    print(f"\nNew stations ({len(new_stations)}):")
    for s in new_stations:
        print(f"  {s}")

    # Verify counts match
    assert len(old_stations) == len(new_stations), "Station count mismatch after rename!"

    # Save CSV
    df.to_csv(CSV_PATH, index=False)
    print(f"\n✅ Saved {len(df)} rows to stations.csv")

    # Regenerate parquet
    try:
        import polars as pl
        df_pl = pl.from_pandas(df)
        df_pl.write_parquet(PARQUET_PATH, compression="zstd")
        print(f"✅ Saved parquet to stations.parquet ({os.path.getsize(PARQUET_PATH)/1024:.1f} KB)")
    except ImportError:
        try:
            df.to_parquet(PARQUET_PATH, compression="zstd")
            print(f"✅ Saved parquet via pyarrow ({os.path.getsize(PARQUET_PATH)/1024:.1f} KB)")
        except ImportError:
            print("⚠️  Parquet not regenerated (install polars or pyarrow)")


if __name__ == "__main__":
    main()
