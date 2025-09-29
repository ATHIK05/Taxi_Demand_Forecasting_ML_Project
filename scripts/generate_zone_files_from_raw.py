import argparse
import json
from pathlib import Path
from typing import Dict

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MAP_PATH = DATA_DIR / "hub_to_zone.json"


def build_or_load_zone_map(hubs: pd.Series) -> Dict[str, int]:
    """Create or load a stable mapping from hub name (City column after expansion) to integer PUZone.
    Saves/loads JSON at data/hub_to_zone.json so repeated runs keep the same codes.
    """
    existing: Dict[str, int] = {}
    if MAP_PATH.exists():
        existing = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    # Ensure all hubs have a code, assign new codes sequentially after max(existing)
    next_code = (max(existing.values()) + 1) if existing else 0
    for hub in hubs.sort_values().unique():
        if hub not in existing:
            existing[hub] = next_code
            next_code += 1

    MAP_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return existing


def main():
    parser = argparse.ArgumentParser(description="Generate monthly *_1H_zone.csv files from hub-level RAW dataset.")
    parser.add_argument("--input", default=str(DATA_DIR / "tamilnadu_taxi_raw.csv"), help="Path to RAW hub-level CSV (City=hub, CityName=city, Count, PUTime)")
    parser.add_argument("--city_col", default="City", help="Hub column name in RAW (used as zone label)")
    parser.add_argument("--count_col", default="Count", help="Count column name")
    parser.add_argument("--time_col", default="PUTime", help="Pickup time column name")
    parser.add_argument("--output_dir", default=str(DATA_DIR), help="Directory to write monthly zone files")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    required = [args.city_col, args.count_col, args.time_col]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"Missing column in RAW dataset: {c}")

    # Normalize dtypes
    df[args.count_col] = pd.to_numeric(df[args.count_col], errors="coerce").fillna(0).astype(int)
    # Ensure datetime
    df[args.time_col] = pd.to_datetime(df[args.time_col])

    # Build stable zone mapping
    zone_map = build_or_load_zone_map(df[args.city_col].astype(str))
    df["PUZone"] = df[args.city_col].map(zone_map)

    # Aggregate by (PUZone, PUTime) to ensure single row per hour per zone
    agg = (
        df.groupby(["PUZone", args.time_col], as_index=False)[args.count_col]
        .sum()
        .rename(columns={args.time_col: "PUTime"})
    )

    # Split by month and write files like YYYY-MM_1H_zone.csv
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    agg["month_str"] = agg["PUTime"].dt.strftime("%Y-%m")

    for month, g in agg.groupby("month_str", as_index=False):
        g = g.sort_values(["PUTime", "PUZone"]).reset_index(drop=True)
        g.insert(0, "Unnamed: 0", range(len(g)))
        out_path = out_dir / f"{month}_1H_zone.csv"
        g[["Unnamed: 0", "PUZone", args.count_col, "PUTime"]].to_csv(out_path, index=False)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()


