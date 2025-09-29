import argparse
import hashlib
import os
from pathlib import Path
from typing import List, Dict

import pandas as pd


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def read_hub_list_for_city(city_name: str, expected_count: int = 72) -> List[str]:
    """Load hub list for the given city from data/hubs_<city>.txt or .csv.
    If not found, generate deterministic placeholder hubs to ensure the script runs.
    """
    city_key = city_name.strip().lower().replace(" ", "_")
    candidates = [
        DATA_DIR / f"hubs_{city_key}.txt",
        DATA_DIR / f"hubs_{city_key}.csv",
    ]

    for p in candidates:
        if p.exists():
            if p.suffix == ".txt":
                hubs = [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
                break
            else:
                # CSV: prefer a column named 'hub' else first column
                df = pd.read_csv(p)
                if "hub" in df.columns:
                    hubs = df["hub"].dropna().astype(str).str.strip().tolist()
                else:
                    hubs = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                break
    else:
        # Fallback: deterministic placeholders
        hubs = [f"{city_name} Hub {i:02d}" for i in range(1, expected_count + 1)]

    # Normalize, ensure uniqueness and size
    hubs = [h for h in (x.strip() for x in hubs) if h]
    # Deduplicate preserving order
    seen = set()
    unique_hubs = []
    for h in hubs:
        if h not in seen:
            unique_hubs.append(h)
            seen.add(h)

    if len(unique_hubs) < expected_count:
        # Pad deterministically
        for i in range(len(unique_hubs) + 1, expected_count + 1):
            unique_hubs.append(f"{city_name} Hub {i:02d}")
    elif len(unique_hubs) > expected_count:
        unique_hubs = unique_hubs[:expected_count]

    return unique_hubs


def build_hub_lookup(cities: List[str], expected_count: int = 72) -> Dict[str, List[str]]:
    return {city: read_hub_list_for_city(city, expected_count) for city in cities}


def deterministic_index(*parts: str, modulo: int) -> int:
    hasher = hashlib.sha256()
    for p in parts:
        hasher.update(str(p).encode("utf-8"))
        hasher.update(b"||")
    return int.from_bytes(hasher.digest()[:8], "big") % modulo


def assign_hub(row, hub_lookup: Dict[str, List[str]], city_col: str, time_col: str) -> str:
    city = str(row[city_col])
    hubs = hub_lookup.get(city)
    if not hubs:
        # Leave untouched if city not targeted
        return city
    # Use time plus count to distribute deterministically
    key_parts = [city, str(row.get(time_col, "")), str(row.get("Count", ""))]
    idx = deterministic_index(*key_parts, modulo=len(hubs))
    return hubs[idx]


def main():
    parser = argparse.ArgumentParser(description="Generate RAW hub-level dataset from processed city-level dataset.")
    parser.add_argument("--input", default=str(DATA_DIR / "tamilnadu_taxi_demand.csv"), help="Path to processed CSV (City,Count,PUTime)")
    parser.add_argument("--output", default=str(DATA_DIR / "tamilnadu_taxi_raw.csv"), help="Path to write raw hub-level CSV")
    parser.add_argument("--target_cities", nargs="*", default=["Erode", "Chennai", "Salem"], help="Cities to expand into hubs")
    parser.add_argument("--city_col", default="City", help="City column name in input")
    parser.add_argument("--count_col", default="Count", help="Count column name in input")
    parser.add_argument("--time_col", default="PUTime", help="Time column name in input")
    parser.add_argument("--hubs_per_city", type=int, default=72, help="Number of hubs per city")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    missing_cols = [c for c in [args.city_col, args.count_col, args.time_col] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")

    hub_lookup = build_hub_lookup(args.target_cities, expected_count=args.hubs_per_city)

    # Preserve original city in a new column
    df["CityName"] = df[args.city_col]

    # Assign hubs only for target cities
    df[args.city_col] = df.apply(
        lambda r: assign_hub(r, hub_lookup, city_col="CityName", time_col=args.time_col), axis=1
    )

    # Reorder columns: City (hub), CityName (city), Count, PUTime
    out_cols = [args.city_col, "CityName", args.count_col, args.time_col]
    other_cols = [c for c in df.columns if c not in out_cols]
    df_out = df[out_cols + other_cols]

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.output, index=False)
    print(f"Wrote RAW hub-level dataset: {args.output}")


if __name__ == "__main__":
    main()


