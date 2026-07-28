from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

NATIONAL_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_national_prices.csv"
)

STATE_INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "aggregated"
    / "weekly_state_prices.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "docs" / "data"

TREND_PRODUCTS = [
    "GASOLINA",
    "ETANOL",
    "DIESEL",
    "DIESEL S10",
]

STATE_RANKING_PRODUCT = "GASOLINA"
EXPECTED_LIQUID_UNIT = "R$ / litro"
MIN_STATE_OBSERVATIONS = 30


def load_summary(
    file_path: Path,
    string_columns: list[str],
) -> pd.DataFrame:
    """Load an aggregated fuel price table."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"Aggregated dataset not found: {file_path}"
        )

    dtype_mapping = {
        column: "string"
        for column in string_columns
    }

    return pd.read_csv(
        file_path,
        parse_dates=[
            "week_start",
            "week_end",
        ],
        dtype=dtype_mapping,
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
            .str.lower()
            .map(
                {
                    "true": True,
                    "false": False,
                }
            )
        )

    if dataframe["is_partial_week"].isna().any():
        raise ValueError(
            "Invalid values were found in is_partial_week."
        )

    return dataframe


def format_date_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Convert datetime columns to ISO date strings."""

    dataframe = dataframe.copy()

    for column in ["week_start", "week_end"]:
        if column in dataframe.columns:
            dataframe[column] = (
                dataframe[column]
                .dt.strftime("%Y-%m-%d")
            )

    return dataframe


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Convert a DataFrame into JSON-compatible records."""

    formatted = format_date_columns(dataframe)

    json_text = formatted.to_json(
        orient="records",
        force_ascii=False,
    )

    return json.loads(json_text)


def write_json(
    data: Any,
    file_name: str,
) -> Path:
    """Write dashboard data to a formatted JSON file."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / file_name

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            data,
            output_file,
            ensure_ascii=False,
            indent=2,
        )

    return output_path


def get_latest_complete_week_start(
    dataframe: pd.DataFrame,
) -> pd.Timestamp:
    """Return the most recent complete week in the dataset."""

    complete_weeks = dataframe[
        ~dataframe["is_partial_week"]
    ]

    if complete_weeks.empty:
        raise ValueError(
            "No complete weeks were found in the dataset."
        )

    return complete_weeks["week_start"].max()


def build_latest_national_prices(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Build the latest complete national fuel price table."""

    latest_week_start = get_latest_complete_week_start(
        dataframe
    )

    latest_prices = dataframe[
        dataframe["week_start"] == latest_week_start
    ].copy()

    columns = [
        "week_start",
        "week_end",
        "product",
        "measurement_unit",
        "average_price",
        "median_price",
        "minimum_price",
        "maximum_price",
        "price_observations",
        "station_count",
    ]

    latest_prices = latest_prices[columns]

    price_columns = [
        "average_price",
        "median_price",
        "minimum_price",
        "maximum_price",
    ]

    latest_prices[price_columns] = (
        latest_prices[price_columns].round(3)
    )

    return latest_prices.sort_values(
        by="average_price",
        ascending=False,
    ).reset_index(drop=True)


def build_latest_state_ranking(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Build the latest eligible state gasoline ranking."""

    product_data = dataframe[
        dataframe["product"] == STATE_RANKING_PRODUCT
    ].copy()

    latest_week_start = get_latest_complete_week_start(
        product_data
    )

    latest_prices = product_data[
        (product_data["week_start"] == latest_week_start)
        & (
            product_data["price_observations"]
            >= MIN_STATE_OBSERVATIONS
        )
    ].copy()

    columns = [
        "week_start",
        "week_end",
        "state_code",
        "product",
        "measurement_unit",
        "average_price",
        "median_price",
        "minimum_price",
        "maximum_price",
        "price_observations",
        "station_count",
    ]

    latest_prices = latest_prices[columns]

    price_columns = [
        "average_price",
        "median_price",
        "minimum_price",
        "maximum_price",
    ]

    latest_prices[price_columns] = (
        latest_prices[price_columns].round(3)
    )

    return latest_prices.sort_values(
        by="average_price",
        ascending=False,
    ).reset_index(drop=True)


def build_national_trends(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Build complete-week national price trends."""

    trend_data = dataframe[
        (~dataframe["is_partial_week"])
        & (dataframe["product"].isin(TREND_PRODUCTS))
        & (
            dataframe["measurement_unit"]
            == EXPECTED_LIQUID_UNIT
        )
    ].copy()

    columns = [
        "week_start",
        "week_end",
        "product",
        "measurement_unit",
        "average_price",
        "price_observations",
        "station_count",
    ]

    trend_data = trend_data[columns]

    trend_data["average_price"] = (
        trend_data["average_price"].round(3)
    )

    return trend_data.sort_values(
        by=[
            "week_start",
            "product",
        ]
    ).reset_index(drop=True)


def build_metadata(
    national_prices: pd.DataFrame,
) -> dict[str, Any]:
    """Build dashboard metadata."""

    first_row = national_prices.iloc[0]

    return {
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "source": "ANP - Brazilian National Agency of Petroleum",
        "latest_complete_week": {
            "start": first_row["week_start"].strftime(
                "%Y-%m-%d"
            ),
            "end": first_row["week_end"].strftime(
                "%Y-%m-%d"
            ),
        },
        "state_ranking": {
            "product": STATE_RANKING_PRODUCT,
            "minimum_observations": MIN_STATE_OBSERVATIONS,
        },
    }


def main() -> None:
    """Export compact JSON files for the static dashboard."""

    national_data = load_summary(
        NATIONAL_INPUT_FILE,
        string_columns=[
            "product",
            "measurement_unit",
        ],
    )

    state_data = load_summary(
        STATE_INPUT_FILE,
        string_columns=[
            "state_code",
            "product",
            "measurement_unit",
        ],
    )

    national_data = normalize_partial_week_column(
        national_data
    )

    state_data = normalize_partial_week_column(
        state_data
    )

    latest_national = build_latest_national_prices(
        national_data
    )

    latest_states = build_latest_state_ranking(
        state_data
    )

    national_trends = build_national_trends(
        national_data
    )

    metadata = build_metadata(
        latest_national
    )

    national_output = write_json(
        dataframe_to_records(latest_national),
        "latest_national_prices.json",
    )

    state_output = write_json(
        dataframe_to_records(latest_states),
        "latest_state_gasoline_prices.json",
    )

    trends_output = write_json(
        dataframe_to_records(national_trends),
        "weekly_national_trends.json",
    )

    metadata_output = write_json(
        metadata,
        "metadata.json",
    )

    print("Dashboard files created:\n")
    print(
        f"- National prices: {national_output}"
    )
    print(
        f"- State ranking: {state_output}"
    )
    print(
        f"- Weekly trends: {trends_output}"
    )
    print(
        f"- Metadata: {metadata_output}"
    )

    print("\nExport summary:")
    print(
        f"- National products: {len(latest_national):,}"
    )
    print(
        f"- Eligible states: {len(latest_states):,}"
    )
    print(
        f"- Trend observations: {len(national_trends):,}"
    )

    print("\nDashboard data export completed successfully.")


if __name__ == "__main__":
    main()