from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_state_prices.csv"
)

PRODUCT = "GASOLINA"
RANKING_SIZE = 10
MIN_OBSERVATIONS = 30

def filter_by_minimum_observations(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate states with sufficient and insufficient observations."""

    eligible_states = dataframe[
        dataframe["price_observations"] >= MIN_OBSERVATIONS
    ].copy()

    low_sample_states = dataframe[
        dataframe["price_observations"] < MIN_OBSERVATIONS
    ].copy()

    if eligible_states.empty:
        raise ValueError(
            "No states meet the minimum observation requirement."
        )

    return eligible_states, low_sample_states

def load_state_summary() -> pd.DataFrame:
    """Load the weekly state fuel price summary."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"State summary file not found: {INPUT_FILE}"
        )

    return pd.read_csv(
        INPUT_FILE,
        parse_dates=[
            "week_start",
            "week_end",
        ],
        dtype={
            "state_code": "string",
            "product": "string",
            "measurement_unit": "string",
        },
    )


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


def get_latest_state_prices(
    dataframe: pd.DataFrame,
    product: str,
) -> pd.DataFrame:
    """Return state prices for one product in the latest complete week."""

    filtered = dataframe[
        (~dataframe["is_partial_week"])
        & (dataframe["product"] == product)
    ].copy()

    if filtered.empty:
        raise ValueError(
            f"No complete-week data was found for product: {product}"
        )

    latest_week_start = filtered["week_start"].max()

    latest_week = filtered[
        filtered["week_start"] == latest_week_start
    ].copy()

    return latest_week.reset_index(drop=True)


def print_ranking(
    dataframe: pd.DataFrame,
    title: str,
) -> None:
    """Display a formatted state fuel price ranking."""

    print(f"\n{title}\n")

    header = (
        f"{'Rank':>4} | "
        f"{'State':<5} | "
        f"{'Average':>9} | "
        f"{'Median':>9} | "
        f"{'Minimum':>9} | "
        f"{'Maximum':>9} | "
        f"{'Observations':>12} | "
        f"{'Stations':>8}"
    )

    print(header)
    print("-" * len(header))

    for rank, row in enumerate(
        dataframe.itertuples(index=False),
        start=1,
    ):
        print(
            f"{rank:>4} | "
            f"{row.state_code:<5} | "
            f"R$ {row.average_price:>6.3f} | "
            f"R$ {row.median_price:>6.3f} | "
            f"R$ {row.minimum_price:>6.3f} | "
            f"R$ {row.maximum_price:>6.3f} | "
            f"{row.price_observations:>12,} | "
            f"{row.station_count:>8,}"
        )


def display_state_rankings(
    dataframe: pd.DataFrame,
) -> None:
    """Display state rankings with a minimum sample requirement."""

    week_start = dataframe["week_start"].iloc[0]
    week_end = dataframe["week_end"].iloc[0]
    unit = dataframe["measurement_unit"].iloc[0]

    eligible_states, low_sample_states = (
        filter_by_minimum_observations(dataframe)
    )

    print(f"Product: {PRODUCT}")
    print(f"Unit: {unit}")
    print(
        "Latest complete week: "
        f"{week_start.date()} to {week_end.date()}"
    )
    print(
        "Minimum observations required for ranking: "
        f"{MIN_OBSERVATIONS}"
    )

    highest_prices = eligible_states.sort_values(
        by="average_price",
        ascending=False,
    ).head(RANKING_SIZE)

    lowest_prices = eligible_states.sort_values(
        by="average_price",
        ascending=True,
    ).head(RANKING_SIZE)

    print_ranking(
        highest_prices,
        f"{RANKING_SIZE} states with the highest average prices",
    )

    print_ranking(
        lowest_prices,
        f"{RANKING_SIZE} states with the lowest average prices",
    )

    state_price_spread = (
        eligible_states["average_price"].max()
        - eligible_states["average_price"].min()
    )

    print(
        "\nDifference between the highest and lowest "
        f"eligible state averages: R$ {state_price_spread:.3f}"
    )

    if not low_sample_states.empty:
        print(
            "\nStates excluded from the ranking "
            "because of low observation counts:"
        )

        excluded_columns = [
            "state_code",
            "average_price",
            "price_observations",
            "station_count",
        ]

        excluded = low_sample_states[
            excluded_columns
        ].sort_values(
            by="price_observations"
        )

        print(
            excluded.to_string(
                index=False,
                formatters={
                    "average_price": lambda value: (
                        f"R$ {value:.3f}"
                    ),
                    "price_observations": lambda value: (
                        f"{value:,}"
                    ),
                    "station_count": lambda value: (
                        f"{value:,}"
                    ),
                },
            )
        )


def main() -> None:
    """Analyze gasoline prices by state."""

    dataframe = load_state_summary()

    dataframe = normalize_partial_week_column(dataframe)

    latest_state_prices = get_latest_state_prices(
        dataframe,
        PRODUCT,
    )

    display_state_rankings(latest_state_prices)


if __name__ == "__main__":
    main()