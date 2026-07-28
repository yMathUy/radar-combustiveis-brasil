from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

EXPECTED_COLUMNS = {
    "region_code",
    "state_code",
    "municipality",
    "station_name",
    "station_tax_id",
    "street_name",
    "street_number",
    "address_complement",
    "neighborhood",
    "postal_code",
    "product",
    "collection_date",
    "sale_price",
    "measurement_unit",
    "brand",
}

VALID_STATE_CODES = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}

STATE_REGION_MAP = {
    "AC": "N",
    "AP": "N",
    "AM": "N",
    "PA": "N",
    "RO": "N",
    "RR": "N",
    "TO": "N",
    "AL": "NE",
    "BA": "NE",
    "CE": "NE",
    "MA": "NE",
    "PB": "NE",
    "PE": "NE",
    "PI": "NE",
    "RN": "NE",
    "SE": "NE",
    "DF": "CO",
    "GO": "CO",
    "MT": "CO",
    "MS": "CO",
    "ES": "SE",
    "MG": "SE",
    "RJ": "SE",
    "SP": "SE",
    "PR": "S",
    "RS": "S",
    "SC": "S",
}

DATASET_START_DATE = pd.Timestamp("2026-01-01")
DATASET_END_DATE = pd.Timestamp("2026-06-30")


def find_processed_csv() -> Path:
    """Find the cleaned CSV file in the processed data directory."""

    csv_files = list(PROCESSED_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No processed CSV files were found in: {PROCESSED_DATA_DIR}"
        )

    if len(csv_files) > 1:
        raise RuntimeError(
            "Multiple processed CSV files were found. "
            "The input file must be selected explicitly."
        )

    return csv_files[0]


def load_processed_data(file_path: Path) -> pd.DataFrame:
    """Load the cleaned dataset with the expected data types."""

    return pd.read_csv(
        file_path,
        parse_dates=["collection_date"],
        dtype={
            "region_code": "string",
            "state_code": "string",
            "municipality": "string",
            "station_name": "string",
            "station_tax_id": "string",
            "street_name": "string",
            "street_number": "string",
            "address_complement": "string",
            "neighborhood": "string",
            "postal_code": "string",
            "product": "string",
            "measurement_unit": "string",
            "brand": "string",
        },
        low_memory=False,
    )


def validate_schema(dataframe: pd.DataFrame) -> None:
    """Validate whether the dataset contains the expected columns."""

    actual_columns = set(dataframe.columns)

    missing_columns = EXPECTED_COLUMNS - actual_columns
    unexpected_columns = actual_columns - EXPECTED_COLUMNS

    if missing_columns:
        raise ValueError(
            f"Missing expected columns: {sorted(missing_columns)}"
        )

    if unexpected_columns:
        raise ValueError(
            f"Unexpected columns found: {sorted(unexpected_columns)}"
        )

    print("[PASS] Dataset schema is valid.")


def validate_required_values(dataframe: pd.DataFrame) -> None:
    """Validate required fields for missing values."""

    required_columns = [
        "region_code",
        "state_code",
        "municipality",
        "station_name",
        "station_tax_id",
        "product",
        "collection_date",
        "sale_price",
        "measurement_unit",
    ]

    missing_values = dataframe[required_columns].isna().sum()
    invalid_columns = missing_values[missing_values > 0]

    if not invalid_columns.empty:
        raise ValueError(
            "Missing required values were found:\n"
            f"{invalid_columns.to_string()}"
        )

    print("[PASS] Required fields have no missing values.")


def validate_state_codes(dataframe: pd.DataFrame) -> None:
    """Validate Brazilian state codes."""

    dataset_state_codes = set(dataframe["state_code"].dropna().unique())
    invalid_state_codes = dataset_state_codes - VALID_STATE_CODES

    if invalid_state_codes:
        raise ValueError(
            f"Invalid state codes found: {sorted(invalid_state_codes)}"
        )

    print("[PASS] All state codes are valid.")


def validate_region_mapping(dataframe: pd.DataFrame) -> None:
    """Validate whether each state belongs to the expected region."""

    expected_regions = dataframe["state_code"].map(STATE_REGION_MAP)
    invalid_rows = dataframe["region_code"] != expected_regions

    invalid_count = int(invalid_rows.sum())

    if invalid_count > 0:
        raise ValueError(
            f"{invalid_count:,} rows have an invalid state-region mapping."
        )

    print("[PASS] State and region mappings are valid.")


def validate_dates(dataframe: pd.DataFrame) -> None:
    """Validate the dataset date range."""

    minimum_date = dataframe["collection_date"].min()
    maximum_date = dataframe["collection_date"].max()

    if minimum_date < DATASET_START_DATE:
        raise ValueError(
            f"Date before expected period found: {minimum_date.date()}"
        )

    if maximum_date > DATASET_END_DATE:
        raise ValueError(
            f"Date after expected period found: {maximum_date.date()}"
        )

    print(
        "[PASS] Collection dates are valid: "
        f"{minimum_date.date()} to {maximum_date.date()}."
    )


def validate_prices(dataframe: pd.DataFrame) -> None:
    """Validate sale prices and report potential outliers."""

    if not pd.api.types.is_numeric_dtype(dataframe["sale_price"]):
        raise TypeError("sale_price must be a numeric column.")

    if dataframe["sale_price"].isna().any():
        raise ValueError("Missing values were found in sale_price.")

    if (dataframe["sale_price"] <= 0).any():
        raise ValueError("Sale prices must be greater than zero.")

    first_quartile = dataframe["sale_price"].quantile(0.25)
    third_quartile = dataframe["sale_price"].quantile(0.75)
    interquartile_range = third_quartile - first_quartile

    lower_limit = first_quartile - 3 * interquartile_range
    upper_limit = third_quartile + 3 * interquartile_range

    possible_outliers = dataframe[
        (dataframe["sale_price"] < lower_limit)
        | (dataframe["sale_price"] > upper_limit)
    ]

    print("[PASS] All sale prices are numeric and greater than zero.")
    print(
        "[INFO] Potential statistical price outliers: "
        f"{len(possible_outliers):,}"
    )
    print(
        "[INFO] Sale price range: "
        f"R$ {dataframe['sale_price'].min():.2f} to "
        f"R$ {dataframe['sale_price'].max():.2f}"
    )


def report_duplicates(dataframe: pd.DataFrame) -> None:
    """Report exact and business-key duplicates."""

    exact_duplicates = int(dataframe.duplicated().sum())

    business_key = [
        "station_tax_id",
        "product",
        "collection_date",
    ]

    key_duplicates = int(
        dataframe.duplicated(
            subset=business_key,
            keep=False,
        ).sum()
    )

    print(f"[INFO] Exact duplicate rows: {exact_duplicates:,}")
    print(
        "[INFO] Rows sharing the same station, product, and date: "
        f"{key_duplicates:,}"
    )


def show_summary(dataframe: pd.DataFrame) -> None:
    """Display a compact dataset summary."""

    print("\nDataset summary:")
    print(f"- Rows: {len(dataframe):,}")
    print(f"- Columns: {len(dataframe.columns)}")
    print(f"- States: {dataframe['state_code'].nunique()}")
    print(f"- Municipalities: {dataframe['municipality'].nunique()}")
    print(f"- Stations: {dataframe['station_tax_id'].nunique()}")
    print(f"- Products: {dataframe['product'].nunique()}")

    print("\nProducts found:")

    for product in sorted(dataframe["product"].dropna().unique()):
        print(f"- {product}")


def main() -> None:
    """Load and validate the cleaned ANP dataset."""

    processed_file = find_processed_csv()

    print(f"Validating dataset: {processed_file.name}\n")

    dataframe = load_processed_data(processed_file)

    validate_schema(dataframe)
    validate_required_values(dataframe)
    validate_state_codes(dataframe)
    validate_region_mapping(dataframe)
    validate_dates(dataframe)
    validate_prices(dataframe)
    report_duplicates(dataframe)
    show_summary(dataframe)

    print("\nData validation completed successfully.")


if __name__ == "__main__":
    main()