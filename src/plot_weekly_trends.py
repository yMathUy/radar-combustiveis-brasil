from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_national_prices.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "reports" / "figures"

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


def prepare_trend_data(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Select complete weeks and comparable fuel products."""

    filtered = dataframe[
        (~dataframe["is_partial_week"])
        & (dataframe["product"].isin(PRODUCTS))
    ].copy()

    if filtered.empty:
        raise ValueError(
            "No complete-week data was found for the selected products."
        )

    missing_products = set(PRODUCTS) - set(
        filtered["product"].unique()
    )

    if missing_products:
        raise ValueError(
            f"Products missing from the dataset: {sorted(missing_products)}"
        )

    invalid_units = filtered[
        filtered["measurement_unit"] != EXPECTED_UNIT
    ]

    if not invalid_units.empty:
        found_units = sorted(
            invalid_units["measurement_unit"]
            .dropna()
            .unique()
        )

        raise ValueError(
            "Unexpected measurement units found: "
            f"{found_units}"
        )

    return filtered.sort_values(
        by=[
            "product",
            "week_start",
        ]
    ).reset_index(drop=True)


def create_chart(
    dataframe: pd.DataFrame,
) -> Path:
    """Create and save the weekly national price trend chart."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure, axis = plt.subplots(
        figsize=(12, 7)
    )

    for product in PRODUCTS:
        product_data = dataframe[
            dataframe["product"] == product
        ].sort_values(
            by="week_start"
        )

        axis.plot(
            product_data["week_start"],
            product_data["average_price"],
            marker="o",
            markersize=4,
            linewidth=1.8,
            label=product,
        )

    minimum_date = dataframe["week_start"].min()
    maximum_date = dataframe["week_end"].max()

    axis.set_title(
        "Weekly average fuel prices in Brazil\n"
        f"{minimum_date.date()} to {maximum_date.date()}"
    )

    axis.set_xlim(
        dataframe["week_start"].min(),
        dataframe["week_start"].max(),
    )    

    axis.set_xlabel("Week")
    axis.set_ylabel("Average price (R$ per liter)")

    axis.xaxis.set_major_locator(
        mdates.WeekdayLocator(
            byweekday=mdates.MO,
            interval=2,
        )
    )

    axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%d/%m")
    )

    axis.grid(
        axis="y",
        alpha=0.3,
    )

    axis.legend(
        title="Product",
    )

    figure.autofmt_xdate(
        rotation=45,
    )

    figure.text(
        0.01,
        0.01,
        (
            "Partial weeks were excluded. "
            "Values represent average prices observed by ANP."
        ),
        fontsize=8,
    )

    figure.tight_layout(
        rect=[0, 0.04, 1, 1]
    )

    output_path = (
        OUTPUT_DIR
        / "weekly_national_fuel_price_trends.png"
    )

    figure.savefig(
        output_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(figure)

    return output_path


def show_summary(
    dataframe: pd.DataFrame,
) -> None:
    """Display the period and number of weekly observations."""

    print(
        "Complete-week period: "
        f"{dataframe['week_start'].min().date()} to "
        f"{dataframe['week_end'].max().date()}"
    )

    print("\nWeeks by product:")

    product_counts = (
        dataframe.groupby(
            "product",
            observed=True,
        )["week_start"]
        .nunique()
        .sort_index()
    )

    for product, week_count in product_counts.items():
        print(f"- {product}: {week_count} weeks")


def main() -> None:
    """Generate the national weekly fuel price trend chart."""

    dataframe = load_national_summary()

    dataframe = normalize_partial_week_column(dataframe)

    trend_data = prepare_trend_data(dataframe)

    show_summary(trend_data)

    output_path = create_chart(trend_data)

    print(f"\nChart saved to: {output_path}")
    print("Weekly trend chart generated successfully.")


if __name__ == "__main__":
    main()