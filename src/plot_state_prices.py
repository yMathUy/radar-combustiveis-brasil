from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_state_prices.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "reports" / "figures"

PRODUCT = "GASOLINA"
MIN_OBSERVATIONS = 30


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


def get_latest_eligible_prices(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return eligible state prices from the latest complete week."""

    filtered = dataframe[
        (~dataframe["is_partial_week"])
        & (dataframe["product"] == PRODUCT)
    ].copy()

    if filtered.empty:
        raise ValueError(
            f"No complete-week data was found for: {PRODUCT}"
        )

    latest_week_start = filtered["week_start"].max()

    latest_week = filtered[
        filtered["week_start"] == latest_week_start
    ].copy()

    eligible_states = latest_week[
        latest_week["price_observations"] >= MIN_OBSERVATIONS
    ].copy()

    if eligible_states.empty:
        raise ValueError(
            "No states meet the minimum observation requirement."
        )

    return eligible_states.sort_values(
        by="average_price",
        ascending=True,
    ).reset_index(drop=True)


def create_chart(dataframe: pd.DataFrame) -> Path:
    """Create and save a state gasoline price ranking dot plot."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    week_start = dataframe["week_start"].iloc[0]
    week_end = dataframe["week_end"].iloc[0]

    figure_height = max(7, len(dataframe) * 0.36)

    figure, axis = plt.subplots(
        figsize=(10, figure_height)
    )

    positions = range(len(dataframe))

    # Draw horizontal guide lines between the axis and each point.
    axis.hlines(
        y=positions,
        xmin=dataframe["average_price"].min() - 0.05,
        xmax=dataframe["average_price"],
        linewidth=1,
        alpha=0.4,
    )

    # Draw one point for each state average.
    axis.scatter(
        dataframe["average_price"],
        positions,
        s=55,
    )

    axis.set_yticks(
        list(positions),
        labels=dataframe["state_code"],
    )

    axis.set_xlabel("Average gasoline price (R$ per liter)")
    axis.set_ylabel("State")

    axis.set_title(
        "Average gasoline price by state\n"
        f"{week_start.date()} to {week_end.date()}"
    )

    axis.set_xlim(
        dataframe["average_price"].min() - 0.10,
        dataframe["average_price"].max() + 0.22,
    )

    # Display the average beside each state point.
    for position, value in enumerate(
        dataframe["average_price"]
    ):
        axis.text(
            value + 0.025,
            position,
            f"R$ {value:.3f}",
            va="center",
            fontsize=8,
        )

    figure.text(
        0.01,
        0.01,
        (
            f"Only states with at least {MIN_OBSERVATIONS} "
            "price observations are included. Source: ANP."
        ),
        fontsize=8,
    )

    figure.tight_layout(
        rect=[0, 0.035, 1, 1]
    )

    output_path = (
        OUTPUT_DIR
        / "latest_state_gasoline_prices.png"
    )

    figure.savefig(
        output_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close(figure)

    return output_path


def main() -> None:
    """Generate the latest state gasoline price chart."""

    dataframe = load_state_summary()

    dataframe = normalize_partial_week_column(dataframe)

    latest_prices = get_latest_eligible_prices(dataframe)

    output_path = create_chart(latest_prices)

    print(f"States included: {len(latest_prices)}")
    print(f"Chart saved to: {output_path}")
    print("Chart generation completed successfully.")


if __name__ == "__main__":
    main()