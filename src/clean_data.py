from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

COLUMN_NAMES = {
    "Regiao - Sigla": "region_code",
    "Estado - Sigla": "state_code",
    "Municipio": "municipality",
    "Revenda": "station_name",
    "CNPJ da Revenda": "station_tax_id",
    "Nome da Rua": "street_name",
    "Numero Rua": "street_number",
    "Complemento": "address_complement",
    "Bairro": "neighborhood",
    "Cep": "postal_code",
    "Produto": "product",
    "Data da Coleta": "collection_date",
    "Valor de Venda": "sale_price",
    "Valor de Compra": "purchase_price",
    "Unidade de Medida": "measurement_unit",
    "Bandeira": "brand",
}


def find_raw_csv() -> Path:
    """Find the raw ANP CSV file."""

    csv_files = list(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files were found in: {RAW_DATA_DIR}"
        )

    if len(csv_files) > 1:
        raise RuntimeError(
            "Multiple raw CSV files were found. "
            "The input file must be selected explicitly."
        )

    return csv_files[0]


def load_raw_data(file_path: Path) -> pd.DataFrame:
    """Load the raw ANP dataset without changing the source file."""

    return pd.read_csv(
        file_path,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        low_memory=False,
    )


def clean_text_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Remove leading and trailing spaces from text columns."""

    text_columns = dataframe.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        dataframe[column] = dataframe[column].str.strip()

    return dataframe


def transform_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Apply the main cleaning transformations."""

    dataframe = dataframe.rename(columns=COLUMN_NAMES)

    dataframe = clean_text_columns(dataframe)

    dataframe["collection_date"] = pd.to_datetime(
        dataframe["collection_date"],
        format="%d/%m/%Y",
        errors="raise",
    )

    dataframe["sale_price"] = pd.to_numeric(
        dataframe["sale_price"].str.replace(",", ".", regex=False),
        errors="raise",
    )

    if dataframe["purchase_price"].isna().all():
        dataframe = dataframe.drop(columns=["purchase_price"])

    return dataframe


def validate_clean_data(dataframe: pd.DataFrame) -> None:
    """Run basic validations on the cleaned dataset."""

    if dataframe.empty:
        raise ValueError("The cleaned dataset is empty.")

    if dataframe["sale_price"].isna().any():
        raise ValueError("Missing values were found in sale_price.")

    if dataframe["collection_date"].isna().any():
        raise ValueError(
            "Missing values were found in collection_date."
        )

    if (dataframe["sale_price"] <= 0).any():
        raise ValueError(
            "Sale prices must be greater than zero."
        )


def save_clean_data(dataframe: pd.DataFrame) -> Path:
    """Save the cleaned dataset as a CSV file."""

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        PROCESSED_DATA_DIR
        / "anp_fuel_prices_2026_01_clean.csv"
    )

    dataframe.to_csv(
        output_path,
        index=False,
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    """Load, clean, validate, and save the ANP dataset."""

    raw_file = find_raw_csv()

    print(f"Loading raw dataset: {raw_file.name}")

    dataframe = load_raw_data(raw_file)

    print(f"Raw rows: {len(dataframe):,}")

    dataframe = transform_data(dataframe)

    validate_clean_data(dataframe)

    output_path = save_clean_data(dataframe)

    print(f"Clean rows: {len(dataframe):,}")
    print(f"Clean columns: {len(dataframe.columns)}")
    print(f"Output file: {output_path}")
    print("Data cleaning completed successfully.")


if __name__ == "__main__":
    main()