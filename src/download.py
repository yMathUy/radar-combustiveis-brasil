from pathlib import Path
from zipfile import ZipFile, is_zipfile

import requests


# Official ANP dataset URL:
# Automotive fuel prices for the first half of 2026.
ANP_URL = (
    "https://www.gov.br/anp/pt-br/centrais-de-conteudo/"
    "dados-abertos/arquivos/shpc/dsas/ca/"
    "ca-2026-01.zip/@@download/file"
)

# Find the project root directory.
#
# __file__ points to:
# src/download.py
#
# parent points to the src directory.
# parents[1] points to the project root directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directory used to store the original source files.
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

# Full path where the ZIP file will be stored.
ZIP_FILE_PATH = RAW_DATA_DIR / "ca-2026-01.zip"


def download_file() -> None:
    """Download the raw fuel price dataset from ANP."""

    # Create the raw data directory if it does not exist.
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Avoid downloading the same file again.
    if ZIP_FILE_PATH.exists():
        print(f"File already exists: {ZIP_FILE_PATH}")
        return

    print("Starting ANP dataset download...")

    try:
        # stream=True downloads the file in smaller chunks instead
        # of loading the entire response into memory.
        with requests.get(
            ANP_URL,
            stream=True,
            timeout=120,
        ) as response:

            # Raise an exception for HTTP errors such as 404 or 500.
            response.raise_for_status()

            # Open the destination file in binary write mode.
            with ZIP_FILE_PATH.open("wb") as output_file:

                # Download the file in approximately 1 MB chunks.
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        output_file.write(chunk)

    except requests.RequestException as error:
        # Remove an incomplete file if the download fails.
        ZIP_FILE_PATH.unlink(missing_ok=True)

        raise RuntimeError(
            f"Could not download the ANP dataset: {error}"
        ) from error

    print(f"Download completed: {ZIP_FILE_PATH}")


def extract_file() -> None:
    """Validate and extract the downloaded ZIP file."""

    # Verify that the downloaded file is a valid ZIP archive.
    if not is_zipfile(ZIP_FILE_PATH):
        ZIP_FILE_PATH.unlink(missing_ok=True)

        raise RuntimeError(
            "The downloaded file is not a valid ZIP archive. "
            "The invalid file was removed."
        )

    # Open the ZIP archive.
    with ZipFile(ZIP_FILE_PATH, "r") as zip_file:

        print("\nFiles found inside the ZIP archive:")

        for file_name in zip_file.namelist():
            print(f"- {file_name}")

        # Extract all files into the raw data directory.
        zip_file.extractall(RAW_DATA_DIR)

    print(f"\nFiles extracted to: {RAW_DATA_DIR}")


def show_results() -> None:
    """Display the CSV files extracted from the ZIP archive."""

    # Search recursively for CSV files inside the raw data directory.
    csv_files = list(RAW_DATA_DIR.rglob("*.csv"))

    if not csv_files:
        raise RuntimeError(
            "The ZIP archive was extracted, but no CSV files were found."
        )

    print("\nCSV files found:")

    for csv_file in csv_files:
        relative_path = csv_file.relative_to(PROJECT_ROOT)
        print(f"- {relative_path}")

    zip_size_mb = ZIP_FILE_PATH.stat().st_size / 1024 / 1024

    print(f"\nZIP file size: {zip_size_mb:.2f} MB")
    print("Dataset downloaded successfully.")


def main() -> None:
    """Run all download and extraction steps."""

    download_file()
    extract_file()
    show_results()


# Run main() only when this file is executed directly.
if __name__ == "__main__":
    main()