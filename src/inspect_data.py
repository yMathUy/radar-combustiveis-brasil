from pathlib import Path
import csv

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"


def find_csv_file() -> Path:
    """Find the CSV file inside the raw data directory."""

    csv_files = list(RAW_DATA_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files were found in: {RAW_DATA_DIR}"
        )

    if len(csv_files) > 1:
        print("Multiple CSV files were found. Using the first one:")

        for csv_file in csv_files:
            print(f"- {csv_file.name}")

    return csv_files[0]


def detect_encoding(file_path: Path) -> str:
    """Detect a compatible text encoding for the CSV file."""

    possible_encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ]

    for encoding in possible_encodings:
        try:
            with file_path.open(
                "r",
                encoding=encoding,
            ) as file:
                file.read(10_000)

            return encoding

        except UnicodeDecodeError:
            continue

    raise UnicodeError(
        "Could not determine a compatible encoding."
    )


def detect_delimiter(
    file_path: Path,
    encoding: str,
) -> str:
    """Detect the delimiter used by the CSV file."""

    with file_path.open(
        "r",
        encoding=encoding,
        newline="",
    ) as file:
        sample = file.read(10_000)

    dialect = csv.Sniffer().sniff(
        sample,
        delimiters=[",", ";", "\t", "|"],
    )

    return dialect.delimiter


def inspect_dataframe(dataframe: pd.DataFrame) -> None:
    """Display basic information about the dataset."""

    print("\nDataset dimensions:")
    print(f"- Rows: {dataframe.shape[0]:,}")
    print(f"- Columns: {dataframe.shape[1]}")

    print("\nColumn names:")

    for column in dataframe.columns:
        print(f"- {column}")

    print("\nData types:")
    print(dataframe.dtypes)

    print("\nMissing values by column:")
    print(dataframe.isna().sum())

    print("\nFirst five rows:")
    print(dataframe.head().to_string())


def main() -> None:
    """Load and inspect the raw ANP dataset."""

    csv_file = find_csv_file()
    encoding = detect_encoding(csv_file)
    delimiter = detect_delimiter(csv_file, encoding)

    print(f"CSV file: {csv_file.name}")
    print(f"Detected encoding: {encoding}")
    print(f"Detected delimiter: {repr(delimiter)}")

    dataframe = pd.read_csv(
        csv_file,
        encoding=encoding,
        sep=delimiter,
        low_memory=False,
    )

    inspect_dataframe(dataframe)


if __name__ == "__main__":
    main()