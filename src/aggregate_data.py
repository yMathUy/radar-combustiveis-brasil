from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "anp_fuel_prices_2026_01_clean.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "aggregated"


def load_clean_data() -> pd.DataFrame:
    """Load the cleaned ANP fuel price dataset."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Clean dataset not found: {INPUT_FILE}"
        )

    dataframe = pd.read_csv(
        INPUT_FILE,
        parse_dates=["collection_date"],
        dtype={
            "region_code": "string",
            "state_code": "string",
            "municipality": "string",
            "station_name": "string",
            "station_tax_id": "string",
            "product": "string",
            "measurement_unit": "string",
            "brand": "string",
        },
        low_memory=False,
    )

    return dataframe


def add_week_information(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Add week boundaries and identify partial dataset weeks."""

    dataframe = dataframe.copy()

    collection_day = dataframe["collection_date"].dt.normalize()

    dataframe["week_start"] = (
        collection_day
        - pd.to_timedelta(
            collection_day.dt.weekday,
            unit="D",
        )
    )

    dataframe["week_end"] = (
        dataframe["week_start"]
        + pd.Timedelta(days=6)
    )

    dataset_start = dataframe["collection_date"].min()
    dataset_end = dataframe["collection_date"].max()

    dataframe["is_partial_week"] = (
        (dataframe["week_start"] < dataset_start)
        | (dataframe["week_end"] > dataset_end)
    )

    return dataframe


def aggregate_prices(
    dataframe: pd.DataFrame,
    group_columns: list[str],
) -> pd.DataFrame:
    """Calculate price and station metrics for each group."""

    aggregated = (
        dataframe.groupby(
            group_columns,
            observed=True,
            dropna=False,
        )
        .agg(
            average_price=("sale_price", "mean"),
            median_price=("sale_price", "median"),
            minimum_price=("sale_price", "min"),
            maximum_price=("sale_price", "max"),
            price_observations=("sale_price", "size"),
            station_count=("station_tax_id", "nunique"),
        )
        .reset_index()
    )

    price_columns = [
        "average_price",
        "median_price",
        "minimum_price",
        "maximum_price",
    ]

    aggregated[price_columns] = aggregated[price_columns].round(3)

    return aggregated.sort_values(
        by=group_columns
    ).reset_index(drop=True)


def create_municipality_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Create weekly fuel price metrics by municipality."""

    return aggregate_prices(
        dataframe,
        group_columns=[
            "week_start",
            "week_end",
            "is_partial_week",
            "state_code",
            "municipality",
            "product",
        ],
    )


def create_state_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Create weekly fuel price metrics by state."""

    return aggregate_prices(
        dataframe,
        group_columns=[
            "week_start",
            "week_end",
            "is_partial_week",
            "state_code",
            "product",
        ],
    )


def create_national_summary(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Create weekly national fuel price metrics."""

    return aggregate_prices(
        dataframe,
        group_columns=[
            "week_start",
            "week_end",
            "is_partial_week",
            "product",
        ],
    )


def save_dataframe(
    dataframe: pd.DataFrame,
    file_name: str,
) -> Path:
    """Save an aggregated table as a CSV file."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / file_name

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
        date_format="%Y-%m-%d",
    )

    return output_path


def validate_aggregated_data(
    dataframe: pd.DataFrame,
    table_name: str,
) -> None:
    """Validate the basic quality of an aggregated table."""

    if dataframe.empty:
        raise ValueError(
            f"The {table_name} table is empty."
        )

    if dataframe["average_price"].isna().any():
        raise ValueError(
            f"Missing average prices found in {table_name}."
        )

    if (dataframe["price_observations"] <= 0).any():
        raise ValueError(
            f"Invalid observation counts found in {table_name}."
        )


def main() -> None:
    """Create and save weekly fuel price summary tables."""

    print(f"Loading dataset: {INPUT_FILE.name}")

    dataframe = load_clean_data()

    print(f"Input rows: {len(dataframe):,}")

    dataframe = add_week_information(dataframe)

    national_summary = create_national_summary(dataframe)
    state_summary = create_state_summary(dataframe)
    municipality_summary = create_municipality_summary(dataframe)

    validate_aggregated_data(
        national_summary,
        "national summary",
    )
    validate_aggregated_data(
        state_summary,
        "state summary",
    )
    validate_aggregated_data(
        municipality_summary,
        "municipality summary",
    )

    national_output = save_dataframe(
        national_summary,
        "weekly_national_prices.csv",
    )

    state_output = save_dataframe(
        state_summary,
        "weekly_state_prices.csv",
    )

    municipality_output = save_dataframe(
        municipality_summary,
        "weekly_municipality_prices.csv",
    )

    print("\nAggregated tables created:")

    print(
        f"- National: {len(national_summary):,} rows "
        f"({national_output})"
    )

    print(
        f"- State: {len(state_summary):,} rows "
        f"({state_output})"
    )

    print(
        f"- Municipality: {len(municipality_summary):,} rows "
        f"({municipality_output})"
    )

    print("\nData aggregation completed successfully.")


if __name__ == "__main__":
    main()