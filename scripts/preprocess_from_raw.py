import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description="Aggregate RAW hub-level dataset back to processed city-level dataset.")
    parser.add_argument("--input", default=str(Path(__file__).resolve().parents[1] / "data" / "tamilnadu_taxi_raw.csv"), help="Path to raw hub-level CSV")
    parser.add_argument("--output", default=str(Path(__file__).resolve().parents[1] / "data" / "tamilnadu_taxi_demand_from_raw.csv"), help="Path to write processed city-level CSV")
    parser.add_argument("--city_col", default="CityName", help="Original city column name in raw (preserved city)")
    parser.add_argument("--count_col", default="Count", help="Count column name")
    parser.add_argument("--time_col", default="PUTime", help="Pickup time column name")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    for col in [args.city_col, args.count_col, args.time_col]:
        if col not in df.columns:
            raise ValueError(f"Missing required column in raw dataset: {col}")

    # Ensure correct dtypes
    # If Count is not numeric, coerce
    df[args.count_col] = pd.to_numeric(df[args.count_col], errors="coerce").fillna(0).astype(int)

    # Aggregate back to city-level counts per time
    grouped = (
        df.groupby([args.city_col, args.time_col], as_index=False)[args.count_col]
        .sum()
        .rename(columns={args.city_col: "City"})
    )

    grouped = grouped[["City", args.count_col, args.time_col]]

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    grouped.to_csv(args.output, index=False)
    print(f"Wrote processed dataset from raw: {args.output}")


if __name__ == "__main__":
    main()


