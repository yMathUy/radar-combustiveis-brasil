from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_national_prices.csv"
)


def load_national_summary() -> pd.DataFrame:
    """Load the weekly national fuel price summary."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"National summary file not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        INPUT_FILE,
        parse_dates=[
            "week_start",
            "week_end",
        ],
            dtype={
                "product": "string",
                "measurement_unit": "string",
            },
    )

    return dataframe


def normalize_partial_week_column(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Ensure that is_partial_week contains Boolean values."""

    dataframe = dataframe.copy()

    if dataframe["is_partial_week"].dtype != bool:
        dataframe["is_partial_week"] = (
            dataframe["is_partial_week"]
            .astype("string")
            .str.strip()
            .map(
                {
                    "True": True,
                    "False": False,
                }
            )
        )

    if dataframe["is_partial_week"].isna().any():
        raise ValueError(
            "Invalid values were found in is_partial_week."
        )

    return dataframe


def get_latest_complete_week(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return fuel prices from the latest complete week."""

    complete_weeks = dataframe[
        ~dataframe["is_partial_week"]
    ].copy()

    if complete_weeks.empty:
        raise ValueError(
            "No complete weeks were found in the dataset."
        )

    latest_week_start = complete_weeks["week_start"].max()

    latest_week = complete_weeks[
        complete_weeks["week_start"] == latest_week_start
    ].copy()

    return latest_week.sort_values(
        by="average_price",
        ascending=False,
    ).reset_index(drop=True)


def display_latest_prices(dataframe: pd.DataFrame) -> None:
    """Display the latest complete weekly fuel price summary."""

    week_start = dataframe["week_start"].iloc[0]
    week_end = dataframe["week_end"].iloc[0]

    print(
        "Latest complete week: "
        f"{week_start.date()} to {week_end.date()}"
    )

    print("\nNational fuel prices:\n")

    header = (
        f"{'Product':<20} | "
        f"{'Unit':<12} | "
        f"{'Average':>9} | "
        f"{'Median':>9} | "
        f"{'Minimum':>9} | "
        f"{'Maximum':>9} | "
        f"{'Observations':>12} | "
        f"{'Stations':>8}"
    )

    print(header)
    print("-" * len(header))

    for row in dataframe.itertuples(index=False):
        print(
            f"{row.product:<20} | "
            f"{row.measurement_unit:<12} | "
            f"R$ {row.average_price:>6.3f} | "
            f"R$ {row.median_price:>6.3f} | "
            f"R$ {row.minimum_price:>6.3f} | "
            f"R$ {row.maximum_price:>6.3f} | "
            f"{row.price_observations:>12,} | "
            f"{row.station_count:>8,}"
        )

def main() -> None:
    """Analyze prices from the latest complete week."""

    dataframe = load_national_summary()

    dataframe = normalize_partial_week_column(dataframe)

    latest_week = get_latest_complete_week(dataframe)

    display_latest_prices(latest_week)


if __name__ == "__main__":
    main()