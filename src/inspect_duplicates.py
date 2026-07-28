from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "reports"


def find_processed_csv() -> Path:
    """Find the cleaned ANP CSV file."""

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


def load_data(file_path: Path) -> pd.DataFrame:
    """Load the cleaned fuel price dataset."""

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


def find_exact_duplicates(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return all rows that are exact duplicates."""

    return dataframe[
        dataframe.duplicated(
            keep=False,
        )
    ].sort_values(
        by=[
            "station_tax_id",
            "product",
            "collection_date",
        ]
    )


def find_business_key_duplicates(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Find rows sharing the same station, product, and collection date."""

    business_key = [
        "station_tax_id",
        "product",
        "collection_date",
    ]

    return dataframe[
        dataframe.duplicated(
            subset=business_key,
            keep=False,
        )
    ].sort_values(
        by=business_key + ["sale_price"]
    )


def save_report(
    dataframe: pd.DataFrame,
    file_name: str,
) -> Path:
    """Save a duplicate inspection report as CSV."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = OUTPUT_DIR / file_name

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    return output_path


def main() -> None:
    """Inspect and report duplicate rows."""

    input_file = find_processed_csv()
    dataframe = load_data(input_file)

    exact_duplicates = find_exact_duplicates(dataframe)
    business_key_duplicates = find_business_key_duplicates(dataframe)

    exact_report = save_report(
        exact_duplicates,
        "exact_duplicates.csv",
    )

    business_key_report = save_report(
        business_key_duplicates,
        "business_key_duplicates.csv",
    )

    print(f"Dataset: {input_file.name}")
    print(f"Exact duplicate rows: {len(exact_duplicates):,}")
    print(
        "Rows sharing station, product, and collection date: "
        f"{len(business_key_duplicates):,}"
    )

    print("\nExact duplicates:")
    print(
        exact_duplicates[
            [
                "state_code",
                "municipality",
                "station_name",
                "station_tax_id",
                "product",
                "collection_date",
                "sale_price",
            ]
        ].to_string(index=False)
    )

    print("\nBusiness-key duplicates:")
    print(
        business_key_duplicates[
            [
                "state_code",
                "municipality",
                "station_name",
                "station_tax_id",
                "product",
                "collection_date",
                "sale_price",
            ]
        ].to_string(index=False)
    )

    print(f"\nExact duplicate report: {exact_report}")
    print(f"Business-key duplicate report: {business_key_report}")


if __name__ == "__main__":
    main()