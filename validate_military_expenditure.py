from __future__ import annotations

import argparse
import math
from pathlib import Path
from zipfile import ZipFile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"Entity", "Year", "Military expenditure"}
COUNTRY_CODE_PATTERN = r"^[A-Z]{3}$"


def load_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            candidates = [
                name for name in archive.namelist() if name.lower().endswith(".csv")
            ]
            if not candidates:
                raise ValueError("ZIP file does not contain a CSV file.")

            target = None
            for name in candidates:
                if Path(name).name == "military-spending-sipri.csv":
                    target = name
                    break
            if target is None:
                target = candidates[0]

            with archive.open(target) as csv_file:
                return pd.read_csv(csv_file)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    raise ValueError("Input must be a CSV file or a ZIP containing a CSV file.")


def validate_and_prepare(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    missing_columns = REQUIRED_COLUMNS - set(raw.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

    df = raw.copy()

    year_numeric = pd.to_numeric(df["Year"], errors="coerce")
    year_is_whole_number = year_numeric.notna() & np.isfinite(year_numeric) & (year_numeric % 1 == 0)

    spending_numeric = pd.to_numeric(df["Military expenditure"], errors="coerce")
    spending_is_finite = spending_numeric.notna() & np.isfinite(spending_numeric)
    spending_is_non_negative = spending_numeric >= 0

    df["year_numeric"] = year_numeric
    df["spending_numeric"] = spending_numeric
    df["year_invalid"] = ~year_is_whole_number
    df["spending_invalid"] = ~(spending_is_finite & spending_is_non_negative)

    df.loc[year_is_whole_number, "year_int"] = year_numeric[year_is_whole_number].astype(int)
    df["is_country"] = df.get("Code", pd.Series(index=df.index, dtype="object")).fillna("").str.match(
        COUNTRY_CODE_PATTERN
    )

    duplicate_country_year = (
        df[df["is_country"] & ~df["year_invalid"]]
        .duplicated(subset=["Entity", "year_int"], keep=False)
        .reindex(df.index, fill_value=False)
    )
    df["duplicate_country_year"] = duplicate_country_year

    summary = {
        "total_rows": int(len(df)),
        "invalid_year_rows": int(df["year_invalid"].sum()),
        "invalid_spending_rows": int(df["spending_invalid"].sum()),
        "duplicate_country_year_rows": int(df["duplicate_country_year"].sum()),
        "aggregate_rows": int((~df["is_country"]).sum()),
    }

    return df, summary


def compute_country_2025_stats(df: pd.DataFrame, sample_std: bool) -> tuple[pd.DataFrame, dict[str, float]]:
    valid_country_rows = df[
        df["is_country"]
        & ~df["year_invalid"]
        & ~df["spending_invalid"]
        & ~df["duplicate_country_year"]
    ].copy()

    subset_2025 = valid_country_rows[valid_country_rows["year_int"] == 2025].copy()
    if subset_2025.empty:
        raise ValueError("No valid country rows found for year 2025.")

    spend = subset_2025["spending_numeric"]
    std_ddof = 1 if sample_std else 0

    stats = {
        "country_count": float(len(subset_2025)),
        "mean": float(spend.mean()),
        "median": float(spend.median()),
        "std": float(spend.std(ddof=std_ddof)),
        "std_ddof": float(std_ddof),
    }

    top_10 = subset_2025.sort_values("spending_numeric", ascending=False).head(10)
    return top_10, stats


def compute_world_growth(df: pd.DataFrame) -> dict[str, float]:
    world = df[
        df["Entity"].eq("World")
        & ~df["year_invalid"]
        & ~df["spending_invalid"]
    ][["year_int", "spending_numeric"]].copy()

    if world.empty:
        raise ValueError("No valid World rows found for growth calculation.")

    world = world.sort_values("year_int")
    world = world.drop_duplicates(subset=["year_int"], keep="last")

    first_year = int(world.iloc[0]["year_int"])
    last_year = int(world.iloc[-1]["year_int"])
    first_value = float(world.iloc[0]["spending_numeric"])
    last_value = float(world.iloc[-1]["spending_numeric"])

    if first_value <= 0:
        raise ValueError("Cannot compute growth rates when first World value is <= 0.")

    elapsed_years = last_year - first_year
    if elapsed_years <= 0:
        raise ValueError("Cannot compute CAGR when elapsed years is 0.")

    pct_growth = ((last_value - first_value) / first_value) * 100
    cagr = (last_value / first_value) ** (1 / elapsed_years) - 1

    return {
        "first_year": float(first_year),
        "last_year": float(last_year),
        "first_value": first_value,
        "last_value": last_value,
        "percent_growth": pct_growth,
        "cagr": cagr,
    }


def create_distribution_chart(df: pd.DataFrame, output_chart: Path) -> None:
    subset_2025 = df[
        df["is_country"]
        & ~df["year_invalid"]
        & ~df["spending_invalid"]
        & ~df["duplicate_country_year"]
        & df["year_int"].eq(2025)
    ].copy()

    values = subset_2025["spending_numeric"]
    positive_values = values[values > 0]

    if positive_values.empty:
        raise ValueError("No positive 2025 country values available for charting.")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bins = np.logspace(math.log10(positive_values.min()), math.log10(positive_values.max()), 25)

    ax.hist(positive_values, bins=bins, color="#4C78A8", edgecolor="white", alpha=0.9)
    ax.set_xscale("log")
    ax.set_title("Distribution of 2025 country military expenditure")
    ax.set_xlabel("Military expenditure (constant 2024 US$, logarithmic scale)")
    ax.set_ylabel("Number of countries")
    ax.grid(axis="y", alpha=0.25)

    fig.tight_layout()
    output_chart.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_chart, dpi=300)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and analyze SIPRI military expenditure data."
    )
    parser.add_argument("--input", required=True, type=Path, help="Path to CSV or ZIP data file")
    parser.add_argument(
        "--output-chart",
        type=Path,
        default=Path("military_expenditure_distribution_2025.png"),
        help="Path for generated chart image",
    )
    parser.add_argument(
        "--population-std",
        action="store_true",
        help="Use population standard deviation (ddof=0). Default is sample std (ddof=1).",
    )

    args = parser.parse_args()

    raw = load_input(args.input)
    df, validation_summary = validate_and_prepare(raw)

    top_10, stats = compute_country_2025_stats(df, sample_std=not args.population_std)
    growth = compute_world_growth(df)
    create_distribution_chart(df, args.output_chart)

    included_rows = int(
        (
            df["is_country"]
            & ~df["year_invalid"]
            & ~df["spending_invalid"]
            & ~df["duplicate_country_year"]
        ).sum()
    )
    excluded_rows = int(len(df) - included_rows)

    print("\nVALIDATION SUMMARY")
    print("-" * 72)
    print(f"Total rows reviewed: {validation_summary['total_rows']}")
    print(f"Rows with invalid year values: {validation_summary['invalid_year_rows']}")
    print(f"Rows with invalid expenditure values: {validation_summary['invalid_spending_rows']}")
    print(f"Rows with duplicate country-year: {validation_summary['duplicate_country_year_rows']}")
    print(f"Aggregate/non-country rows excluded from country analysis: {validation_summary['aggregate_rows']}")
    print(f"Included rows for country analysis: {included_rows}")
    print(f"Excluded rows from country analysis: {excluded_rows}")

    print("\n2025 COUNTRY SUMMARY (calculated from observed records)")
    print("-" * 72)
    print(f"Country count: {stats['country_count']:.0f}")
    print(f"Mean expenditure: {stats['mean']:,.2f}")
    print(f"Median expenditure: {stats['median']:,.2f}")
    std_kind = "sample" if int(stats["std_ddof"]) == 1 else "population"
    print(f"Standard deviation ({std_kind}, ddof={int(stats['std_ddof'])}): {stats['std']:,.2f}")

    print("\nTOP 10 COUNTRIES BY 2025 EXPENDITURE")
    print("-" * 72)
    print(
        top_10[["Entity", "spending_numeric"]]
        .rename(columns={"Entity": "Country", "spending_numeric": "Military expenditure"})
        .to_string(index=False, formatters={"Military expenditure": "{:,.2f}".format})
    )

    print("\nWORLD GROWTH FROM FIRST TO LAST OBSERVED YEAR")
    print("-" * 72)
    print(
        f"{int(growth['first_year'])} to {int(growth['last_year'])}: "
        f"{growth['first_value']:,.2f} -> {growth['last_value']:,.2f}"
    )
    print(f"Percentage growth: {growth['percent_growth']:.2f}%")
    print(f"Compound annual growth rate (CAGR): {growth['cagr'] * 100:.2f}%")

    print(f"\nChart saved to: {args.output_chart.resolve()}")


if __name__ == "__main__":
    main()
