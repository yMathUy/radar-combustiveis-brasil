from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_national_prices.csv"
)

PRODUCTS = [
    "GASOLINA",
    "ETANOL",
    "DIESEL",
    "DIESEL S10",
]

EXPECTED_UNIT = "R$ / litro"


def load_national_summary() -> pd.DataFrame:
    """Load the weekly national fuel price summary."""

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"National summary file not found: {INPUT_FILE}"
        )

    return pd.read_csv(
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


def prepare_change_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare complete weekly observations and calculate price changes."""

    filtered = dataframe[
        (~dataframe["is_partial_week"])
        & (dataframe["product"].isin(PRODUCTS))
        & (dataframe["measurement_unit"] == EXPECTED_UNIT)
    ].copy()

    if filtered.empty:
        raise ValueError(
            "No comparable complete-week observations were found."
        )

    filtered = filtered.sort_values(
        by=[
            "product",
            "week_start",
        ]
    ).reset_index(drop=True)

    filtered["previous_price"] = (
        filtered.groupby(
            "product",
            observed=True,
        )["average_price"]
        .shift(1)
    )

    filtered["weekly_change_value"] = (
        filtered["average_price"]
        - filtered["previous_price"]
    )

    filtered["weekly_change_percent"] = (
        filtered["weekly_change_value"]
        / filtered["previous_price"]
        * 100
    )

    return filtered


def display_product_summary(
    product_data: pd.DataFrame,
    product: str,
) -> None:
    """Display weekly change statistics for one product."""

    product_data = product_data.sort_values(
        by="week_start"
    ).reset_index(drop=True)

    valid_changes = product_data.dropna(
        subset=[
            "weekly_change_value",
            "weekly_change_percent",
        ]
    )

    if valid_changes.empty:
        raise ValueError(
            f"Not enough weekly observations for product: {product}"
        )

    largest_increase = valid_changes.loc[
        valid_changes["weekly_change_value"].idxmax()
    ]

    largest_decrease = valid_changes.loc[
        valid_changes["weekly_change_value"].idxmin()
    ]

    first_row = product_data.iloc[0]
    last_row = product_data.iloc[-1]

    period_change_value = (
        last_row["average_price"]
        - first_row["average_price"]
    )

    period_change_percent = (
        period_change_value
        / first_row["average_price"]
        * 100
    )

    print(f"\n{product}")
    print("-" * len(product))

    print(
        "Period: "
        f"{first_row['week_start'].date()} to "
        f"{last_row['week_end'].date()}"
    )

    print(
        "Initial average price: "
        f"R$ {first_row['average_price']:.3f}"
    )

    print(
        "Final average price: "
        f"R$ {last_row['average_price']:.3f}"
    )

    print(
        "Total period change: "
        f"R$ {period_change_value:+.3f} "
        f"({period_change_percent:+.2f}%)"
    )

    print(
        "Largest weekly increase: "
        f"R$ {largest_increase['weekly_change_value']:+.3f} "
        f"({largest_increase['weekly_change_percent']:+.2f}%) "
        f"in the week starting "
        f"{largest_increase['week_start'].date()}"
    )

    print(
        "Largest weekly decrease: "
        f"R$ {largest_decrease['weekly_change_value']:+.3f} "
        f"({largest_decrease['weekly_change_percent']:+.2f}%) "
        f"in the week starting "
        f"{largest_decrease['week_start'].date()}"
    )


def main() -> None:
    """Analyze weekly national fuel price changes."""

    dataframe = load_national_summary()

    dataframe = normalize_partial_week_column(dataframe)

    change_data = prepare_change_data(dataframe)

    print("Weekly national fuel price changes")
    print("Partial weeks are excluded.")

    for product in PRODUCTS:
        product_data = change_data[
            change_data["product"] == product
        ]

        display_product_summary(
            product_data,
            product,
        )


if __name__ == "__main__":
    main()